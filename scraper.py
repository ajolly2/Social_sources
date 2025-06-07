import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

SITEMAP_INDEX = 'https://www.livesoccertv.com/sitemap/sitemap_index.xml'
TODAY = datetime.utcnow().strftime('%Y-%m-%d')

def get_today_sitemap_urls():
    r = requests.get(SITEMAP_INDEX)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    urls = []
    for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
        loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
        if TODAY in loc:
            r2 = requests.get(loc)
            r2.raise_for_status()
            subroot = ET.fromstring(r2.text)
            for url in subroot.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                urls.append(url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text)
    return urls

def parse_league_page(url):
    r = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept-Language': 'en-US,en;q=0.9'
    })
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    date = soup.find('h2', text=re.compile(r'\w+day,\s+\d+\s+\w+')).get_text(strip=True)
    out = []
    for section in soup.select('.wrap .stat-wrap'):
        league = section.find('h3').get_text(strip=True)
        for row in section.select('tr'):
            cols = row.find_all('td')
            if len(cols) < 2: continue
            time_cell = cols[0].get_text(strip=True)
            match_text = cols[1].get_text(" ", strip=True)
            stream = cols[-1].get_text(strip=True)
            m = re.match(r'(.+?)\s+(\d+\s*-\s*\d+)\s+(.+)', match_text)
            if m:
                home, score, away = m.groups()
            else:
                parts = match_text.split(' vs ')
                home, away = parts if len(parts)==2 else (match_text, '')
                score = ''
            out.append({
                'date': date,
                'league': league,
                'time': time_cell,
                'home': home,
                'away': away,
                'score': score,
                'stream': stream,
                'url': url
            })
    return out

def main():
    all_matches = []
    for league_url in get_today_sitemap_urls():
        all_matches += parse_league_page(league_url)
    with open('data.json','w') as f:
        json.dump(all_matches, f, indent=2)

if __name__ == '__main__':
    main()
