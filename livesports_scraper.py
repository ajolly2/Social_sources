import os
import re
import json
import requests
from datetime import datetime

URL = "https://www.livesportsontv.com/"

def scrape_livesportsontv():
    # 1. Fetch the page
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    html = resp.text

    # 2. Extract the JSON under "schemaFixtures"
    m = re.search(r'"schemaFixtures"\s*:\s*(\{.*?\})\s*,\s*"schemaTables"', html, re.DOTALL)
    if not m:
        raise RuntimeError("Could not locate schemaFixtures JSON")
    schema = json.loads(m.group(1))

    # 3. Grab the oldFixtures array
    fixtures = schema.get("oldFixtures", [])

    tv_listings = []
    for ev in fixtures:
        if ev.get("league") != "MLB":
            continue

        # parse the UTC ISO date
        dt = datetime.fromisoformat(ev["date"].replace("Z", ""))
        start_time = dt.isoformat()

        # extract the first channel shortname
        channels = ev.get("channels", [])
        chan = channels[0]["shortname"] if channels else None

        tv_listings.append({
            "league":     ev["league"],
            "home":       ev["home_team"],
            "away":       ev["visiting_team"],
            "start_time": start_time,
            "channel":    chan
        })

    # write result
    os.makedirs("data", exist_ok=True)
    with open("data/raw_tv.json", "w") as f:
        json.dump(tv_listings, f, indent=2)

    return tv_listings

if __name__ == "__main__":
    listings = scrape_livesportsontv()
    print(f"Extracted {len(listings)} TV listings")
