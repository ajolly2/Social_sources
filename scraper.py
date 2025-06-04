#!/usr/bin/env python3
import requests
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from feedgenerator import Rss201rev2Feed

# ─── CONFIGURATION ──────────────────────────────────────────────────────────────

# List of X.com handles (without '@'):
ACCOUNTS = [
    "MLB",
    "ESPN",
    "NBCSports",
    "SBNation",
    # add/remove handles here as desired
]

# How many tweets to fetch per account (max):
TWEETS_PER_ACCOUNT = 5

# Public Nitter mirrors to rotate through:
NITTER_MIRRORS = [
    "https://nitter.net",
    "https://nitter.snopyta.org",
    "https://nitter.42l.fr"
]

# Seconds to sleep between each mirror request:
DELAY_BETWEEN_REQUESTS = 2.0

# Output RSS filename:
OUTPUT_RSS_FILE = "social_feed.xml"


# ─── HELPERS ────────────────────────────────────────────────────────────────────

def fetch_from_mirror(base_url: str, username: str, limit: int):
    """
    Attempt to scrape up to `limit` tweets from `base_url/<username>`.
    Returns a list of tweet dicts.
    Raises RuntimeError("429 …") if this mirror returned HTTP 429.
    Raises any other Exception for other errors.
    """
    url = f"{base_url}/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SocialFeedBot/1.0; +https://thporth.com/)"
    }
    print(f"[DEBUG]  → GET {url}")
    resp = requests.get(url, headers=headers, timeout=20)
    print(f"[DEBUG]    ← {resp.status_code} from {base_url}")

    if resp.status_code == 429:
        # Mirror is rate‐limiting us
        raise RuntimeError(f"429 Too Many Requests from {base_url}")

    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find all <div class="timeline-item">
    timeline_items = soup.select("div.timeline-item")
    print(f"[DEBUG]    Found {len(timeline_items)} <div.timeline-item> elements on {base_url}/{username}")

    tweets = []
    for item in timeline_items[:limit]:
        # (A) Tweet link (relative → absolute)
        link_tag = item.select_one("a.tweet-link")
        if not link_tag or not link_tag.get("href"):
            continue
        path = link_tag["href"].strip()
        tweet_link = base_url + path
        tweet_id = path.rsplit("/", 1)[-1]

        # (B) Tweet text
        content_div = item.select_one("div.tweet-content")
        tweet_text = ""
        if content_div:
            parts = []
            for node in content_div.find_all(["p", "span"]):
                txt = node.get_text(separator=" ", strip=True)
                if txt:
                    parts.append(txt)
            tweet_text = " ".join(parts).strip()

        # (C) First image (if any)
        img_url = ""
        attachment = item.select_one("div.attachments img")
        if attachment and attachment.get("src"):
            src = attachment["src"].strip()
            img_url = src if src.startswith("http") else base_url + src

        # (D) Published timestamp
        time_tag = item.select_one("time")
        if time_tag and time_tag.get("datetime"):
            iso = time_tag["datetime"]
            try:
                pub_dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            except Exception:
                pub_dt = datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        else:
            pub_dt = datetime.now(timezone.utc)

        tweets.append({
            "id":        tweet_id,
            "link":      tweet_link,
            "text":      tweet_text,
            "image":     img_url,
            "published": pub_dt
        })

    return tweets


def fetch_nitter_tweets(username: str, limit: int):
    """
    Try each mirror in NITTER_MIRRORS until one succeeds.
    Returns a list of tweet dicts for that username (up to limit).
    If all mirrors return 429 or errors, returns [] after warning.
    """
    for mirror in NITTER_MIRRORS:
        try:
            tweets = fetch_from_mirror(mirror, username, limit)
            return tweets
        except RuntimeError as re_err:
            if "429" in str(re_err):
                print(f"[WARN] Mirror {mirror} returned 429 for @{username}. Trying next mirror…")
                continue
            else:
                raise
        except Exception as e:
            print(f"[WARN] Mirror {mirror} failed for @{username}: {e}")
            continue

    # If we reach here, all mirrors have failed or rate‐limited us.
    print(f"[WARN] All Nitter mirrors failed or rate‐limited for @{username}. Skipping user.")
    return []


def build_rss(all_tweets: list):
    """
    Given a list of tweet dicts, build an RSS feed and write to OUTPUT_RSS_FILE.
    """
    feed = Rss201rev2Feed(
        title="THPORTH Social Feed",
        link="https://thporth.com/",
        description="Aggregated tweets from multiple X.com accounts (via Nitter)",
        language="en",
        last_build_date=datetime.now(timezone.utc)
    )

    # Sort newest-first
    sorted_tweets = sorted(all_tweets, key=lambda t: t["published"], reverse=True)

    for tw in sorted_tweets:
        pub_str = tw["published"].strftime("%a, %d %b %Y %H:%M:%S +0000")
        snippet = (tw["text"][:50] + "…") if len(tw["text"]) > 50 else tw["text"] or "(Image Only)"

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
            title       = snippet,
            link        = tw["link"],
            description = f"<![CDATA[{description_html}]]>",
            unique_id   = tw["id"] or tw["link"],
            pubdate     = pub_str
        )

    with open(OUTPUT_RSS_FILE, "w", encoding="utf-8") as fp:
        feed.write(fp, "utf-8")
    print(f"[OK] Wrote {len(sorted_tweets)} items to {OUTPUT_RSS_FILE}")


def main():
    all_collected = []
    for acct in ACCOUNTS:
        print(f"[INFO] Fetching tweets for @{acct} …")
        try:
            tweets = fetch_nitter_tweets(acct, TWEETS_PER_ACCOUNT)
        except Exception as e:
            print(f"[ERROR] Unexpected error fetching @{acct}: {e}")
            tweets = []

        print(f"[INFO] Retrieved {len(tweets)} tweets from @{acct}. Sleeping {DELAY_BETWEEN_REQUESTS}s…")
        all_collected.extend(tweets)
        time.sleep(DELAY_BETWEEN_REQUESTS)

    build_rss(all_collected)


if __name__ == "__main__":
    main()
