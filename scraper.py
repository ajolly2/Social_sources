
import csv
import requests
import feedparser
from feedgenerator import Rss201rev2Feed
from bs4 import BeautifulSoup
import datetime

# CSV URLs per platform
CSV_URLS = {
    'X': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTEz2MZh1rsBpDf5SzS_OVSy2YCNaNZBO4yOZSpZqlbqs7oEOeWcOvpaSrY3KT8hYhxn2IYvsPbMklu/pub?gid=0&single=true&output=csv',
    'Reddit': 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTEz2MZh1rsBpDf5SzS_OVSy2YCNaNZBO4yOZSpZqlbqs7oEOeWcOvpaSrY3KT8hYhxn2IYvsPbMklu/pub?gid=1893373667&single=true&output=csv'
}

def fetch_accounts(platform):
    response = requests.get(CSV_URLS[platform])
    lines = response.text.strip().split("\n")[1:]  # skip header
    return [line.split(',')[2].strip() for line in lines if len(line.split(',')) > 2]

def extract_image_x(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        html = requests.get(url, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, 'html.parser')
        images = soup.find_all('img')
        for img in images:
            src = img.get('src', '')
            if 'pbs.twimg.com/media' in src and not 'profile_images' in src:
                return src
    except Exception:
        return ''
    return ''

def extract_image_reddit(entry):
    if 'media_content' in entry and entry.media_content:
        return entry.media_content[0]['url']
    if 'media_thumbnail' in entry and entry.media_thumbnail:
        return entry.media_thumbnail[0]['url']
    soup = BeautifulSoup(entry.get('summary', ''), 'html.parser')
    img = soup.find('img')
    return img['src'] if img and 'src' in img.attrs else ''

def parse_x():
    items = []
    for url in fetch_accounts('X'):
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            title_tag = soup.find('title')
            title = title_tag.text if title_tag else url
            post_url = url
            image = extract_image_x(url)
            now = datetime.datetime.utcnow()
            items.append({
                'title': f"@@{title}:",
                'link': post_url,
                'description': f"<br/><img src='{image}'/>" if image else '',
                'pubdate': now
            })
        except Exception:
            continue
    return items

def parse_reddit():
    items = []
    for url in fetch_accounts('Reddit'):
        d = feedparser.parse(url)
        for entry in d.entries:
            image = extract_image_reddit(entry)
            items.append({
                'title': f"@@reddit/{entry.get('author', 'unknown')}: {entry.title}",
                'link': entry.link,
                'description': f"{entry.summary}<br/><img src='{image}'/>" if image else entry.summary,
                'pubdate': datetime.datetime(*entry.published_parsed[:6]) if 'published_parsed' in entry else datetime.datetime.utcnow()
            })
    return items

def generate_rss(items, filename="social_feed.xml"):
    feed = Rss201rev2Feed(
        title="THPORTH Social Feed",
        link="https://thporth.com/",
        description="Aggregated social posts from multiple platforms",
        language="en"
    )
    items.sort(key=lambda x: x['pubdate'], reverse=True)
    seen = set()
    for item in items:
        key = item['title'] + item['description']
        if any(similarity(key, s) >= 0.75 for s in seen):
            continue
        seen.add(key)
        feed.add_item(
            title=item['title'],
            link=item['link'],
            description=item['description'],
            pubdate=item['pubdate']
        )
    with open(filename, 'w', encoding='utf-8') as f:
        feed.write(f, 'utf-8')

def similarity(a, b):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio()

if __name__ == '__main__':
    all_items = parse_x() + parse_reddit()
    generate_rss(all_items)
