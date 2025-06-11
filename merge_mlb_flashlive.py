#!/usr/bin/env python3
import argparse
import datetime
import json
import requests

from flashlive import get_flashlive_games  # your existing flashlive.py must define this

MLB_BASE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"

def fetch_mlb_schedule(date=None):
    """
    Fetch MLB’s schedule JSON for the given YYYY-MM-DD date.
    """
    url = MLB_BASE_URL
    if date:
        url += f"&date={date}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    games = []
    for date_block in data.get("dates", []):
        for game in date_block.get("games", []):
            games.append({
                "gamePk":     game.get("gamePk"),
                "home":       game["teams"]["home"]["team"]["name"],
                "away":       game["teams"]["away"]["team"]["name"],
                "start_time": game.get("gameDate"),
                "status":     game["status"]["detailedState"],
                "channels":   []  # will fill from flashlive
            })
    return {"date": date, "games": games}

def merge(mlb, flash):
    """
    For each MLB game, look for a matching flashlive game
    by home/away names + same hour/minute start, and copy channels.
    """
    out = []
    for m in mlb["games"]:
        match = next((
            f for f in flash
            if f["home"] == m["home"]
            and f["away"] == m["away"]
            and m["start_time"][:16] == f["start_time"][:16]
        ), None)

        if match:
            m["channels"] = match.get("channels", [])
        out.append(m)
    return out

def main():
    p = argparse.ArgumentParser(
        description="Merge MLB schedule from statsapi with channel info from FlashLive"
    )
    p.add_argument(
        "--date",
        help="YYYY-MM-DD (defaults to today UTC)",
        default=None
    )
    args = p.parse_args()

    # default to today if no --date passed
    date = args.date or datetime.datetime.utcnow().strftime("%Y-%m-%d")

    mlb_schedule = fetch_mlb_schedule(date)
    flash_games  = get_flashlive_games()        # from flashlive.py
    merged       = merge(mlb_schedule, flash_games)

    output = {
        "date":  date,
        "games": merged
    }

    with open("mlb_flashlive_merged.json", "w") as fp:
        json.dump(output, fp, indent=2)

    print(f"Wrote {len(merged)} games to mlb_flashlive_merged.json for {date}")

if __name__ == "__main__":
    main()
