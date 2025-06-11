import os
import re
import json
import requests
from datetime import datetime

URL = "https://www.livesportsontv.com/"

def scrape_livesportsontv():
    # 1) Download the page
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    html = resp.text

    # 2) Extract the JSON DATA array from the embedded "schemaFixtures" block
    m = re.search(r'"DATA"\s*:\s*(\[\s*\{.*?\}\s*\])\s*,\s*"META"', html, re.DOTALL)
    if not m:
        raise RuntimeError("Could not locate the main DATA array in the page")

    tournaments = json.loads(m.group(1))

    listings = []
    # 3) Find the USA MLB tournament
    for tour in tournaments:
        if tour.get("SHORT_NAME") == "MLB" and tour.get("COUNTRY_NAME") == "USA":
            for ev in tour.get("EVENTS", []):
                # parse the UTC timestamp
                ts = ev.get("START_UTIME") or ev.get("START_TIME")
                start = datetime.utcfromtimestamp(ts).isoformat() if ts else None

                # collect **all** broadcast channel names exactly as given
                chans = [c.get("name") for c in ev.get("channels", []) if c.get("name")]

                listings.append({
                    "league":            "MLB",
                    "home":              ev.get("HOME_NAME"),
                    "away":              ev.get("AWAY_NAME"),
                    "start_time":        start,
                    "channels_broadcast":chans
                })
            break

    # 4) Write to raw_tv.json
    os.makedirs("data", exist_ok=True)
    with open("data/raw_tv.json", "w") as f:
        json.dump(listings, f, indent=2)

    return listings

if __name__ == "__main__":
    out = scrape_livesportsontv()
    print(f"Extracted {len(out)} MLB broadcast listings")
