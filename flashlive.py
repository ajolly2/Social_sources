import os
import requests
import json

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_URL     = "https://flashlive-sports.p.rapidapi.com/v1/events/list"

# Only MLB for now (to reduce noise)
SPORT_IDS = {
    "MLB": 6  # Baseball
}

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
}

def get_flashlive_games():
    """
    Debug version: fetches the raw MLB payload and writes it to data/flash_mlb_payload.json
    for inspection of the exact field names returned by the API.
    """
    # Ensure output directory exists
    os.makedirs("data", exist_ok=True)

    for league_key, sport_id in SPORT_IDS.items():
        params = {
            "sport_id":    sport_id,
            "locale":      "en_GB",   # valid locale
            "timezone":    0,         # UTC+0
            "indent_days": 0          # today
        }
        resp = requests.get(BASE_URL, headers=HEADERS, params=params)
        try:
            payload = resp.json()
        except ValueError:
            payload = {"error": "Invalid JSON", "raw_text": resp.text}

        # Write full payload for debugging
        debug_path = os.path.join("data", "flash_mlb_payload.json")
        with open(debug_path, "w") as f:
            json.dump(payload, f, indent=2)

        # We only need one debug file, so break after MLB
        break

    # Return empty list to avoid further parsing errors
    return []
