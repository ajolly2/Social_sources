#!/usr/bin/env python3
import requests
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from feedgenerator import Rss201rev2Feed

# ─── CONFIGURATION ──────────────────────────────────────────────────────────────

# 1) List of X.com handles (without '@') you want to scrape.
#    E.g. "MLB", "ESPN", "NBCSports", "SBNation", etc.
#    Add or remove handles here as needed.
ACCOUNTS = [
    "MLB",
    "ESPN",
    "NBCSports",
    "SBNation",
    "BleacherReport",
    "FOXSports",
    "BBCSport",
    "SportsCenter",
    "YahooSports",
    # …you can extend this list at any time…
]

# 2) How many tweets to fetch per account (max). Nitter HTML shows a timeline;
#    we will scrape up to this many tweets on each run.
TWEETS_PER_ACCOUNT = 5

# 3) Small list of public Nitter mirrors to rotate through, to reduce 429s.
#    If one mirror returns a 429, we try the next. If *all* mirrors 429, skip that account.
NITTER_MIRRORS = [
    "https://nitter.net",
    "https://nitter.snopyta.org",
    "https://nitter.42l.fr"
]

# 4) How many seconds to sleep between each Nitter request.
#    (Keeps us under the mirror’s rate limits.)
DELAY_BETWEEN_REQUESTS = 2.0

# 5) Output RSS filename (will live in repo root).
OUTPUT_RSS_FILE = "social_feed.xml"


# ─── HELPERS ────────────────────────────────────────────────────────────────────

def fetch_from_mirror(base_url: str, username: str, limit: int):
    """
    Attempt to scrape up to `limit` tweets from `base_url/<username>`. Returns a list of tweet‐dicts.
    Raises RuntimeError("429 …") if this mirror returned HTTP 429.
    Raises any other Exception if something else went wrong.
    """
    url = f"{base_url}/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SocialFeedBot/1.0; +https://thporth.com/)"
    }
    resp = requests.get(url, headers=headers, timeout=20)
    if resp.status_code == 429:
        raise RuntimeError(f"429 Too Many Requests from {base_url}")
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    tweets = []
    timeline_items = soup.select("div.timeline-item")[:limit]

    for item in timeline_items:
        # (A) Tweet link (relative → absolute)
        link_tag = item.select_one("a.tweet-link")
        if not link_tag or not link_tag.get("href"):
            continue
        path = link_tag["href"].strip()
        tweet_link = base_url + path

        # (B) Tweet ID (last segment of path)
        tweet_id = path.rsplit("/", 1)[-1]

        # (C) Tweet text/content
        content_div = item.select_one("div.tweet-content")
        tweet_text = ""
        if content_div:
            parts = []
            for node in content_div.find_all(["p", "span"]):
                txt = node.get_text(separator=" ", strip=True)
                if txt:
                    parts.append(txt)
            tweet_text = " ".join(parts).strip()

        # (D) First image URL (if any)
        img_url = ""
        attachment = item.select_one("div.attachments img")
        if attachment and attachment.get("src"):
            src = attachment["src"].strip()
            img_url = src if src.startswith("http") else base_url + src

        # (E) Published timestamp from <time datetime="…">
        time_tag = item.select_one("time")
        pub_dt = None
        if time_tag and time_tag.get("datetime"):
            iso = time_tag["datetime"]
            try:
                pub_dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            except Exception:
                # Fallback parse if needed:
                pub_dt = datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        else:
            # If no exact time, use “now”:
            pub_dt = datetime.now(timezone.utc)

        tweets.append({
            "id":      tweet_id,
            "link":    tweet_link,
            "text":    tweet_text,
            "image":   img_url,
            "published": pub_dt
        })

    return tweets


def fetch_nitter_tweets(username: str, limit: int):
    """
    Try each mirror in NITTER_MIRRORS until one succeeds.
    Returns a list of tweet‐dicts for that username (up to `limit`).
    If all mirrors return 429, logs a warning and returns [].
    """
    for mirror in NITTER_MIRRORS:
        try:
            return fetch_from_mirror(mirror, username, limit)
        except RuntimeError as re_err:
            # Mirror-specific 429: try the next mirror
            if "429" in str(re_err):
                continue
            else:
                # Some other runtime error (unlikely), re-raise
                raise
        except Exception:
            # Any other exception (e.g. network), try next mirror
            continue

    # If we get here, all mirrors failed with 429 (or other errors):
    print(f"[WARN] All Nitter mirrors rate-limited or failed for {username}; skipping.")
    return []


def build_rss(all_tweets: list):
    """
    Given a list of tweet dicts (with keys: id, link, text, image, published),
    build an RSS 2.0 feed and write OUTPUT_RSS_FILE.
    """
    feed = Rss201rev2Feed(
        title="THPORTH Social Feed",
        link="https://thporth.com/",
        description="Aggregated tweets from multiple X.com accounts (via Nitter)",
        language="en",
        last_build_date=datetime.now(timezone.utc)
    )

    # Sort tweets by published timestamp, newest first
    sorted_tweets = sorted(all_tweets, key=lambda t: t["published"], reverse=True)

    for tw in sorted_tweets:
        # RSS requires an RFC-2822 pubDate string
        pub_str = tw["published"].strftime("%a, %d %b %Y %H:%M:%S +0000")

        # Short title = first 50 chars of text (or “(Image Only)” if no text)
        if tw["text"]:
            snippet = tw["text"][:50] + ("…" if len(tw["text"]) > 50 else "")
        else:
            snippet = "(Image Only)"

        # Build description: HTML with <p>…</p> and <img> if present
        desc_parts = []
        if tw["text"]:
            safe = (
                tw["text"]
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            desc_parts.append(f"<p>{safe}</p>")
        if tw["image"]:
            desc_parts.append(f'<img src="{tw["image"]}" style="max-width:100%;"/>')
        description_html = "".join(desc_parts)

        feed.add_item(
            title       = f"{snippet}",
            link        = tw["link"],
            description = f"<![CDATA[{description_html}]]>",
            unique_id   = tw["id"] or tw["link"],
            pubdate     = pub_str
        )

    # Write out the XML to disk
    with open(OUTPUT_RSS_FILE, "w", encoding="utf-8") as fp:
        feed.write(fp, "utf-8")
    print(f"[OK] Wrote {len(sorted_tweets)} items to {OUTPUT_RSS_FILE}")


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    all_collected = []
    for acct in ACCOUNTS:
        print(f"→ Fetching tweets for @{acct} …")
        try:
            tweets = fetch_nitter_tweets(acct, TWEETS_PER_ACCOUNT)
        except Exception as e:
            print(f"[ERROR] Unexpected error fetching {acct}: {e}")
            tweets = []

        print(f"   Retrieved {len(tweets)} tweets from @{acct}. Sleeping {DELAY_BETWEEN_REQUESTS}s …")
        all_collected.extend(tweets)
        time.sleep(DELAY_BETWEEN_REQUESTS)

    # Build the combined RSS feed (sorted by timestamp)
    build_rss(all_collected)


if __name__ == "__main__":
    main()
