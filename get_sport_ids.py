import os
import requests

KEY  = os.getenv("RAPIDAPI_KEY")
HEAD = {
    "X-RapidAPI-Key": KEY,
    "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
}
URL  = "https://flashlive-sports.p.rapidapi.com/v1/sports/list"

resp = requests.get(URL, headers=HEAD)
print(resp.json())
