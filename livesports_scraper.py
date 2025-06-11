# livesports_scraper.py

import os
import re
import json
import requests
from datetime import datetime

URL = "https://www.livesportsontv.com/"

def scrape_livesportsontv():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    html = resp.text

    # Extract the "DATA":[ ... ] array that's under schemaFixtures
    m = re.search(r'"schemaFixtures"\s*:\s*\{.*?"DATA"\s*:\s*(\[\s*\{.*?\}\s*\])', html, re.DOTALL)
    if not m:
        raise RuntimeError("Could not locate schemaFixtures.DATA in page")

    tournaments = json.loads(m.group(1))

    listings = []
    # Find the USA MLB tournament
    for tour in tournaments:
        if tour.get("SHORT_NAME") == "MLB" and tour.get("COUNTRY_NAME") == "USA":
            for ev in tour.get("EVENTS", []):
                # parse UTC timestamp
                ts = ev.get("START_UTIME") or ev.get("START_TIME")
                start = datetime.utcfromtimestamp(ts).isoformat() if ts else None

                chans = [c.get("name") for c in ev.get("channels", []) if c.get("name")]
                listings.append({
                    "league":            "MLB",
                    "home":              ev.get("HOME_NAME"),
                    "away":              ev.get("AWAY_NAME"),
                    "start_time":        start,
                    "channels_broadcast":chans
                })
            break

    os.makedirs("data", exist_ok=True)
    with open("data/raw_tv.json", "w") as f:
        json.dump(listings, f, indent=2)

    return listings

if __name__ == "__main__":
    out = scrape_livesportsontv()
    print(f"Wrote {len(out)} listings to data/raw_tv.json")
