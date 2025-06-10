import os
import requests
import datetime

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_URL    = "https://flashlive-sports.p.rapidapi.com/v1/events/list"

LEAGUES = {
    "MLB": 103,
    "NBA": 2,
    "NHL": 4,
    "WNBA": 22
}

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
}

def get_flashlive_games():
    all_games = []

    for league_name, sport_id in LEAGUES.items():
        # **Use a valid locale code and drop timezone entirely**
        params = {
            "locale":    "en_GB",   # MUST be one of the enum values (e.g. en_GB, en_CA, etc.)
            "sport_id":  sport_id,
            "indent_days": 0        # today’s events
        }
        resp = requests.get(BASE_URL, headers=HEADERS, params=params)
        payload = resp.json()

        items = payload.get("DATA") or payload.get("data") or []
        for item in items:
            start_time = item.get("START_TIME") or item.get("start_time")
            home       = (item.get("HOME") or {}).get("NAME") or (item.get("home") or {}).get("name")
            away       = (item.get("AWAY") or {}).get("NAME") or (item.get("away") or {}).get("name")
            score_home = (item.get("HOME") or {}).get("SCORE", {}).get("CURRENT", "")
            score_away = (item.get("AWAY") or {}).get("SCORE", {}).get("CURRENT", "")
            status     = item.get("STATE") or item.get("state")

            all_games.append({
                "league":      league_name,
                "home":        home,
                "away":        away,
                "start_time":  start_time,
                "score_home":  score_home,
                "score_away":  score_away,
                "status":      status,
                "channel":     None
            })

    return all_games
