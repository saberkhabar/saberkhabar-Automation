
import os
import json
import hashlib
import requests

from bale_news_search import search_news

TOKEN = os.environ.get("BALE_TOKEN")
CHANNEL = "@shaftkhabar"
STATE_FILE = "sent_news.json"

if not TOKEN:
    raise ValueError("BALE_TOKEN پیدا نشد.")

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"


def get_news_id(news):
    link = (news.get("link") or "").strip()

    if link:
        raw = link
    else:
        raw = (
            (news.get("title") or "").strip()
            + "|"
            + (news.get("date_text") or "").strip()
        )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


def load_state():
    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(ids):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(ids[-3000:], f, ensure_ascii=False, indent=2)


def send_news(news):
    title = news.get("title", "خبر محلی شفت")

    title = title.replace(
        "یادواره شهدای خانگی",
        "یادواره خانگی شهدا"
    )

    description = news.get("description", "")
    image_url = news.get("image_url", "")

    caption = (
    f"📰 {title}\n\n"
    f"{description}\n\n"
    "📢 <b>اخبار شفت را دنبال کنید:</b>\n"
    '<a href="https://ble.ir/shaftkhabar">'
    "https://ble.ir/shaftkhabar</a>"
)

caption = caption[:1000]

    if image_url.startswith(("https://", "http://")):
        try:
            img = requests.get(image_url, timeout=30)
            img.raise_for_status()

            content_type = img.headers.get(
                "Content-Type", ""
            ).split(";")[0].lower()

            if not content_type.startswith("image/"):
                raise ValueError("فایل تصویر معتبر نیست.")

            if not img.content or len(img.content) > 8 * 1024 * 1024:
                raise ValueError("حجم یا محتوای تصویر معتبر نیست.")

            response = requests.post(
                f"{BASE_URL}/sendPhoto",
                data={
                    "chat_id": CHANNEL,
                    "caption": caption
                },
                files={
                    "photo": (
                        "news-image",
                        img.content,
                        content_type
                    )
                },
                timeout=60
            )

        except Exception as error:
            print("تصویر ارسال نشد:", error)

            response = requests.post(
                f"{BASE_URL}/sendMessage",
                json={
                    "chat_id": CHANNEL,
                    "text": caption
                },
                timeout=30
            )

    else:
        response = requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": CHANNEL,
                "text": caption
            },
            timeout=30
        )

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(f"خطا در ارسال به بله: {result}")

    print("خبر ارسال شد:", title)


def main():
    print("در حال دریافت خبرها...")

    news_list = search_news()

    if not news_list:
        print("خبری پیدا نشد.")
        return

    state = load_state()

    # اجرای اول: خبرهای فعلی فقط ثبت می‌شوند
    # تا خبرهای قدیمی دوباره منتشر نشوند.
    if state is None:
        initial_ids = [
            get_news_id(news)
            for news in news_list
        ]

        save_state(initial_ids)

        print("فهرست اولیه خبرها ثبت شد.")
        print("در این اجرای اول هیچ خبری منتشر نمی‌شود.")
        return

    sent_ids = set(state)

    # فقط خبرهای جدید انتخاب می‌شوند.
    for news in news_list:
        news_id = get_news_id(news)

        if news_id in sent_ids:
            continue

        # فقط یک خبر در هر اجرا
        send_news(news)

        state.append(news_id)
        save_state(state)

        print("ارسال آزمایشی یک خبر جدید تمام شد.")
        return

    print("خبر جدیدی برای انتشار وجود ندارد.")


if __name__ == "__main__":
    main()
