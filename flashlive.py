import os
import requests
import datetime
import json

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_URL = "https://flashlive-sports.p.rapidapi.com/v1"
LEAGUES = {"MLB": 103, "NBA": 2, "NHL": 4, "WNBA": 22}
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
}

def get_flashlive_games():
    today = datetime.datetime.utcnow().date()
    all_games = []
    debug_payload = {}

    for league_name, league_id in LEAGUES.items():
        url = f"{BASE_URL}/events/list?category_id={league_id}&days=0"
        resp = requests.get(url, headers=HEADERS)
        # capture entire JSON for debug
        payload = resp.json()
        debug_payload[league_name] = payload

        # try both upper- and lower-case
        items = payload.get("DATA") or payload.get("data") or []
        for item in items:
            start_time = item.get("START_TIME") or item.get("start_time")
            home = (item.get("HOME") or item.get("home") or {}).get("NAME") \
                   or (item.get("HOME") or item.get("home") or {}).get("name")
            away = (item.get("AWAY") or item.get("away") or {}).get("NAME") \
                   or (item.get("AWAY") or item.get("away") or {}).get("name")
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

    # write debug payload out so we can inspect what's coming back
    os.makedirs("data", exist_ok=True)
    with open("data/flash_debug.json", "w") as f:
        json.dump(debug_payload, f, indent=2)

    return all_games
