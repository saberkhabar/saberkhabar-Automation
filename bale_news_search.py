
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode

SEARCHES = [
    "شفت گیلان خبر",
    "اخبار شهرستان شفت",
    "فرمانداری شهرستان شفت",
    "حوادث شفت گیلان",
    "روستاهای شهرستان شفت",
    "اخبار بخش مرکزی شفت",
    "اخبار احمدسرگوراب"
]
    
def search_news(query):
    url = "https://news.google.com/rss/search?"
    params = {
        "q": query,
        "hl": "fa",
        "gl": "IR",
        "ceid": "IR:fa"
    }

    try:
        response = requests.get(
            url + urlencode(params),
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

       print("وضعیت پاسخ:", response.status_code)
print("آدرس پاسخ:", response.url)
print("نوع پاسخ:", response.headers.get("Content-Type"))
print("ابتدای محتوای دریافتی:")
print(response.text[:500])

root = ET.fromstring(response.content)
print("نوع سند:", root.tag)

items = root.findall(".//item") 
        print("تعداد خبرهای پیدا شده:", len(items))

        for item in items:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            date = item.findtext("pubDate", "")

            source = item.find("source")
            source_name = source.text if source is not None else "نامشخص"

            print("-" * 45)
            print("عنوان:", title)
            print("منبع:", source_name)
            print("تاریخ:", date)
            print("لینک:", link)

    except Exception as error:
        print("خطا در جست‌وجو:", error)


if __name__ == "__main__":
    for query in SEARCHES:
        print("\nجست‌وجوی:", query)
        search_news(query)
