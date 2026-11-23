
import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw

TOKEN = os.environ.get("BALE_TOKEN")

if not TOKEN:
    raise ValueError("BALE_TOKEN پیدا نشد.")

# ساخت تصویر آزمایشی
image = Image.new("RGB", (1000, 500), "white")
draw = ImageDraw.Draw(image)

draw.rectangle((20, 20, 980, 480), outline="black", width=5)
draw.text((300, 220), "SHAFT KHABAR - PHOTO TEST", fill="black")

buffer = BytesIO()
image.save(buffer, format="PNG")
buffer.seek(0)

# ارسال تصویر به کانال
url = f"https://tapi.bale.ai/bot{TOKEN}/sendPhoto"

response = requests.post(
    url,
    data={
        "chat_id": "@shaftkhabar",
        "caption": "🧪 آزمایش ارسال تصویر\nاین پیام خبر واقعی نیست."
    },
    files={
        "photo": ("test.png", buffer, "image/png")
    },
    timeout=60
)

result = response.json()

if not result.get("ok"):
    print("خطا:", result)
    raise SystemExit(1)

print("تصویر آزمایشی با موفقیت ارسال شد.")
