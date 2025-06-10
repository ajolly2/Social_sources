import os
import requests
import datetime

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_URL = "https://flashlive-sports.p.rapidapi.com/v1"

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
    today = datetime.datetime.utcnow().date()
    # days=0 means “today”
    all_games = []

    for league_name, league_id in LEAGUES.items():
        url = (
            f"{BASE_URL}/events/list"
            f"?category_id={league_id}"
            f"&days=0"
        )
        resp = requests.get(url, headers=HEADERS)
        payload = resp.json()

        # Try both uppercase DATA or lowercase data
        items = payload.get("DATA") or payload.get("data") or []
        for item in items:
            # adapt to whichever field names you get back
            start_time = item.get("START_TIME") or item.get("start_time")
            home = item.get("HOME", {}).get("NAME") or item.get("home", {}).get("name")
            away = item.get("AWAY", {}).get("NAME") or item.get("away", {}).get("name")
            score_home = item.get("HOME", {}).get("SCORE", {}).get("CURRENT", "")
            score_away = item.get("AWAY", {}).get("SCORE", {}).get("CURRENT", "")
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

    return all_games
