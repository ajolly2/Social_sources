# livesports_scraper.py

import os
import json
import requests
from datetime import datetime, timezone
from backend.constants import SPORTS, LIVESPORTSONTV_API

def scrape_livesportsontv():
    """
    Uses your existing LIVESPORTSONTV_API endpoint and SPORTS list to fetch
    JSON for every sport slug, then extracts each fixture's broadcast channels.
    """
    listings = []

    for sport in SPORTS:
        slug = sport.get("slug")
        if not slug:
            continue
        api_url = LIVESPORTSONTV_API.format(sport_slug=slug)
        resp = requests.get(api_url, headers={"User-Agent":"Mozilla/5.0"})
        resp.raise_for_status()
        data = resp.json()  # list of fixture dicts

        for ev in data:
            # parse UTC datetime from the 'date' field
            raw = ev.get("date")
            if not raw:
                continue
            dt = datetime.fromisoformat(raw.replace("Z","+00:00"))
            start = dt.astimezone(timezone.utc).isoformat()

            # collect all broadcast channel entries
            chans = [c.get("name") for c in ev.get("channels", []) if c.get("name")]

            listings.append({
                "league":            ev.get("league"),
                "home":              ev.get("home_team"),
                "away":              ev.get("visiting_team"),
                "start_time":        start,
                "channels_broadcast":chans
            })

    # write out
    os.makedirs("data", exist_ok=True)
    with open("data/raw_tv.json","w") as f:
        json.dump(listings, f, indent=2)

    return listings

if __name__ == "__main__":
    out = scrape_livesportsontv()
    print(f"Wrote {len(out)} TV listings to data/raw_tv.json")
