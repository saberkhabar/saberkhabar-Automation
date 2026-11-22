
import os
import requests

TOKEN = os.environ.get("BALE_TOKEN")
ADMIN_ID = 1944602651

if not TOKEN:
    raise ValueError("BALE_TOKEN پیدا نشد.")

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

print("در انتظار دریافت پیام از بله...")

response = requests.get(
    f"{BASE_URL}/getUpdates",
    params={"timeout": 10},
    timeout=20
)

data = response.json()

if not data.get("ok"):
    print("خطا در دریافت پیام:", data)
    raise SystemExit(1)

updates = data.get("result", [])

if not updates:
    print("هنوز پیامی دریافت نشده است.")
else:
    for update in updates:
        message = update.get("message", {})
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        message_text = message.get("text", "")

        if str(chat_id) == str(ADMIN_ID):
            print("پیام مدیر دریافت شد.")

            requests.post(
                f"{BASE_URL}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "پیامت دریافت شد. ✅"
                },
                timeout=20
            )
        else:
            print("پیام از شناسه‌ای غیر از مدیر دریافت شد.")
