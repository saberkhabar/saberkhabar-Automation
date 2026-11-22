
import os
import requests

TOKEN = os.environ.get("BALE_TOKEN")
ADMIN_ID = 1944602651

if not TOKEN:
    raise ValueError("BALE_TOKEN در تنظیمات GitHub پیدا نشد.")

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

# بررسی اتصال بازو
response = requests.get(f"{BASE_URL}/getMe", timeout=30)
data = response.json()

if not data.get("ok"):
    print("خطا در اتصال:", data)
    raise SystemExit(1)

print("اتصال به بازو برقرار شد.")

# ارسال پیام آزمایشی به مدیر
response = requests.post(
    f"{BASE_URL}/sendMessage",
    json={
        "chat_id": ADMIN_ID,
        "text": "سلام! بازوی شفت خبر با موفقیت به برنامه متصل شد. ✅"
    },
    timeout=30
)

result = response.json()
print("نتیجه ارسال:", result)
