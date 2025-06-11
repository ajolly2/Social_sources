import os, json, requests
from datetime import datetime

BASE = "https://www.livesportsontv.com"

def scrape_league_via_next(league_slug):
    url = f"{BASE}/league/{league_slug}"
    r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    text = r.text

    # extract the Next.js data blob
    start = text.find('<script id="__NEXT_DATA__"')
    if start < 0:
        raise RuntimeError("No __NEXT_DATA__ script found")
    start = text.find(">", start) + 1
    end   = text.find("</script>", start)
    blob  = text[start:end]
    data  = json.loads(blob)

    events = data["props"]["pageProps"]["events"]
    out = []
    for ev in events:
        # each ev has: id, date (YYYY-MM-DD), time, home, away, channels[]
        dt_str = f"{ev['date']} {ev['time']}"
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
            iso = dt.isoformat()
        except:
            iso = None

        out.append({
            "league":   league_slug.upper(),
            "start":    iso,
            "home":     ev["home"],
            "away":     ev["away"],
            "channels": [c["name"] for c in ev["channels"]],
        })

    # write file
    os.makedirs("data", exist_ok=True)
    with open(f"data/{league_slug}.json","w") as f:
        json.dump(out, f, indent=2)

    return out

if __name__ == "__main__":
    wnba = scrape_league_via_next("wnba")
    print(f"Wrote {len(wnba)} WNBA games")
