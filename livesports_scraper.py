import os
import re
import json
import requests
from datetime import datetime

URL = "https://www.livesportsontv.com/"

def scrape_livesportsontv():
    # 1. Get raw HTML
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    html = resp.text

    # 2. Find the fixtures JSON blob
    #    It starts with [{"fixture_id": and ends with }]
    m = re.search(r'(\[\s*{\s*"fixture_id".*?\}\s*\])', html, re.DOTALL)
    if not m:
        raise RuntimeError("Could not locate fixtures JSON in page")

    fixtures = json.loads(m.group(1))

    tv_listings = []
    for ev in fixtures:
        # Only MLB for now
        if ev.get("league") != "MLB":
            continue

        # parse ISO date to match FlashLive's format
        # ev["date"] is like "2025-06-11T23:10:00.000Z"
        dt = datetime.fromisoformat(ev["date"].replace("Z", ""))
        start_time = dt.isoformat()

        # build listing
        tv_listings.append({
            "league":     ev["league"],
            "home":       ev["home_team"],
            "away":       ev["visiting_team"],
            "start_time": start_time,
            # take the first channel shortname if available
            "channel":    ev.get("channels", [{}])[0].get("shortname")
        })

    # ensure data dir
    os.makedirs("data", exist_ok=True)
    # write out raw_tv.json
    with open("data/raw_tv.json", "w") as f:
        json.dump(tv_listings, f, indent=2)

    return tv_listings

if __name__ == "__main__":
    listings = scrape_livesportsontv()
    print(f"Extracted {len(listings)} TV listings")    
