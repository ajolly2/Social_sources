import requests
from bs4 import BeautifulSoup
import os

def scrape_livesportsontv():
    url = "https://www.livesportsontv.com/"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    html = resp.text

    # Write raw HTML to data/tv_debug.html
    os.makedirs("data", exist_ok=True)
    with open("data/tv_debug.html", "w", encoding="utf-8") as f:
        f.write(html)

    # Return empty for now
    return []
