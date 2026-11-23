
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode

SEARCHES = [
    "اخبار شهرستان شفت",
    "شفت گیلان خبر",
    "فرمانداری شهرستان شفت",
    "حوادث شفت گیلان",
    "روستاهای شهرستان شفت",
    "اخبار احمدسرگوراب",
    "اخبار بخش مرکزی شفت"
]

def search_news(query):
    params = {
        "q": query,
        "hl": "fa",
        "gl": "IR",
        "ceid": "IR:fa"
    }

    url = "https://news.google.com/rss/search?" + urlencode(params)

    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30
        )

        print("وضعیت اتصال:", response.status_code)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        items = root.findall(".//item")

        print("تعداد خبرهای پیدا شده:", len(items))

        for item in items:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            date = item.findtext("pubDate", "")
            source = item.find("source")

            source_name = source.text if source is not None else "نامشخص"

            print("--------------------")
            print("عنوان:", title)
            print("منبع:", source_name)
            print("تاریخ:", date)
            print("لینک:", link)

    except Exception as error:
        print("خطا:", error)


if __name__ == "__main__":
    for query in SEARCHES:
        print("\nجست‌وجوی:", query)
        search_news(query)
