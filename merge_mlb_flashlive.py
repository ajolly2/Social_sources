#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import requests
from flashlive import get_flashlive_games  # your existing flashlive.py

def fetch_mlb_schedule(date_str):
    """
    Pull MLB schedule for a given date from the official MLB Stats API.
    Returns a list of games with team names, start times, and broadcast channels.
    """
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    games = []
    for day in data.get("dates", []):
        for g in day.get("games", []):
            pk = g["gamePk"]
            home = g["teams"]["home"]["team"]["name"]
            away = g["teams"]["away"]["team"]["name"]
            start = g["gameDate"]  # ISO8601 UTC
            # extract channel list if present
            epg = g.get("content", {}).get("media", {}).get("epg", [])
            channels = [ item.get("callLetters") or item.get("name") for item in epg ]
            games.append({
                "gamePk": pk,
                "home": home,
                "away": away,
                "start_time": start,
                "mlb_channels": channels,
            })
    return games


def merge_schedules(mlb_games, flash_games, date_str):
    """
    Merge two lists of games by matching home/away+start_time within 5 minutes,
    and inject flashlive channel into mlb entry under 'flashlive_channels'.
    """
    out = []
    # index flashlive by a simple key
    def key(g): 
        # round start to minute
        dt = datetime.datetime.fromisoformat(g["start_time"].replace("Z", "+00:00"))
        return (g["home"], g["away"], dt.replace(second=0, microsecond=0))
    flash_index = { key(g): g for g in flash_games }

    for m in mlb_games:
        dt = datetime.datetime.fromisoformat(m["start_time"].replace("Z", "+00:00"))
        k = (m["home"], m["away"], dt.replace(second=0, microsecond=0))
        match = flash_index.get(k)
        merged = dict(m)
        merged["flashlive_channels"] = match.get("channel") if match else None
        out.append(merged)

    # write out
    fname = f"mlb_flashlive_merged.json"
    with open(fname, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {len(out)} games to {fname} for {date_str}")
    return fname


def main():
    p = argparse.ArgumentParser(description="Merge MLB API + FlashLive channel schedules")
    p.add_argument(
      "--date",
      help="Date to fetch in YYYY-MM-DD format (defaults to today UTC)."
    )
    args = p.parse_args()
    if args.date:
        date_str = args.date
    else:
        date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    print(f"Fetching MLB schedule for {date_str}")
    mlb = fetch_mlb_schedule(date_str)

    print("Fetching FlashLive games")
    fl = get_flashlive_games()

    merge_schedules(mlb, fl, date_str)


if __name__ == "__main__":
    main()
