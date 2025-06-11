# livesports_scraper.py

import os
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup

URL = "https://www.livesportsontv.com/"

def scrape_livesportsontv():
    resp = requests.get(URL, headers={"User-Agent":"Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    listings = []

    # 1) Find the Baseball sport header
    baseball_header = soup.find("h3", string="Baseball")
    if not baseball_header:
        raise RuntimeError("Baseball header not found")

    # The MLB league section is the next <a href="/league/mlb"> ancestor
    mlb_section = baseball_header.find_next("a", href="/league/mlb")
    if not mlb_section:
        raise RuntimeError("MLB league header not found")

    # The events container follows that link
    events_container = mlb_section.find_next_sibling("div", class_="events")
    if not events_container:
        raise RuntimeError("MLB events container not found")

    # 2) Iterate each <div class="event ...">
    for ev_div in events_container.find_all("div", class_="event"):
        # Time
        time_tag = ev_div.select_one("div.event__info--time time")
        time_str = time_tag.get_text(strip=True) if time_tag else None

        # Build an ISO timestamp using today’s date (adjust as needed)
        if time_str:
            today = datetime.utcnow().date()
            dt = datetime.strptime(f"{today} {time_str.lower()}", "%Y-%m-%d %I:%M %p")
            start_time = dt.isoformat()
        else:
            start_time = None

        # Teams
        home = ev_div.select_one(".event__participant--home")
        away = ev_div.select_one(".event__participant--away")
        # remove any trailing @
        home_team = home.get_text(strip=True).rstrip(" @") if home else None
        away_team = away.get_text(strip=True) if away else None

        # Channels — both <li class="channel-link"> and <li> with channel-container
        channel_texts = []
        for li in ev_div.select("ul.event__tags li"):
            text = li.get_text(strip=True)
            # skip the "MORE" link
            if text and text.upper() != "MORE":
                channel_texts.append(text)

        listings.append({
            "league":             "MLB",
            "home":               home_team,
            "away":               away_team,
            "start_time":         start_time,
            "channels_broadcast": channel_texts
        })

    # Write out
    os.makedirs("data", exist_ok=True)
    with open("data/raw_tv.json", "w") as f:
        json.dump(listings, f, indent=2)

    return listings

if __name__ == "__main__":
    out = scrape_livesportsontv()
    print(f"Wrote {len(out)} listings to data/raw_tv.json")
