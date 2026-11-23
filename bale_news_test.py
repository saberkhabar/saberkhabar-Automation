
import os
import requests
from bale_news_search import search_news

TOKEN = os.environ.get("BALE_TOKEN")
CHANNEL = "@shaftkhabar"

if not TOKEN:
    raise ValueError("BALE_TOKEN پیدا نشد.")

print("در حال جست‌وجوی خبرهای محلی...")

news_list = search_news()

if not news_list:
    print("هیچ خبر معتبری برای ارسال پیدا نشد.")
    raise SystemExit(0)

# فقط یک خبر انتخاب می‌شود
news = news_list[0]

title = news.get("title", "خبر محلی شفت")
description = news.get("description", "")
image_url = news.get("image_url", "")

caption = f"📰 {title}\n\n{description}"
caption = caption[:1000]

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

print("خبر انتخاب شد:", title)

# اگر خبر تصویر داشته باشد
if image_url.startswith(("https://", "http://")):

    try:
        image_response = requests.get(
            image_url,
            timeout=30
        )

        image_response.raise_for_status()

        content_type = image_response.headers.get(
            "Content-Type", ""
        ).split(";")[0].lower()

        image_bytes = image_response.content

        if not content_type.startswith("image/"):
            raise ValueError("فایل دریافت‌شده تصویر نیست.")

        if not image_bytes:
            raise ValueError("تصویر خالی است.")

        if len(image_bytes) > 8 * 1024 * 1024:
            raise ValueError("حجم تصویر بیش از حد مجاز است.")

        response = requests.post(
            f"{BASE_URL}/sendPhoto",
            data={
                "chat_id": CHANNEL,
                "caption": caption
            },
            files={
                "photo": (
                    "news-image",
                    image_bytes,
                    content_type
                )
            },
            timeout=60
        )

    except Exception as error:

        print("ارسال تصویر ممکن نشد:", error)
        print("ارسال متن خبر به‌تنهایی انجام می‌شود.")

        response = requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": CHANNEL,
                "text": caption
            },
            timeout=30
        )

else:

    print("این خبر تصویر ندارد؛ فقط متن ارسال می‌شود.")

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
    print("خطا در ارسال:", result)
    raise SystemExit(1)

print("یک خبر آزمایشی با موفقیت ارسال شد.")
