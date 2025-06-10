import os
import requests
import datetime

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_URL     = "https://flashlive-sports.p.rapidapi.com/v1/events/list"

# We'll only fetch baseball (sport_id 6)
SPORT_ID = 6

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
}

def get_flashlive_games():
    # Fetch today’s baseball tournaments & events
    params = {
        "sport_id":    SPORT_ID,
        "locale":      "en_GB",
        "timezone":    0,
        "indent_days": 0
    }
    resp    = requests.get(BASE_URL, headers=HEADERS, params=params)
    payload = resp.json()
    tournaments = payload.get("DATA", [])

    games = []

    # Find the USA MLB tournament
    for tour in tournaments:
        if tour.get("SHORT_NAME") == "MLB" and tour.get("COUNTRY_NAME") == "USA":
            for ev in tour.get("EVENTS", []):
                # Timestamp is in seconds UTC
                ts = ev.get("START_UTIME") or ev.get("START_TIME")
                start = datetime.datetime.utcfromtimestamp(ts).isoformat() if ts else None

                games.append({
                    "league":      "MLB",
                    "home":        ev.get("HOME_NAME") or (ev.get("home") or {}).get("name"),
                    "away":        ev.get("AWAY_NAME") or (ev.get("away") or {}).get("name"),
                    "start_time":  start,
                    "score_home":  ev.get("HOME_SCORE_CURRENT", ""),
                    "score_away":  ev.get("AWAY_SCORE_CURRENT", ""),
                    "status":      ev.get("STAGE_TYPE") or ev.get("STAGE"),
                    "channel":     None
                })
            break  # no need to check other tournaments

    return games
