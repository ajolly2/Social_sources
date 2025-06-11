import os
import re
import json
import requests
from datetime import datetime

URL = "https://www.livesportsontv.com/"

def scrape_livesportsontv():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    html = resp.text

    # 1) Find the "DATA":[ part (first occurrence under schemaFixtures)
    idx = html.find('"DATA":[')
    if idx < 0:
        raise RuntimeError("Could not locate DATA array")
    start = html.find("[", idx)
    depth = 0
    for i, ch in enumerate(html[start:], start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    raw_data = html[start:end]

    # 2) Parse the full DATA array
    tournaments = json.loads(raw_data)

    tv_listings = []
    # 3) Find USA MLB tournament
    for tour in tournaments:
        if tour.get("SHORT_NAME") == "MLB" and tour.get("COUNTRY_NAME") == "USA":
            for ev in tour.get("EVENTS", []):
                ts = ev.get("START_UTIME") or ev.get("START_TIME")
                start_time = datetime.utcfromtimestamp(ts).isoformat() if ts else None

                # collect every channel
                chans = [c.get("shortname") for c in ev.get("channels", []) if c.get("shortname")]

                tv_listings.append({
                    "league":     "MLB",
                    "home":       ev.get("HOME_NAME"),
                    "away":       ev.get("AWAY_NAME"),
                    "start_time": start_time,
                    "channels":   chans
                })
            break  # done with MLB

    os.makedirs("data", exist_ok=True)
    with open("data/raw_tv.json", "w") as f:
        json.dump(tv_listings, f, indent=2)

    return tv_listings

if __name__ == "__main__":
    lst = scrape_livesportsontv()
    print(f"Extracted {len(lst)} MLB listings")
