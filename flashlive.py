import os
import requests
import json
import datetime

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_URL = "https://flashlive-sports.p.rapidapi.com/v1/events/list"
LEAGUES = {"MLB": 103, "NBA": 2, "NHL": 4, "WNBA": 22}
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
}

def get_flashlive_games():
    all_games = []
    debug = {}

    for league_name, sport_id in LEAGUES.items():
        params = {
            "locale": "en-US",
            "sport_id": sport_id,
            "timezone": "America/New_York",
            "indent_days": 0
        }
        resp = requests.get(BASE_URL, headers=HEADERS, params=params)
        debug[league_name] = {
            "status_code": resp.status_code,
            "body": resp.text[:1000]   # first 1k chars
        }

        # try to parse JSON
        try:
            payload = resp.json()
        except Exception as e:
            payload = {"error": str(e)}

        items = payload.get("DATA") or payload.get("data") or []
        for item in items:
            start_time = item.get("START_TIME") or item.get("start_time")
            home = (item.get("HOME") or {}).get("NAME") or (item.get("home") or {}).get("name")
            away = (item.get("AWAY") or {}).get("NAME") or (item.get("away") or {}).get("name")
            score_home = (item.get("HOME") or {}).get("SCORE", {}).get("CURRENT", "")
            score_away = (item.get("AWAY") or {}).get("SCORE", {}).get("CURRENT", "")
            status = item.get("STATE") or item.get("state")

            all_games.append({
                "league": league_name,
                "home": home,
                "away": away,
                "start_time": start_time,
                "score_home": score_home,
                "score_away": score_away,
                "status": status,
                "channel": None
            })

    # write debug payload
    os.makedirs("data", exist_ok=True)
    with open("data/flash_debug.json", "w") as f:
        json.dump(debug, f, indent=2)

    return all_games
