import json
from flashlive import get_flashlive_games
from livesports_scraper import scrape_livesportsontv

def normalize(name):
    return name.lower().replace(" ", "").replace(".", "")

def match_games(flash_games, tv_listings):
    matched = []

    for game in flash_games:
        for listing in tv_listings:
            if (
                normalize(game["home"]) in normalize(listing["home"]) and
                normalize(game["away"]) in normalize(listing["away"]) and
                game["league"] == listing["league"] and
                game["start_time"][:16] == listing["start_time"][:16]
            ):
                game["channel"] = listing["channel"]
                break
        matched.append(game)

    return matched

def main():
    flash_games = get_flashlive_games()
    tv_listings = scrape_livesportsontv()
    combined = match_games(flash_games, tv_listings)

    with open("data/games.json", "w") as f:
        json.dump(combined, f, indent=2)

if __name__ == "__main__":
    main()
