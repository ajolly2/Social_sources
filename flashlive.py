import requests
import os
from datetime import datetime
from dateutil import tz

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_URL = "https://flashlive-sports.p.rapidapi.com/v1/events/list"

LEAGUE_IDS = {
    "MLB": 144,
    "NBA": 132,
    "NHL": 140,
    "WNBA": 897
}

def fetch_flashlive_games():
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
    }

    games = []

    for league, league_id in LEAGUE_IDS.items():
        params = {"sport_id": 1, "league_id": league_id, "timezone": "-5"}  # EST timezone

        try:
            res = requests.get(BASE_URL, headers=headers, params=params)
            data = res.json().get("DATA", [])
            for item in data:
                home = item["EHOME"]
                away = item["EAWAY"]
                time_utc = item["EST"]
                local_dt = datetime.fromtimestamp(time_utc, tz=tz.gettz("America/New_York"))

                games.append({
                    "sport": "Basketball" if league in ["NBA", "WNBA"] else "Baseball" if league == "MLB" else "Hockey",
                    "league": league,
                    "match
