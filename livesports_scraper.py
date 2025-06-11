import os
import requests
import json
from datetime import datetime

URL = "https://www.livesportsontv.com/"

def scrape_livesportsontv():
    # 1. Download HTML
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    html = resp.text

    # 2. Extract the schemaFixtures.DATA object
    start_key = '"schemaFixtures":'
    idx = html.find(start_key)
    if idx < 0:
        raise RuntimeError("schemaFixtures not found")

    # find opening brace of the object, then "DATA":
    data_key = '"DATA":'
    idx_data = html.find(data_key, idx)
    start = html.find("[", idx_data)
    end = start
    depth = 0
    for i, ch in enumerate(html[start:], start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    tournaments = json.loads(html[start:end])

    tv_listings = []
    for tour in tournaments:
        # only the USA: MLB tournament
        if tour.get("SHORT_NAME") != "MLB" or tour.get("COUNTRY_NAME") != "USA":
            continue

        for ev in tour.get("EVENTS", []):
            # parse time
            ut = ev.get("START_UTIME") or ev.get("START_TIME")
            dt = datetime.utcfromtimestamp(ut) if ut else None
            start_time = dt.isoformat() if dt else None

            # collect all channels shortnames
            chans = [c.get("shortname") for c in ev.get("channels", []) if c.get("shortname")]

            tv_listings.append({
                "league":     "MLB",
                "home":       ev.get("HOME_NAME"),
                "away":       ev.get("AWAY_NAME"),
                "start_time": start_time,
                "channels":   chans    # **all** channels
            })

        # once you’ve processed the USA: MLB block, stop
        break

    os.makedirs("data", exist_ok=True)
    with open("data/raw_tv.json", "w") as f:
        json.dump(tv_listings, f, indent=2)

    return tv_listings

if __name__ == "__main__":
    lst = scrape_livesportsontv()
    print(f"Extracted {len(lst)} MLB TV listings")
