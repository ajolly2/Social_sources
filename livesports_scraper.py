#!/usr/bin/env python3
import requests
import json
import argparse
import datetime
from bs4 import BeautifulSoup

BASE_URL = "https://www.livesportsontv.com"

def fetch_league_schedule(league_slug: str):
    url = f"{BASE_URL}/league/{league_slug}"
    resp = requests.get(url)
    resp.raise_for_status()

    # find the Next.js data blob
    soup = BeautifulSoup(resp.text, "html.parser")
    blob = soup.find("script", id="__NEXT_DATA__")
    if not blob:
        raise RuntimeError(f"No JSON data found on /league/{league_slug}")

    data = json.loads(blob.string)
    events = data["props"]["pageProps"].get("events", [])
    out = []

    for ev in events:
        # skip hidden/dontshow
        if "dontshow" in ev.get("classNames", []):
            continue

        # date + time
        info = ev.get("event__info", {}).get("time", {})
        date_obj = info.get("date")  # {"b":"11","span":"Jun"}
        time_str = info.get("time")  # "9:00 PM"
        dt = None
        if date_obj and time_str:
            day = int(date_obj["b"])
            mon = date_obj["span"]
            year = datetime.datetime.now().year
            dt = datetime.datetime.strptime(
                f"{day} {mon} {year} {time_str}",
                "%d %b %Y %I:%M %p"
            ).isoformat()

        # teams
        match = ev.get("event__matchInfo", {}).get("matchInfo", {})
        parts = match.get("participant", [])
        home = parts[0].get("text") if len(parts) > 0 else None
        away = parts[1].get("text") if len(parts) > 1 else None

        # channels
        tags = ev.get("event__tags", {}).get("tags", [])
        channels = []
        for t in tags:
            name = t.get("text") or t.get("channel-text")
            link = t.get("href") or t.get("link")
            if name:
                channels.append({"name": name, "link": link})

        out.append({
            "datetime": dt,
            "home": home,
            "away": away,
            "channels": channels
        })

    return out

def main():
    p = argparse.ArgumentParser(description="Scrape LiveSportsOnTV league schedules")
    p.add_argument("league", help="league slug (e.g. wnba, nfl, nba, mlb, etc.)")
    args = p.parse_args()

    schedule = fetch_league_schedule(args.league)
    print(json.dumps(schedule, indent=2))

if __name__ == "__main__":
    main()
