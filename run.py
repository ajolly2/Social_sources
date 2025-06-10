import os
import json

from flashlive import get_flashlive_games
from livesports_scraper import scrape_livesportsontv

def normalize(name: str) -> str:
    return name.lower().replace(" ", "").replace(".", "")

def match_games(flash_games: list, tv_listings: list) -> list:
    matched = []
    for game in flash_games:
        for listing in tv_listings:
            if (
                normalize(game["home"]) in normalize(listing["home"])
                and normalize(game["away"]) in normalize(listing["away"])
                and game["league"] == listing["league"]
                and game["start_time"][:16] == listing["start_time"][:16]
            ):
                game["channel"] = listing["channel"]
                break
        matched.append(game)
    return matched

def main():
    flash_games = get_flashlive_games()
    tv_listings = scrape_livesportsontv()

    # debug prints
    print(f"🐙 FlashLive returned {len(flash_games)} games")
    print(f"📺 TV scraper returned {len(tv_listings)} listings")

    # dump raw for inspection
    os.makedirs("data", exist_ok=True)
    with open("data/raw_flash.json", "w") as f:
        json.dump(flash_games, f, indent=2)
    with open("data/raw_tv.json", "w") as f:
        json.dump(tv_listings, f, indent=2)

    combined = match_games(flash_games, tv_listings)
    print(f"🔗 Matched {sum(1 for g in combined if g.get('channel'))} channels applied")

    # write the final output
    with open("data/games.json", "w") as f:
        json.dump(combined, f, indent=2)

if __name__ == "__main__":
    main()
