import os
import re
import json
import requests
from datetime import datetime

URL = "https://www.livesportsontv.com/"

def scrape_livesportsontv():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    html = resp.text

    # Look for schemaFixtures (case-insensitive), quoted with ' or "
    pattern = re.compile(
        r"""['"]schemaFixtures['"]\s*:\s*(\{.*?\})\s*,\s*['"]schemaTables['"]""",
        re.DOTALL | re.IGNORECASE
    )
    m = pattern.search(html)
    if not m:
        raise RuntimeError("Could not extract schemaFixtures JSON")

    schema_obj = json.loads(m.group(1))
    tournaments = schema_obj.get("DATA") or schema_obj.get("data") or []

    tv_listings = []
    for tour in tournaments:
        if tour.get("SHORT_NAME") != "MLB" or tour.get("COUNTRY_NAME") != "USA":
            continue

        for ev in tour.get("EVENTS", []):
            ts = ev.get("START_UTIME") or ev.get("START_TIME")
            start_time = datetime.utcfromtimestamp(ts).isoformat() if ts else None

            chans = [c.get("shortname") for c in ev.get("channels", []) if c.get("shortname")]

            tv_listings.append({
                "league":     "MLB",
                "home":       ev.get("HOME_NAME"),
                "away":       ev.get("AWAY_NAME"),
                "start_time": start_time,
                "channels":   chans
            })
        break

    os.makedirs("data", exist_ok=True)
    with open("data/raw_tv.json", "w") as f:
        json.dump(tv_listings, f, indent=2)

    return tv_listings

if __name__ == "__main__":
    listings = scrape_livesportsontv()
    print(f"Extracted {len(listings)} MLB listings")
