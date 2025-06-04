# scraper.py
import json
import csv
import time
import requests
from io import StringIO
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import feedparser

CSV_TABS = {
    "X": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTEz2MZh1rsBpDf5SzS_OVSy2YCNaNZBO4yOZSpZqlbqs7oEOeWcOvpaSrY3KT8hYhxn2IYvsPbMklu/pub?gid=0&single=true&output=csv",
    "Reddit": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTEz2MZh1rsBpDf5SzS_OVSy2YCNaNZBO4yOZSpZqlbqs7oEOeWcOvpaSrY3KT8hYhxn2IYvsPbMklu/pub?gid=1893373667&single=true&output=csv",
    "Instagram": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTEz2MZh1rsBpDf5SzS_OVSy2YCNaNZBO4yOZSpZqlbqs7oEOeWcOvpaSrY3KT8hYhxn2IYvsPbMklu/pub?gid=132310951&single=true&output=csv",
    "TikTok": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTEz2MZh1rsBpDf5SzS_OVSy2YCNaNZBO4yOZSpZqlbqs7oEOeWcOvpaSrY3KT8hYhxn2IYvsPbMklu/pub?gid=1615836936&single=true&output=csv",
    "Snapchat": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTEz2MZh1rsBpDf5SzS_OVSy2YCNaNZBO4yOZSpZqlbqs7oEOeWcOvpaSrY3KT8hYhxn2IYvsPbMklu/pub?gid=1149773381&single=true&output=csv"
}

def fetch_sources():
    sources = []
    for platform, url in CSV_TABS.items():
        try:
            resp = requests.get(url)
            reader = csv.DictReader(StringIO(resp.text))
            for row in reader:
                if row.get('platform') and row.get('account') and row.get('url'):
                    sources.append({
                        "platform": platform,
                        "account": row["account"].strip(),
                        "url": row["url"].strip()
                    })
        except Exception as e:
            print(f"Error fetching {platform}: {e}")
    return sources

def scrape_x(page, username):
    posts = []
    page.goto(f"https://x.com/{username}", timeout=60000)
    time.sleep(5)
    for el in page.query_selector_all("article div[lang]")[:5]:
        try:
            content = el.inner_text()
            time_tag = el.evaluate_handle("node => node.closest('article').querySelector('time')")
            timestamp = time_tag.get_property("dateTime").json_value() if time_tag else datetime.utcnow().isoformat()
            link_tag = el.evaluate_handle("node => node.closest('article').querySelector('a[role=link]')")
            link = link_tag.get_property("href").json_value() if link_tag else f"https://x.com/{username}"
            posts.append({
                "platform": "X",
                "account": username,
                "text": content,
                "url": f"https://x.com{link}",
                "date": timestamp
            })
        except:
            continue
    return posts

def scrape_reddit(url):
    posts = []
    feed = feedparser.parse(url + ".rss")
    for entry in feed.entries[:5]:
        posts.append({
            "platform": "Reddit",
            "account": url.split("/")[-2],
            "text": entry.title,
            "url": entry.link,
            "date": entry.published
        })
    return posts

def main():
    all_posts = []
    sources = fetch_sources()
    x_accounts = [s['account'] for s in sources if s['platform'] == 'X']
    reddit_urls = [s['url'] for s in sources if s['platform'] == 'Reddit']

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        for user in x_accounts:
            all_posts.extend(scrape_x(page, user))
        browser.close()

    for url in reddit_urls:
        all_posts.extend(scrape_reddit(url))

    all_posts.sort(key=lambda x: x['date'], reverse=True)

    with open("social_feed.json", "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
