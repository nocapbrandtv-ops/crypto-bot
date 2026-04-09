import os
import time
import requests
import feedparser
import threading
import websocket
import json
from datetime import datetime
from collections import deque

# ============================================================
# ENV VARIABLES (FROM RAILWAY - NOT GITHUB)
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
NEWS_THREAD_ID = int(os.getenv("NEWS_THREAD_ID", "0"))

CHECK_INTERVAL = 300

# ============================================================
# STORAGE
# ============================================================

liquidation_events = deque()
lock = threading.Lock()

# ============================================================
# TELEGRAM MESSAGE
# ============================================================

def send_message(text):
    if not BOT_TOKEN:
        print("Missing BOT_TOKEN")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "message_thread_id": NEWS_THREAD_ID
    }

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# ============================================================
# PRICE DATA
# ============================================================

def get_prices():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": "bitcoin,ethereum,solana",
                "vs_currencies": "usd",
                "include_1hr_change": "true"
            },
            timeout=10
        )
        return r.json()
    except:
        return {}

# ============================================================
# PRICE ALERTS
# ============================================================

def check_moves(prices, sent):
    for coin, data in prices.items():
        change = data.get("usd_1h_change", 0) or 0
        price = data.get("usd", 0)

        if abs(change) < 5:
            continue

        key = f"{coin}_{round(change)}"
        if key in sent:
            continue

        direction = "📈" if change > 0 else "📉"

        send_message(
            f"{direction} <b>{coin.upper()} {change:+.1f}% (1H)</b>\n"
            f"Price: ${price:,.2f}\n"
            f"<i>{datetime.utcnow()} UTC</i>"
        )

        sent.add(key)

# ============================================================
# NEWS
# ============================================================

FEEDS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/"
]

def check_news(sent):
    for feed in FEEDS:
        try:
            data = feedparser.parse(feed)

            for item in data.entries[:5]:
                link = item.get("link")

                if link in sent:
                    continue

                send_message(
                    f"📰 <b>NEWS</b>\n\n{item.get('title')}\n\n{link}"
                )

                sent.add(link)

        except:
            pass

# ============================================================
# MAIN LOOP
# ============================================================

def start():
    send_message("🤖 CryptoDLY Bot ONLINE")

    sent = set()

    while True:
        try:
            prices = get_prices()

            check_moves(prices, sent)
            check_news(sent)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Error:", e)
            time.sleep(30)


if __name__ == "__main__":
    start()
