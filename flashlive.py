import os
import requests

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_URL     = "https://flashlive-sports.p.rapidapi.com/v1/events/list"

# Use the sport-type IDs from /sports/list
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

    for league_key, sport_id in SPORT_IDS.items():
        params = {"sport_id": sport_id, "days": 0}
        resp   = requests.get(BASE_URL, headers=HEADERS, params=params)
        payload = resp.json()
        items   = payload.get("DATA") or payload.get("data") or []

        for ev in items:
            # Identify league from the payload
            # FlashLive typically includes a tournament or league field:
            league_name = ev.get("TOURNAMENT", {}).get("NAME") or ev.get("tournament", {}).get("name", "")
            # Normalize to our keys:
            if sport_id == 6:
                league = "MLB"
            elif sport_id == 4:
                league = "NHL"
            else:
                # basketball: decide NBA vs WNBA by league_name containing "Women's"
                league = "WNBA" if "Women" in league_name else "NBA"

            home       = (ev.get("HOME") or {}).get("NAME") or (ev.get("home") or {}).get("name")
            away       = (ev.get("AWAY") or {}).get("NAME") or (ev.get("away") or {}).get("name")
            start_time = ev.get("START_TIME") or ev.get("start_time")
            score_home = (ev.get("HOME") or {}).get("SCORE", {}).get("CURRENT", "")
            score_away = (ev.get("AWAY") or {}).get("SCORE", {}).get("CURRENT", "")
            status     = ev.get("STATE") or ev.get("state")

            all_games.append({
                "league":     league,
                "home":       home,
                "away":       away,
                "start_time": start_time,
                "score_home": score_home,
                "score_away": score_away,
                "status":     status,
                "channel":    None
            })

    return all_games
