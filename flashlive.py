import os
import requests
import json

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_URL     = "https://flashlive-sports.p.rapidapi.com/v1/events/list"

SPORT_IDS = {
    "MLB":  6,   # Baseball
    "BBALL":3,   # Basketball (NBA + WNBA)
    "NHL":  4    # Hockey
}

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
}

def get_flashlive_games():
    all_games = []
    debug = {}

    for league_key, sport_id in SPORT_IDS.items():
        params = {"sport_id": sport_id, "days": 0}
        resp   = requests.get(BASE_URL, headers=HEADERS, params=params)

        # capture the full JSON (or text if invalid JSON)
        try:
            body = resp.json()
        except:
            body = resp.text

        debug[league_key] = {
            "status_code": resp.status_code,
            "body": body
        }

        # proceed to parse if JSON
        if isinstance(body, dict):
            items = body.get("DATA") or body.get("data") or []
            for ev in items:
                # league mapping
                if sport_id == 6:
                    league = "MLB"
                elif sport_id == 4:
                    league = "NHL"
                else:
                    name = (ev.get("TOURNAMENT") or {}).get("NAME","")
                    league = "WNBA" if "Women" in name else "NBA"

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

    # write debug dump so we can inspect it
    os.makedirs("data", exist_ok=True)
    with open("data/flash_debug_full.json", "w") as f:
        json.dump(debug, f, indent=2)

    return all_games
