
import requests
import xml.etree.ElementTree as ET
import re
import html

RSS_URL = "https://www.mehrnews.com/rss"

LOCAL_WORDS = [
    "شهرستان شفت",
    "شفت گیلان",
    "فرماندار شفت",
    "شفت-",
    "احمدسرگوراب",
    "احمد سرگوراب",
    "امامزاده ابراهیم",
    "چوبر",
    "ملاسرا",
    "نصیرمحله",
    "جیرده",
    "سیاهمزگی",
    "ویسرود",
    "لاسک",
    "بداب",
    "خرمکش",
    "علیسرا"
]

def clean_text(text):
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())

def search_news():
    try:
        response = requests.get(
            RSS_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30
        )

        print("وضعیت اتصال:", response.status_code)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        items = root.findall(".//item")

        print("تعداد کل خبرهای دریافتی:", len(items))
for item in items:
    print(clean_text(item.findtext("title", "")))
        
        found = []

        for item in items:
            title = clean_text(item.findtext("title", ""))
            description = clean_text(
                item.findtext("description", "")
            )
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")

            combined = title + " " + description

            if any(word in combined for word in LOCAL_WORDS):
                found.append({
                    "title": title,
                    "link": link,
                    "date": pub_date
                })

        print("تعداد خبرهای مرتبط احتمالی با شفت:", len(found))

        for news in found:
            print("\n-------------------------")
            print("عنوان:", news["title"])
            print("منبع: خبرگزاری مهر")
            print("تاریخ:", news["date"])
            print("لینک:", news["link"])

    except Exception as error:
        print("خطا در دریافت خبر:", error)

if __name__ == "__main__":
    search_news()
