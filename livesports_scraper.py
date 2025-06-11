# livesports_scraper.py

import os
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup

URL = "https://www.livesportsontv.com/"

def extract_channels_from_event(ev_div):
    channels = []
    for li in ev_div.select("ul.event__tags li"):
        txt = li.get_text(strip=True)
        if txt and txt.upper() != "MORE":
            channels.append(txt)
    return channels

def scrape_livesportsontv_mlb():
    resp = requests.get(URL, headers={"User-Agent":"Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Find the MLB link
    mlb_link = soup.find("a", href="/league/mlb")
    if not mlb_link:
        raise RuntimeError("MLB <a href=\"/league/mlb\"> not found")

    # 2) From there, find the next sibling .events container
    #    The link is wrapped in a div, so climb up one and then find next .events
    league_div = mlb_link.find_parent("div", style=lambda v: v and "position" in v)
    events_container = league_div.find_next_sibling("div", class_="events")
    if not events_container:
        raise RuntimeError("MLB events container not found")

    listings = []
    for ev in events_container.find_all("div", class_="event"):
        # Time
        time_tag = ev.select_one("div.event__info--time time")
        if time_tag:
            t = time_tag.get_text(strip=True).lower()
            today = datetime.utcnow().date()
            dt = datetime.strptime(f"{today} {t}", "%Y-%m-%d %I:%M %p")
            start_time = dt.isoformat()
        else:
            start_time = None

        # Teams
        home = ev.select_one(".event__participant--home")
        away = ev.select_one(".event__participant--away")
        home_team = home.get_text(strip=True).rstrip(" @") if home else None
        away_team = away.get_text(strip=True) if away else None

        # Channels
        chan_list = extract_channels_from_event(ev)

        listings.append({
            "league":             "MLB",
            "home":               home_team,
            "away":               away_team,
            "start_time":         start_time,
            "channels_broadcast": chan_list
        })

    os.makedirs("data", exist_ok=True)
    with open("data/raw_tv.json", "w") as f:
        json.dump(listings, f, indent=2)

    return listings

if __name__ == "__main__":
    out = scrape_livesportsontv_mlb()
    print(f"Wrote {len(out)} MLB listings to data/raw_tv.json")
