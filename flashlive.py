import os
import requests

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_URL     = "https://flashlive-sports.p.rapidapi.com/v1/events/list"

# ← Replace these with the IDs you got from /sports/list
SPORT_IDS = {
    "MLB":  <your_mlb_id>,
    "NBA":  <your_nba_id>,
    "NHL":  <your_nhl_id>,
    "WNBA": <your_wnba_id>
}

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
}

def get_flashlive_games():
    all_games = []

    for league, sid in SPORT_IDS.items():
        params = {
            "sport_id": sid,
            "days":     0       # today
        }
        resp    = requests.get(BASE_URL, headers=HEADERS, params=params)
        payload = resp.json()

        items = payload.get("DATA") or payload.get("data") or []
        for ev in items:
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
