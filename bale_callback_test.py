import os
import requests
import json

TOKEN = os.environ["BALE_TOKEN"]
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

print("در حال بررسی کلیک‌های دریافتی...")

response = requests.get(
    f"{BASE_URL}/getUpdates",
    params={"timeout": 10},
    timeout=20
)

data = response.json()

if not data.get("ok"):
    print("خطا:", data)
    raise SystemExit(1)

updates = data.get("result", [])

for update in updates:
    callback = update.get("callback_query")

    if callback:
        print("کلیک دکمه دریافت شد!")
        print("نوع انتخاب:", callback.get("data"))
    else:
        print("این به‌روزرسانی کلیک دکمه نیست.")

if not updates:
    print("هیچ رویداد جدیدی دریافت نشد.")
