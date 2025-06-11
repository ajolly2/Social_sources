# livesports_scraper.py

import os
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup

BASE = "https://www.livesportsontv.com"

def extract_channels(ev):
    out = []
    for li in ev.select("ul.event__tags li"):
        txt = li.get_text(strip=True)
        if txt and txt.upper() != "MORE":
            out.append(txt)
    return out

def scrape_league(league_slug):
    """
    Scrape /league/{league_slug} page.
    """
    url = f"{BASE}/league/{league_slug}"
    r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # find the schedule block
    schedule = soup.select_one("div.date-events")
    if not schedule:
        raise RuntimeError(f"{league_slug.upper()} schedule block not found")

    listings = []
    for block in schedule.select("div.events > div[style]"):
        date_box = block.select_one("div.event__info--date")
        if not date_box:
            continue
        # parse date
        day = date_box.find("b").get_text()
        mon = date_box.find("span").get_text()
        date_str = f"{day} {mon} {datetime.utcnow().year}"
        for ev in block.select("div.event"):
            time_tag = ev.select_one("div.event__info--time time")
            teams = ev.select(".event__participant")
            channels = extract_channels(ev)

            # build ISO datetime
            if time_tag:
                t = time_tag.get_text(strip=True)
                dt = datetime.strptime(f"{date_str} {t}", "%d %b %Y %I:%M %p")
                start = dt.isoformat()
            else:
                start = None

            home = ev.select_one(".event__participant--home")
            away = ev.select_one(".event__participant--away")
            listings.append({
                "league":   league_slug.upper(),
                "date":     date_str,
                "time":     t if time_tag else None,
                "start":    start,
                "home":     home.get_text(strip=True).rstrip(" @") if home else None,
                "away":     away.get_text(strip=True) if away else None,
                "channels": channels
            })

    # write out
    os.makedirs("data", exist_ok=True)
    with open(f"data/raw_{league_slug}.json", "w") as f:
        json.dump(listings, f, indent=2)

    return listings

if __name__ == "__main__":
    wnba = scrape_league("wnba")
    print(f"Wrote {len(wnba)} WNBA games")
