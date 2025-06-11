import os
import requests
import json
from datetime import datetime

URL = "https://www.livesportsontv.com/"

def scrape_livesportsontv():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    html = resp.text

    # 1) Find the unquoted keyword
    idx = html.find("schemaFixtures")
    if idx < 0:
        raise RuntimeError("Could not locate schemaFixtures in HTML")

    # 2) Find the first brace after that point
    start = html.find("{", idx)
    if start < 0:
        raise RuntimeError("Could not find opening brace for schemaFixtures")

    # 3) Brace‐match to find the end
    depth = 0
    for i, ch in enumerate(html[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    else:
        raise RuntimeError("Unbalanced braces scanning schemaFixtures")

    raw = html[start:end]
    schema = json.loads(raw)
    fixtures = schema.get("oldFixtures", [])

    tv_listings = []
    for ev in fixtures:
        if ev.get("league") != "MLB":
            continue

        dt = datetime.fromisoformat(ev["date"].replace("Z",""))
        start_time = dt.isoformat()

        channels = ev.get("channels", [])
        chan = channels[0].get("shortname") if channels else None

        tv_listings.append({
            "league":     ev["league"],
            "home":       ev["home_team"],
            "away":       ev["visiting_team"],
            "start_time": start_time,
            "channel":    chan
        })

    os.makedirs("data", exist_ok=True)
    with open("data/raw_tv.json", "w") as f:
        json.dump(tv_listings, f, indent=2)

    return tv_listings

if __name__ == "__main__":
    lst = scrape_livesportsontv()
    print(f"Extracted {len(lst)} TV listings")
