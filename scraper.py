import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
import re

# ——————————————————————————————————————————————————————————————
# Spoof a browser User-Agent & language on every request
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/115.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9'
}

# Today’s date in UTC, timezone-aware to silence the deprecation warning
TODAY = datetime.now(timezone.utc).strftime('%Y-%m-%d')

# Sitemap index URL
SITEMAP_INDEX = 'https://www.livesoccertv.com/sitemap/sitemap_index.xml'


def get_today_sitemap_urls():
    """Fetch the sitemap index, find today’s sub-sitemaps, and return all page URLs."""
    r = requests.get(SITEMAP_INDEX, headers=HEADERS)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    urls = []

    for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
        loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
        if TODAY in loc:
            # fetch that date’s sitemap
            r2 = requests.get(loc, headers=HEADERS)
            r2.raise_for_status()
            subroot = ET.fromstring(r2.text)
            for url in subroot.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                urls.append(
                    url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
                )
    return urls


def parse_league_page(url):
    """Scrape one league page for date, league name, matches and streams."""
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    # 1) Date header: “Saturday, 7 June”
    date = soup.find('h2', text=re.compile(r'\w+day,\s+\d+\s+\w+')).get_text(strip=True)

    out = []
    # 2) Each .stat-wrap section is one league
    for section in soup.select('.wrap .stat-wrap'):
        league = section.find('h3').get_text(strip=True)

        # 3) Each table row is one match
        for row in section.select('tr'):
            cols = row.find_all('td')
            if len(cols) < 2:
                continue

            time_cell = cols[0].get_text(strip=True)
            match_text = cols[1].get_text(" ", strip=True)
            stream = cols[-1].get_text(strip=True)

            # 4) Split “Home 1 - 0 Away” vs “Home vs Away”
            m = re.match(r'(.+?)\s+(\d+\s*-\s*\d+)\s+(.+)', match_text)
            if m:
                home, score, away = m.groups()
            else:
                parts = match_text.split(' vs ')
                home, away = (parts + [""])[:2]
                score = ''

            out.append({
                'date':   date,
                'league': league,
                'time':   time_cell,
                'home':   home,
                'away':   away,
                'score':  score,
                'stream': stream,
                'url':    url
            })
    return out


def main():
    all_matches = []
    for league_url in get_today_sitemap_urls():
        all_matches += parse_league_page(league_url)

    with open('data.json', 'w') as f:
        json.dump(all_matches, f, indent=2)


if __name__ == '__main__':
    main()
