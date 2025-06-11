#!/usr/bin/env python3
import datetime
import json
import requests

from flashlive import get_flashlive_games  # <— your scraper module

# ────────────────────────────────────────────────────────────
def fetch_mlb_schedule(date: str):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}"
    r   = requests.get(url); r.raise_for_status()
    data = r.json()

    games = []
    for date_block in data.get("dates", []):
        for g in date_block.get("games", []):
            dt   = g["gameDate"]               # "2025-06-11T17:10:00Z"
            away = g["teams"]["away"]["team"]["name"]
            home = g["teams"]["home"]["team"]["name"]

            channels = [
                {"type": bc["type"], "name": bc["name"], "language": bc["language"]}
                for bc in g.get("broadcasts", [])
            ]

            games.append({
                "datetime": dt,
                "away":     away,
                "home":     home,
                "channels": channels,
            })
    return games

# ────────────────────────────────────────────────────────────
def merge_schedules(mlb_games, flash_games):
    # build a lookup by (datetime, away, home)
    idx = {
        (g["datetime"], g["away"], g["home"]): g["channels"]
        for g in mlb_games
    }

    merged = []
    for fg in flash_games:
        key = (fg["datetime"], fg["away"], fg["home"])
        fg["mlb_channels"] = idx.get(key, [])
        merged.append(fg)

    return merged

# ────────────────────────────────────────────────────────────
def main(date=None):
    date = date or datetime.date.today().isoformat()

    # 1. MLB side
    mlb = fetch_mlb_schedule(date)

    # 2. FlashLive side
    #    get_flashlive_games() yields dicts with:
    #    {
    #      "league","home","away","start_time","score_home","score_away","status","channel"
    #    }
    #    We just need to rename start_time->datetime
    flash_raw = get_flashlive_games()
    flash = []
    for g in flash_raw:
        flash.append({
            "datetime": g["start_time"],
            "away":     g["away"],
            "home":     g["home"],
            "score_home": g["score_home"],
            "score_away": g["score_away"],
            "status":     g["status"],
        })

    # 3. Merge
    merged = merge_schedules(mlb, flash)

    # 4. Dump
    out = f"artifacts/merged_{date}.json"
    with open(out, "w") as f:
        json.dump(merged, f, indent=2)
    print("Wrote", out)

if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv)>1 else None)
