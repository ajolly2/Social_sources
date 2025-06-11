# livesports_scraper.py

import os
import json
import requests
from datetime import datetime, timezone

# ────────────────────────────────────────────
# Inline your SPORTS list and API URL template
#
# Replace these with the exact values from your
# backend/constants.py so this script can run
# standalone without Django.
# ────────────────────────────────────────────

SPORTS = [
    {"slug": "mlb",  "name": "Major League Baseball"},
    {"slug": "nba",  "name": "National Basketball Association"},
    {"slug": "wnba", "name": "Women’s National Basketball Association"},
    {"slug": "nhl",  "name": "National Hockey League"},
]

# Example URL template from your constants — be sure it matches.
# In Django you used:
#   api_url = LIVESPORTSONTV_API.format(sport_slug=sport_slug)
LIVESPORTSONTV_API = "https://api.livesportsontv.com/v1/schedules/{sport_slug}.json"


def scrape_livesportsontv():
    """
    Fetches the LivesportsOnTV JSON for each sport in SPORTS,
    extracts every fixture’s broadcast channels, and writes
    them to data/raw_tv.json.
    """
    listings = []

    for sport in SPORTS:
        slug = sport.get("slug")
        if not slug:
            continue

        api_url = LIVESPORTSONTV_API.format(sport_slug=slug)
        resp = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()

        data = resp.json()  # expected to be a list of fixtures
        for ev in data:
            # Parse the ISO date (e.g. "2025-06-11T00:10:00.000Z")
            raw_date = ev.get("date")
            if not raw_date:
                continue
            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            start = dt.astimezone(timezone.utc).isoformat()

            # Collect every channel name
            chans = [c.get("name") for c in ev.get("channels", []) if c.get("name")]

            listings.append({
                "league":             ev.get("league"),
                "home":               ev.get("home_team"),
                "away":               ev.get("visiting_team"),
                "start_time":         start,
                "channels_broadcast": chans
            })

    # Write out to data/raw_tv.json
    os.makedirs("data", exist_ok=True)
    with open("data/raw_tv.json", "w") as f:
        json.dump(listings, f, indent=2)

    return listings


if __name__ == "__main__":
    out = scrape_livesportsontv()
    print(f"Wrote {len(out)} listings to data/raw_tv.json")
