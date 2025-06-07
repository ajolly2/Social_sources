import cloudscraper
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
import re

# ——————————————————————————————————
# Use cloudscraper to bypass Cloudflare JS
scraper = cloudscraper.create_scraper()

# Today’s date in UTC
TODAY = datetime.now(timezone.utc).strftime('%Y-%m-%d')
SITEMAP_INDEX = 'https://www.livesoccertv.com/sitemap/sitemap_index.xml'

def get_today_sitemap_urls():
    """Fetch sitemap index and return all URLs for today’s pages."""
    r = scraper.get(SITEMAP_INDEX)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    urls = []
    for sm in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
        loc = sm.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
        if TODAY in loc:
            r2 = scraper.get(loc)
            r2.raise_for_status()
            sub = ET.fromstring(r2.text)
            for u in sub.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                urls.append(u.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text)
    return urls

def parse_league_page(url):
    """Scrape one league page for date, league name, matches and streams."""
    r = scraper.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    date = soup.find('h2', text=re.compile(r'\w+day,\s+\d+\s+\w+')).get_text(strip=True)
    out = []
    for section in soup.select('.wrap .stat-wrap'):
        league = section.find('h3').get_text(strip=True)
        for row in section.select('tr'):
            cols = row.find_all('td')
            if len(cols) < 2: 
                continue
            time_cell = cols[0].get_text(strip=True)
            match_txt = cols[1].get_text(" ", strip=True)
            stream    = cols[-1].get_text(strip=True)

            m = re.match(r'(.+?)\s+(\d+\s*-\s*\d+)\s+(.+)', match_txt)
            if m:
                home, score, away = m.groups()
            else:
                parts = match_txt.split(' vs ')
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
