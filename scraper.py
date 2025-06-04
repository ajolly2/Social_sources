#!/usr/bin/env python3
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from feedgenerator import Rss201rev2Feed

# ─── CONFIGURATION ──────────────────────────────────────────────────────────────

# 1) List of Twitter/X handles (without the '@') to include:
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
    # …you can append more handles as you like…
]

# 2) Delay between fetching each account’s RSSHub feed (seconds):
DELAY_BETWEEN_REQUESTS = 2.0

# 3) The RSSHub base URL for Twitter user feeds:
#    (This public instance is free to use: https://rsshub.app)
RSSHUB_BASE = "https://rsshub.app/twitter/user"

# 4) Output filename for our merged RSS:
OUTPUT_RSS_FILE = "social_feed.xml"


# ─── HELPERS ────────────────────────────────────────────────────────────────────

def fetch_rsshub_feed(username: str):
    """
    Fetch the RSS feed for a given Twitter/X username via RSSHub.
    Returns a list of dicts: [{"id","title","link","description","published"}, …].
    If anything goes wrong (HTTP error, parse error), returns [].
    """
    url = f"{RSSHUB_BASE}/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SocialFeedBot/1.0; +https://thporth.com/)"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as ex:
        print(f"[ERROR] Failed to GET {url}: {ex}")
        return []

    # Parse the returned RSS XML
    try:
        root = ET.fromstring(resp.content)
    except Exception as ex:
        print(f"[ERROR] Failed to parse XML from {url}: {ex}")
        return []

    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for itm in channel.findall("item"):
        title   = itm.findtext("title")       or ""
        link    = itm.findtext("link")        or ""
        desc    = itm.findtext("description") or ""
        pubstr  = itm.findtext("pubDate")     or ""

        # Parse pubDate (e.g. "Wed, 04 Jun 2025 15:12:00 +0000")
        try:
            pub_dt = datetime.strptime(pubstr, "%a, %d %b %Y %H:%M:%S %z")
        except Exception:
            pub_dt = datetime.now(timezone.utc)

        # Use <link> as unique ID
        items.append({
            "id":          link,
            "title":       title,
            "link":        link,
            "description": desc,
            "published":   pub_dt
        })

    return items


def build_merged_rss(all_items: list):
    """
    Given a list of item‐dicts with keys "id","title","link","description","published",
    sort them by published (newest first) and write a single RSS 2.0 file.
    """
    feed = Rss201rev2Feed(
        title          = "THPORTH Social Feed",
        link           = "https://thporth.com/",
        description    = "Aggregated tweets from multiple X.com accounts (via RSSHub)",
        language       = "en",
        last_build_date= datetime.now(timezone.utc)
    )

    # Sort descending by timestamp
    sorted_items = sorted(all_items, key=lambda x: x["published"], reverse=True)

    for itm in sorted_items:
        pub_str = itm["published"].strftime("%a, %d %b %Y %H:%M:%S +0000")
        feed.add_item(
            title       = itm["title"],
            link        = itm["link"],
            description = itm["description"],
            unique_id   = itm["id"],
            pubdate     = pub_str
        )

    with open(OUTPUT_RSS_FILE, "w", encoding="utf-8") as fp:
        feed.write(fp, "utf-8")
    print(f"[OK] Wrote {len(sorted_items)} items to {OUTPUT_RSS_FILE}")


def main():
    all_collected = []

    for acct in ACCOUNTS:
        print(f"[INFO] Fetching RSSHub for @{acct} …")
        items = fetch_rsshub_feed(acct)
        print(f"[INFO]   Retrieved {len(items)} items from @{acct}.")
        all_collected.extend(items)
        time.sleep(DELAY_BETWEEN_REQUESTS)

    build_merged_rss(all_collected)


if __name__ == "__main__":
    main()
