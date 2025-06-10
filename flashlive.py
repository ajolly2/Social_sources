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
    formatted_date = today.strftime("%Y-%m-%d")
    all_games = []

    for league_name, league_id in LEAGUES.items():
        url = f"{BASE_URL}/events/list?category_id={league_id}&timezone=America/New_York"
        response = requests.get(url, headers=HEADERS)
        data = response.json()

        for item in data.get("DATA", []):
            start_time = item.get("START_TIME")
            home = item.get("HOME", {}).get("NAME")
            away = item.get("AWAY", {}).get("NAME")
            score_home = item.get("HOME", {}).get("SCORE", {}).get("CURRENT", "")
            score_away = item.get("AWAY", {}).get("SCORE", {}).get("CURRENT", "")
            status = item.get("STATE")

            all_games.append({
                "league": league_name,
                "home": home,
                "away": away,
                "start_time": start_time,
                "score_home": score_home,
                "score_away": score_away,
                "status": status,
                "channel": None  # Placeholder to be filled later
            })

    return all_games
