import os
import time
from typing import List, Dict, Set

import requests
from bs4 import BeautifulSoup

URL = "https://www.sahibinden.com/audi-a4/istanbul-sariyer"
SENT_URLS_FILE = "sent_urls.txt"

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")

def load_sent_urls() -> Set[str]:
    if not os.path.exists(SENT_URLS_FILE):
        return set()
    with open(SENT_URLS_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def save_sent_url(url: str) -> None:
    with open(SENT_URLS_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def fetch_listings() -> List[Dict[str, str]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(URL, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    listings = []
    rows = soup.select("#searchResultsTable tbody tr")
    for row in rows:
        if len(listings) >= 10:
            break
        link_tag = row.select_one("td.searchResultsTitleValue a")
        title_tag = row.select_one("td.searchResultsTagAttributeValue a")
        price_tag = row.select_one("td.searchResultsPriceValue")
        if not link_tag or not title_tag or not price_tag:
            continue
        link = link_tag.get("href")
        if not link.startswith("http"):
            link = "https://www.sahibinden.com" + link
        listings.append({
            "title": title_tag.get_text(strip=True),
            "price": price_tag.get_text(strip=True),
            "link": link,
        })
    return listings

def send_telegram(message: str) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    requests.post(url, data=data, timeout=10)

def run_once() -> None:
    sent_urls = load_sent_urls()
    listings = fetch_listings()
    for listing in listings:
        if listing["link"] in sent_urls:
            continue
        message = (
            f"<b>{listing['title']}</b>\n"
            f"Price: {listing['price']}\n"
            f"<a href='{listing['link']}'>{listing['link']}</a>"
        )
        send_telegram(message)
        save_sent_url(listing["link"])
        sent_urls.add(listing["link"])

if __name__ == "__main__":
    while True:
        try:
            run_once()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(600)
