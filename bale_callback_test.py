
import os
import requests

TOKEN = os.environ["BALE_TOKEN"]
ADMIN_ID = 1944602651
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

response = requests.get(
    f"{BASE_URL}/getUpdates",
    params={"timeout": 0, "limit": 100},
    timeout=20
)

result = response.json()

if not result.get("ok"):
    print("خطا در دریافت:", result)
    raise SystemExit(1)

updates = result.get("result", [])
print("تعداد رویدادهای دریافت‌شده:", len(updates))

for update in updates:
    callback = update.get("callback_query")

    if not callback:
        print("رویداد عادی، نه کلیک دکمه.")
        continue

    user_id = callback.get("from", {}).get("id")
    data = callback.get("data", "")
    callback_id = callback.get("id")

    if str(user_id) == str(ADMIN_ID):
        if data == "approve:test":
            message = "تأیید آزمایشی دریافت شد."
        elif data == "reject:test":
            message = "رد آزمایشی دریافت شد."
        else:
            message = "کلیک دریافت شد."
    else:
        message = "این دکمه فقط برای مدیر است."

    answer = requests.post(
        f"{BASE_URL}/answerCallbackQuery",
        json={
            "callback_query_id": callback_id,
            "text": message
        },
        timeout=20
    )

    print("نتیجه کلیک:", data)
    print("پاسخ بله:", answer.json())

if updates:
    highest_id = max(item["update_id"] for item in updates)

    confirm = requests.get(
        f"{BASE_URL}/getUpdates",
        params={
            "offset": highest_id + 1,
            "timeout": 0,
            "limit": 1
        },
        timeout=20
    )

    print("تأیید رویدادهای قبلی:", confirm.json())
else:
    print("رویداد جدیدی وجود ندارد.")
