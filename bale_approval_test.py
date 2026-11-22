
import os
import requests

TOKEN = os.environ["BALE_TOKEN"]
ADMIN_ID = 1944602651

url = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"

payload = {
    "chat_id": ADMIN_ID,
    "text": "📰 خبر آزمایشی شفت خبر\n\nاین فقط یک آزمایش است. آیا دکمه‌ها نمایش داده می‌شوند؟",
    "reply_markup": {
        "inline_keyboard": [
            [
                {
                    "text": "✅ تأیید آزمایشی",
                    "callback_data": "approve:test"
                },
                {
                    "text": "❌ رد آزمایشی",
                    "callback_data": "reject:test"
                }
            ]
        ]
    }
}

response = requests.post(url, json=payload, timeout=30)
print(response.json())
