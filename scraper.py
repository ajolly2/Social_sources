#!/usr/bin/env python3
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup
from feedgenerator import Rss201rev2Feed

# ─── CONFIG ─────────────────────────────────────────────────────────────────────

# The single Nitter URL we’re targeting for now:
NITTER_URL = "https://nitter.net/MLB"

# How many tweets to pull from that page (up to 100)
TWEETS_TO_FETCH = 100

# Output RSS filename
OUTPUT_FILENAME = "social_feed.xml"


# ─── HELPERS ────────────────────────────────────────────────────────────────────

def fetch_nitter_tweets(url: str, limit: int):
    """
    Scrapes the Nitter timeline at `url` and returns up to `limit` tweets.
    Each tweet is a dict with keys: link, text, image (or ""), published (datetime).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SocialFeedBot/1.0; +https://thporth.com/)"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tweets_data = []
    # Each tweet is wrapped in <div class="timeline-item">
    timeline_items = soup.select("div.timeline-item")[:limit]

    for item in timeline_items:
        # 1) Tweet link (relative path)
        link_tag = item.select_one("a.tweet-link")
        if not link_tag:
            continue
        tweet_path = link_tag["href"].strip()
        tweet_url = "https://nitter.net" + tweet_path

        # 2) Tweet text
        content_div = item.select_one("div.tweet-content")
        tweet_text = ""
        if content_div:
            # Collect all <p> or <span> inside and join their text
            parts = []
            for node in content_div.find_all(["p", "span"]):
                text = node.get_text(separator=" ", strip=True)
                if text:
                    parts.append(text)
            tweet_text = " ".join(parts).strip()

        # 3) First image (if any)
        img_url = ""
        attachment = item.select_one("div.attachments img")
        if attachment and attachment.get("src"):
            raw_src = attachment["src"].strip()
            img_url = raw_src if raw_src.startswith("http") else "https://nitter.net" + raw_src

        # 4) Published date: <span class="tweet-date"> <a title="…">…
        date_span = item.select_one("span.tweet-date a")
        published_dt = None
        if date_span and date_span.get("title"):
            # Format is like "Jun 04, 2025 · 07:52:15 PM"
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


# ─── BUILD AND WRITE RSS ──────────────────────────────────────────────────────────

def build_feed(tweets: list):
    """
    Given a list of tweets (each with link, text, image, published),
    write out an RSS2.0 file named OUTPUT_FILENAME.
    """
    feed = Rss201rev2Feed(
        title="THPORTH • MLB Tweets",
        link="https://thporth.com/",
        description="Latest tweets from @MLB via Nitter",
        language="en",
        last_build_date=datetime.utcnow()
    )

    for tw in tweets:
        # Format pubDate as RFC-2822
        if tw["published"]:
            pubdate_str = tw["published"].strftime("%a, %d %b %Y %H:%M:%S +0000")
        else:
            pubdate_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

        # Build <description> CDATA with text + image if present
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

        # Use first 50 chars of text as a short title
        short_title = tw["text"][:50] + ("…" if len(tw["text"]) > 50 else "")

        feed.add_item(
            title=f"@MLB: {short_title}",
            link=tw["link"],
            description=f"<![CDATA[{description_html}]]>",
            pubdate=pubdate_str
        )

    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as fp:
        feed.write(fp, "utf-8")


def main():
    tweets = fetch_nitter_tweets(NITTER_URL, TWEETS_TO_FETCH)
    build_feed(tweets)
    print(f"Wrote {len(tweets)} items to {OUTPUT_FILENAME}")


if __name__ == "__main__":
    main()
