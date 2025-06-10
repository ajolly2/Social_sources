import os
import json

from flashlive import get_flashlive_games
from livesports_scraper import scrape_livesportsontv

def normalize(name: str) -> str:
    """Normalize team names for matching."""
    return name.lower().replace(" ", "").replace(".", "")

def match_games(flash_games: list, tv_listings: list) -> list:
    """
    For each game from FlashLive, look for a matching listing
    from livesportsontv by league, teams, and start time.
    If found, apply the channel info.
    """
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
    # 1. Fetch games & scores from FlashLive API
    flash_games = get_flashlive_games()

    # 2. Scrape channel listings from livesportsontv.com
    tv_listings = scrape_livesportsontv()

    # 3. Match & merge channel info into the FlashLive data
    combined = match_games(flash_games, tv_listings)

    # 4. Ensure output directory exists
    os.makedirs("data", exist_ok=True)

    # 5. Write the merged data to JSON
    output_path = os.path.join("data", "games.json")
    with open(output_path, "w") as f:
        json.dump(combined, f, indent=2)

if __name__ == "__main__":
    main()
