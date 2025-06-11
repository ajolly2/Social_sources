#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import datetime

BASE_URL = "https://www.livesportsontv.com"
LEAGUE_SLUG = "wnba"

def scrape_wnba():
    url = f"{BASE_URL}/league/{LEAGUE_SLUG}"
    resp = requests.get(url)
    resp.raise_for_status()

    # Grab the Next.js __NEXT_DATA__ blob
    soup = BeautifulSoup(resp.text, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script:
        raise RuntimeError("WNBA JSON data not found on page")

    data = json.loads(script.string)
    events = data["props"]["pageProps"].get("events", [])
    out = []

    for ev in events:
        # skip hidden games
        if ev.get("classNames") and "dontshow" in ev["classNames"]:
            continue

        # parse date + time
        time_block = ev.get("event__info", {}).get("time", {})
        date_obj = time_block.get("date")    # e.g. {"b":"11","span":"Jun"}
        time_str = time_block.get("time")    # e.g. "9:00 PM"
        dt = None
        if date_obj and time_str:
            day = int(date_obj["b"])
            mon = date_obj["span"]
            year = datetime.datetime.now().year
            dt = datetime.datetime.strptime(
                f"{day} {mon} {year} {time_str}",
                "%d %b %Y %I:%M %p"
            ).isoformat()

        # parse teams
        match_info = ev.get("event__matchInfo", {}).get("matchInfo", {})
        participants = match_info.get("participant", [])
        home = participants[0].get("text") if len(participants) >= 1 else None
        away = participants[1].get("text") if len(participants) >= 2 else None

        # parse channels
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
    schedule = scrape_wnba()
    print(json.dumps(schedule, indent=2))

if __name__ == "__main__":
    main()
