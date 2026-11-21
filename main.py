
import os
import json
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]
DESTINATION = "@saberkhabar"

CHANNELS = [
    "caronline",
    "eco_ehsan",
    "Naya_Press"
]

STATE_FILE = "state.json"

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def send_news(text, source, post_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    message = (
        text[:3800]
        + f"\n\nمنبع: https://t.me/{source}/{post_id}"
    )
    response = requests.post(url, json={
        "chat_id": DESTINATION,
        "text": message,
        "disable_web_page_preview": True
    }, timeout=30)
    response.raise_for_status()
    return response.json().get("ok", False)

def main():
    state = load_state()

    for channel in CHANNELS:
        try:
            url = f"https://t.me/s/{channel}"
            page = requests.get(url, timeout=30)
            page.raise_for_status()

            soup = BeautifulSoup(page.text, "html.parser")
            posts = []

            for item in soup.select(".tgme_widget_message_wrap"):
                widget = item.select_one(".tgme_widget_message")
                if not widget:
                    continue

                post = widget.get("data-post", "")
                if not post:
                    continue

                post_id = int(post.split("/")[-1])
                text_el = item.select_one(".tgme_widget_message_text")

                if text_el:
                    text = text_el.get_text("\n", strip=True)
                    if text:
                        posts.append((post_id, text))

            posts.sort()

            last_id = int(state.get(channel, 0))

            if last_id == 0:
                if posts:
                    state[channel] = posts[-1][0]
                print("Initialised:", channel)
                continue

            for post_id, text in posts:
                if post_id <= last_id:
                    continue

                if send_news(text, channel, post_id):
                    state[channel] = post_id
                    save_state(state)
                    print("Published:", channel, post_id)

        except Exception as error:
            print("Error:", channel, error)

    save_state(state)

if __name__ == "__main__":
    main()
