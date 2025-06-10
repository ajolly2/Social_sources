import os
import requests

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_URL     = "https://flashlive-sports.p.rapidapi.com/v1/events/list"

# Use sport-type IDs from /sports/list
SPORT_IDS = {
    "MLB":   6,  # Baseball
    "BBALL": 3,  # Basketball (NBA + WNBA)
    "NHL":   4   # Hockey
}

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
}

def get_flashlive_games():
    all_games = []

    for league_key, sport_id in SPORT_IDS.items():
        params = {
            "sport_id":   sport_id,
            "locale":     "en_GB",  # valid locale
            "timezone":   0,        # UTC+0
            "indent_days":0         # today
        }
        resp    = requests.get(BASE_URL, headers=HEADERS, params=params)
        payload = resp.json()
        items   = payload.get("DATA") or payload.get("data") or []

        for ev in items:
            # Determine our league label
            if sport_id == 6:
                league = "MLB"
            elif sport_id == 4:
                league = "NHL"
            else:
                # basketball: NBA vs WNBA by tournament name
                tour = (ev.get("TOURNAMENT") or {}).get("NAME","")
                league = "WNBA" if "Women" in tour else "NBA"

            all_games.append({
                "league":     league,
                "home":       (ev.get("HOME") or {}).get("NAME") or (ev.get("home") or {}).get("name"),
                "away":       (ev.get("AWAY") or {}).get("NAME") or (ev.get("away") or {}).get("name"),
                "start_time": ev.get("START_TIME") or ev.get("start_time"),
                "score_home": (ev.get("HOME") or {}).get("SCORE", {}).get("CURRENT", ""),
                "score_away": (ev.get("AWAY") or {}).get("SCORE", {}).get("CURRENT", ""),
                "status":     ev.get("STATE") or ev.get("state"),
                "channel":    None
            })

    return all_games
