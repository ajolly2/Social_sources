import requests
from bs4 import BeautifulSoup
import datetime

def scrape_livesportsontv():
    url = "https://www.livesportsontv.com/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    games = []

    for card in soup.select(".event-card"):
        try:
            sport = card.select_one(".event-sport").get_text(strip=True)
            league = card.select_one(".event-league").get_text(strip=True)
            matchup = card.select_one(".event-title").get_text(strip=True)
            time_str = card.select_one(".event-time").get_text(strip=True)
            channel = card.select_one(".event-channels").get_text(strip=True)

            if " vs " in matchup:
                home, away = matchup.split(" vs ")
            else:
                continue

            start_time = _parse_time(time_str)

            games.append({
                "sport": sport,
                "league": league.upper(),
                "home": home.strip(),
                "away": away.strip(),
                "start_time": start_time,
                "channel": channel.strip()
            })
        except Exception:
            continue

    return games

def _parse_time(time_str):
    today = datetime.datetime.utcnow().date()
    full_str = f"{today} {time_str}"
    dt = datetime.datetime.strptime(full_str, "%Y-%m-%d %I:%M %p")
    return dt.isoformat()
