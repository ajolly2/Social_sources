# livesports_scraper.py

import os
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup

URL = "https://www.livesportsontv.com/"

def extract_channels_from_event(ev_div):
    """
    Given a <div class="event">…</div>, return the list of channel names.
    """
    channels = []
    for li in ev_div.select("ul.event__tags li"):
        text = li.get_text(strip=True)
        if not text or text.upper() == "MORE":
            continue
        channels.append(text)
    return channels

def scrape_livesportsontv_mlb():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 1. Find the MLB league header
    mlb_h4 = soup.find("h4", class_="date-events__league-header-title", string="MLB")
    if not mlb_h4:
        raise RuntimeError("MLB league header not found")
    league_header = mlb_h4.find_parent("div", class_="date-events__league-header")

    # 2. Find the corresponding events container
    events_container = league_header.find_next_sibling("div", class_="events")
    if not events_container:
        raise RuntimeError("MLB events container not found")

    listings = []
    # 3. Iterate each game block
    for ev in events_container.find_all("div", class_="event"):
        # Time → ISO string
        time_tag = ev.select_one("div.event__info--time time")
        if time_tag:
            t = time_tag.get_text(strip=True).lower()
            today = datetime.utcnow().date()
            dt = datetime.strptime(f"{today} {t}", "%Y-%m-%d %I:%M %p")
            start_time = dt.isoformat()
        else:
            start_time = None

        # Teams
        home_tag = ev.select_one(".event__participant--home")
        away_tag = ev.select_one(".event__participant--away")
        home = home_tag.get_text(strip=True).rstrip(" @") if home_tag else None
        away = away_tag.get_text(strip=True) if away_tag else None

        # Channels
        chans = extract_channels_from_event(ev)

        listings.append({
            "league":             "MLB",
            "home":               home,
            "away":               away,
            "start_time":         start_time,
            "channels_broadcast": chans
        })

    # 4. Write out
    os.makedirs("data", exist_ok=True)
    with open("data/raw_tv.json", "w") as f:
        json.dump(listings, f, indent=2)

    return listings

if __name__ == "__main__":
    out = scrape_livesportsontv_mlb()
    print(f"Wrote {len(out)} MLB listings to data/raw_tv.json")
