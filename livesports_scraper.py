#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import datetime

BASE_URL = "https://www.livesportsontv.com"

def scrape_league(league_slug):
    """
    Scrape the schedule + broadcast channels for a single league page,
    by pulling data out of the __NEXT_DATA__ JSON blob.
    """
    url = f"{BASE_URL}/league/{league_slug}"
    resp = requests.get(url)
    resp.raise_for_status()

    # extract the Next.js JSON blob
    soup = BeautifulSoup(resp.text, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script:
        raise RuntimeError(f"{league_slug.upper()} JSON data not found on page")

    data = json.loads(script.string)
    # drill into the pageProps -> events
    try:
        events = data["props"]["pageProps"]["events"]
    except KeyError:
        raise RuntimeError(f"{league_slug.upper()} events not found in JSON")

    out = []
    for ev in events:
        # skip any hidden/dontshow entries
        if ev.get("classNames") and "dontshow" in ev["classNames"]:
            continue

        info = ev.get("event", ev).get("event--wrapp", ev).get("matchInfo") or ev.get("event")
        # date/time
        dt_block = ev.get("event__info", ev).get("info", {}).get("time", {})
        date_str = dt_block.get("date")  # e.g. {"b": "11", "span": "Jun"}
        time_str = dt_block.get("time")  # e.g. "9:00 PM"
        if date_str and time_str:
            day = int(date_str["b"])
            mon = date_str["span"]
            # assume current year
            dt = datetime.datetime.strptime(f"{day} {mon} {datetime.datetime.now().year} {time_str}", "%d %b %Y %I:%M %p")
        else:
            dt = None

        # teams
        teams = ev.get("event__matchInfo", ev).get("matchInfo", {})
        home = teams.get("participant", [{}])[0].get("text") if teams.get("participant") else None
        away = teams.get("participant", [{}])[1].get("text") if teams.get("participant") and len(teams["participant"])>1 else None

        # channels
        tags = ev.get("event__tags", ev).get("tags", [])
        channels = []
        for tag in tags:
            text = tag.get("text") or tag.get("channel-text")
            href = tag.get("href") or tag.get("link")
            if text:
                channels.append({
                    "name": text,
                    "link": href
                })

        out.append({
            "datetime": dt.isoformat() if dt else None,
            "home": home,
            "away": away,
            "channels": channels
        })

    return out

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scrape LiveSportsOnTV league schedules")
    parser.add_argument("league", help="league slug (e.g. wnba, mlb, nfl)")
    args = parser.parse_args()

    schedule = scrape_league(args.league)
    print(json.dumps(schedule, indent=2))

if __name__ == "__main__":
    main()
