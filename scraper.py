import json
import csv
import requests
from io import StringIO
from datetime import datetime
from difflib import SequenceMatcher
from playwright.sync_api import sync_playwright
import feedparser

CSV_TABS = {
    "X": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTEz2MZh1rsBpDf5SzS_OVSy2YCNaNZBO4yOZSpZqlbqs7oEOeWcOvpaSrY3KT8hYhxn2IYvsPbMklu/pub?gid=0&single=true&output=csv",
    "Reddit": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTEz2MZh1rsBpDf5SzS_OVSy2YCNaNZBO4yOZSpZqlbqs7oEOeWcOvpaSrY3KT8hYhxn2IYvsPbMklu/pub?gid=1893373667&single=true&output=csv"
}


def fetch_all_sources():
    all_sources = []
    for platform, url in CSV_TABS.items():
        try:
            resp = requests.get(url)
            data = resp.text
            reader = csv.DictReader(StringIO(data))
            for row in reader:
                if row.get('platform') and row.get('account') and row.get('url'):
                    all_sources.append({
                        "platform": row["platform"].strip(),
                        "account": row["account"].strip(),
                        "url": row["url"].strip()
                    })
        except Exception as e:
            print(f"Failed to fetch {platform}: {e}")
    return all_sources


def scrape_x_profile(page, username):
    tweets = []
    url = f"https://x.com/{username}"
    page.goto(url, timeout=60000)
    page.wait_for_timeout(5000)
    elements = page.query_selector_all("article div[lang]")
    for el in elements[:10]:
        try:
            content = el.inner_text()
            timestamp_el = el.evaluate_handle("node => node.closest('article').querySelector('time')")
            timestamp = timestamp_el.get_property("dateTime").json_value() if timestamp_el else datetime.utcnow().isoformat()
            link_el = el.evaluate_handle("node => node.closest('article').querySelector('a[role=link]')")
            link = link_el.get_property("href").json_value() if link_el else url
            tweets.append({
                "platform": "X",
                "user": username,
                "content": content.strip(),
                "url": "https://x.com" + link,
                "date": datetime.fromisoformat(timestamp.replace("Z", "")).isoformat()
            })
        except:
            continue
    return tweets


def parse_reddit_rss(url):
    posts = []
    feed = feedparser.parse(url + ".rss")
    for entry in feed.entries[:10]:
        posts.append({
            "platform": "Reddit",
            "user": url.split("/")[-2],
            "content": entry.title,
            "url": entry.link,
            "date": datetime(*entry.published_parsed[:6]).isoformat()
        })
    return posts


def is_similar(a, b):
    return SequenceMatcher(None, a, b).ratio() >= 0.75


def remove_duplicates(items):
    unique = []
    for item in items:
        if not any(is_similar(item["content"], other["content"]) for other in unique):
            unique.append(item)
    return unique


def main():
    sources = fetch_all_sources()
    x_accounts = [s['account'] for s in sources if s['platform'].lower() == 'x']
    reddit_urls = [s['url'] for s in sources if s['platform'].lower() == 'reddit']

    all_posts = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        for account in x_accounts:
            print(f"Scraping X @{account}")
            all_posts += scrape_x_profile(page, account)
        browser.close()

    for url in reddit_urls:
        print(f"Fetching Reddit feed: {url}")
        all_posts += parse_reddit_rss(url)

    all_posts.sort(key=lambda x: x["date"], reverse=True)
    filtered = remove_duplicates(all_posts)

    with open("social_feed.json", "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)
    print(f"[OK] Wrote {len(filtered)} items to social_feed.json")


if __name__ == "__main__":
    main()
