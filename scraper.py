#!/usr/bin/env python3
import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup
from feedgenerator import Rss201rev2Feed

#
# ─── CONFIGURATION ─────────────────────────────────────────────────────────────
#

# List of X.com handles (no @). We'll hit each via Nitter:
ACCOUNTS = [
    "MLB",
    "ESPN",
    "NBCSports",
    "SBNation",
    # add more as needed…
]

# How many tweets to pull per account:
TWEETS_PER_ACCOUNT = 10

# Delay (in seconds) between each HTTP request to Nitter to reduce rate‐limit hits:
DELAY_BETWEEN_ACCOUNTS = 2

# Output filename:
OUTPUT_FILENAME = "social_feed.xml"

#
# ─── HELPERS ────────────────────────────────────────────────────────────────────
#

def fetch_nitter_tweets(username: str, limit: int):
    """
    Scrape up to `limit` tweets from https://nitter.net/<username>.
    Returns a list of dicts: { link, text, image, published (datetime) }.
    In case of HTTP 429, raises a custom exception or returns an empty list.
    """
    url = f"https://nitter.net/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SocialFeedBot/1.0; +https://thporth.com/)"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        # If we receive 429, raise it to be caught below
        resp.raise_for_status()
    except requests.exceptions.HTTPError as he:
        # If it’s a 429 Too Many Requests, bail out gracefully:
        if resp.status_code == 429:
            raise RuntimeError(f"429 Too Many Requests for {username}")
        else:
            raise

    soup = BeautifulSoup(resp.text, "html.parser")
    tweets_data = []
    timeline_items = soup.select("div.timeline-item")[:limit]

    for item in timeline_items:
        # 1) Tweet link (relative → absolute)
        link_tag = item.select_one("a.tweet-link")
        if not link_tag:
            continue
        tweet_path = link_tag["href"].strip()
        tweet_url = "https://nitter.net" + tweet_path

        # 2) Tweet text
        content_div = item.select_one("div.tweet-content")
        tweet_text = ""
        if content_div:
            parts = []
            for node in content_div.find_all(["p", "span"]):
                txt = node.get_text(separator=" ", strip=True)
                if txt:
                    parts.append(txt)
            tweet_text = " ".join(parts).strip()

        # 3) First image (if any)
        img_url = ""
        attachment = item.select_one("div.attachments img")
        if attachment and attachment.get("src"):
            raw_src = attachment["src"].strip()
            img_url = raw_src if raw_src.startswith("http") else "https://nitter.net" + raw_src

        # 4) Published date (title="Jun 04, 2025 · 07:52:15 PM")
        date_span = item.select_one("span.tweet-date a")
        published_dt = None
        if date_span and date_span.get("title"):
            try:
                published_dt = datetime.strptime(date_span["title"], "%b %d, %Y · %I:%M:%S %p")
            except ValueError:
                published_dt = None

        tweets_data.append({
            "link": tweet_url,
            "text": tweet_text,
            "image": img_url,
            "published": published_dt
        })

    return tweets_data


def build_feed(all_tweets: list):
    """
    Given a list of tweets (each dict with link, text, image, published),
    writes out an RSS2.0 file named OUTPUT_FILENAME.
    """
    feed = Rss201rev2Feed(
        title="THPORTH Social Feed",
        link="https://thporth.com/",
        description="Aggregated tweets from multiple X.com accounts (via Nitter)",
        language="en",
        last_build_date=datetime.utcnow()
    )

    for tw in all_tweets:
        # Format pubDate as RFC‐2822
        if tw["published"]:
            pubdate_str = tw["published"].strftime("%a, %d %b %Y %H:%M:%S +0000")
        else:
            pubdate_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

        desc_parts = []
        if tw["text"]:
            safe_text = (
                tw["text"]
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            desc_parts.append(f"<p>{safe_text}</p>")
        if tw["image"]:
            desc_parts.append(f'<img src="{tw["image"]}" style="max-width:100%;"/>')

        description_html = "".join(desc_parts)
        short_title = tw["text"][:50] + ("…" if len(tw["text"]) > 50 else "")

        feed.add_item(
            title=f"{short_title}",
            link=tw["link"],
            description=f"<![CDATA[{description_html}]]>",
            pubdate=pubdate_str
        )

    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as fp:
        feed.write(fp, "utf-8")
    print(f"Wrote {len(all_tweets)} items to {OUTPUT_FILENAME}")


def main():
    combined = []
    for acct in ACCOUNTS:
        try:
            print(f"Fetching tweets from Nitter: {acct} …")
            tweets = fetch_nitter_tweets(acct, TWEETS_PER_ACCOUNT)
            combined.extend(tweets)
            # Sleep a little before hitting the next account
            print(f"  → Retrieved {len(tweets)} tweets from {acct}, sleeping {DELAY_BETWEEN_ACCOUNTS}s …")
            time.sleep(DELAY_BETWEEN_ACCOUNTS)
        except RuntimeError as re_err:
            # This is our “429 Too Many Requests” branch
            print(f"Warning: {re_err}. Skipping {acct} this run.")
            continue
        except Exception as e:
            print(f"Warning: Could not fetch {acct}: {e}")
            continue

    # Sort by published (newest first). If no published date, treat as epoch.
    combined.sort(key=lambda x: x["published"] or datetime(1970, 1, 1), reverse=True)

    build_feed(combined)


if __name__ == "__main__":
    main()
