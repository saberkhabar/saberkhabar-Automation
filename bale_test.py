
import os
import requests

TOKEN = os.environ.get("BALE_TOKEN")

if not TOKEN:
    raise ValueError("توکن ربات در GitHub پیدا نشد.")

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

response = requests.post(
    f"{BASE_URL}/sendMessage",
    json={
        "chat_id": "@shaftkhabar",
        "text": "🧪 پیام آزمایشی\n\nاتصال ربات شفت خبر به کانال با موفقیت برقرار شد. ✅"
    },
    timeout=30
)

result = response.json()

if not result.get("ok"):
    print("خطا در ارسال پیام:", result)
    raise SystemExit(1)

print("پیام آزمایشی با موفقیت به کانال ارسال شد.")
