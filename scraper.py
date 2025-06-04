# scraper.py

import feedparser
import time
import re
from datetime import datetime
from feedgenerator import Rss201rev2Feed
from bs4 import BeautifulSoup

# ───────────────────────────────────────────────────────────────────────────────
# 1)  List of X.com usernames (without “@”).  Each line below becomes
#     https://nitter.net/<username>/rss
#     Nitter’s /rss endpoint already returns a full RSS feed of that user’s tweets,
#     including embedded <img src="…"> where images appear.
# ───────────────────────────────────────────────────────────────────────────────
ACCOUNTS = [
    "espn",
    "CBSSports",
    "YahooSports",
    "SBNation",
    "BleacherReport",
    "Sports",         # “sports” is actually the @Sports account
    "SportsCenter",
    "SkySportsNews",
    "FOXSports",
    "BBCSport",
    "NBCSports",
    "TheAthletic",
    # …you can add more X usernames here over time
]


# ───────────────────────────────────────────────────────────────────────────────
# 2)  Helper to normalize any HTML snippet into plain lowercase text.
#     We use it to detect (and drop) near-duplicates: if the text of one tweet
#     is “contained” in another, we skip it.
#     (This is a quick & simple “50-75% match” by exact‐substring containment.
#      If you need something more advanced, you can switch to a word‐count
#      similarity or a fuzzy‐match routine.)
# ───────────────────────────────────────────────────────────────────────────────
def normalize_text(html_snippet):
    """
    Strip tags and whitespace from the HTML, collapse multiple spaces,
    and lowercase. Returns a single plain string.
    """
    soup = BeautifulSoup(html_snippet, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    # collapse multiple whitespace into one space
    text = re.sub(r"\s+", " ", text)
    return text.lower()


# ───────────────────────────────────────────────────────────────────────────────
# 3)  Fetch every account’s Nitter RSS, pull all <item> entries, and merge:
# ───────────────────────────────────────────────────────────────────────────────
all_entries = []

for user in ACCOUNTS:
    nitter_rss_url = f"https://nitter.net/{user}/rss"
    parsed = feedparser.parse(nitter_rss_url)

    if parsed.bozo:
        # If the Nitter instance is down or the feed is malformed, skip it.
        print(f"Warning: Could not parse RSS for {user} (URL: {nitter_rss_url})")
        continue

    for entry in parsed.entries:
        # Each entry normally has:
        #   - entry.title             (string, often “@username: tweet text…”)
        #   - entry.link              (URL to the tweet on nitter.net)
        #   - entry.published         (e.g. "Wed, 04 Jun 2025 12:52:15 +0000")
        #   - entry.published_parsed  (time.struct_time)
        #   - entry.summary           (HTML snippet including <p>text</p> + <img>…)
        #
        title = entry.get("title", "")
        link = entry.get("link", "")
        pub_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if not pub_struct:
            # Skip if no date
            continue

        pub_date_str = time.strftime("%a, %d %b %Y %H:%M:%S +0000", pub_struct)
        summary_html = entry.get("summary", "")

        all_entries.append({
            "source_user": user,
            "title": title,
            "link": link,
            "published_parsed": pub_struct,
            "pubDate": pub_date_str,
            "description_html": summary_html,
        })


# ───────────────────────────────────────────────────────────────────────────────
# 4)  Sort ALL entries by timestamp, descending (newest first)
# ───────────────────────────────────────────────────────────────────────────────
all_entries.sort(key=lambda e: e["published_parsed"], reverse=True)


# ───────────────────────────────────────────────────────────────────────────────
# 5)  De‐duplicate: keep only the first occurrence of any “normalized text.”
#     If one tweet’s text (after stripping tags) is contained within a previously
#     seen tweet’s text, we assume it’s a retweet or near‐duplicate and skip it.
# ───────────────────────────────────────────────────────────────────────────────
unique_entries = []
seen_texts = []

for e in all_entries:
    norm = normalize_text(e["description_html"])
    duplicate = False
    for prev in seen_texts:
        if (norm in prev) or (prev in norm):
            duplicate = True
            break
    if not duplicate:
        unique_entries.append(e)
        seen_texts.append(norm)


# ───────────────────────────────────────────────────────────────────────────────
# 6)  Build one aggregated RSS feed using feedgenerator.Rss201rev2Feed
#     We will wrap each <description> inside CDATA so that the embedded
#     <img src="…"> tags are preserved.
# ───────────────────────────────────────────────────────────────────────────────
feed = Rss201rev2Feed(
    title="THPORTH Social Feed",
    link="https://thporth.com/",
    description="Aggregated social posts from multiple X.com accounts (via Nitter).",
    language="en",
)

max_items = 50   # or however many “most recent” you want to keep

count = 0
for e in unique_entries:
    if count >= max_items:
        break

    # Make sure to wrap the HTML snippet in CDATA so that <img> appears verbatim.
    desc_cdata = f"<![CDATA[{e['description_html']}]]>"

    feed.add_item(
        title=e["title"],
        link=e["link"],
        description=desc_cdata,
        pubdate=datetime.strptime(e["pubDate"], "%a, %d %b %Y %H:%M:%S +0000"),
    )

    count += 1


# ───────────────────────────────────────────────────────────────────────────────
# 7)  Finally, write out the combined feed to social_feed.xml in UTF_
