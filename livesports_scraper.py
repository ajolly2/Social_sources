import os
import re
import json
import requests
from datetime import datetime

URL = "https://www.livesportsontv.com/"

def scrape_livesportsontv():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    html = resp.text

    # Regex to capture the JS object assigned to schemaFixtures
    m = re.search(
        r'schemaFixtures\s*=\s*(\{.*?\})\s*;'
        , html, re.DOTALL
    )
    if not m:
        raise RuntimeError("Could not extract schemaFixtures JS object")

    schema_obj = json.loads(m.group(1))
    tournaments = schema_obj.get("DATA", [])

    tv_listings = []
    for tour in tournaments:
        if tour.get("SHORT_NAME") != "MLB" or tour.get("COUNTRY_NAME") != "USA":
            continue
        for ev in tour.get("EVENTS", []):
            ts = ev.get("START_UTIME") or ev.get("START_TIME")
            dt = datetime.utcfromtimestamp(ts) if ts else None
            start = dt.isoformat() if dt else None

            chans = [c.get("shortname") for c in ev.get("channels", []) if c.get("shortname")]

            tv_listings.append({
                "league":     "MLB",
                "home":       ev.get("HOME_NAME"),
                "away":       ev.get("AWAY_NAME"),
                "start_time": start,
                "channels":   chans
            })
        break

    os.makedirs("data", exist_ok=True)
    with open("data/raw_tv.json", "w") as f:
        json.dump(tv_listings, f, indent=2)

    return tv_listings

if __name__ == "__main__":
    lst = scrape_livesportsontv()
    print(f"Extracted {len(lst)} MLB TV listings")
