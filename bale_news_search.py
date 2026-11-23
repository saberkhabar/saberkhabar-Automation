
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode

SEARCHES = [
    "شفت",
    "شفت گیلان",
    "شهرستان شفت",
    "احمدسرگوراب",
    "ملاسرا شفت",
    "نصیرمحله شفت",
    "روستاهای شفت"
]

def search_news(query):
    params = {
        "q": query,
        "hl": "fa-IR",
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

        response.raise_for_status()

        root = ET.fromstring(response.content)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []

        print("\nجست‌وجو:", query)
        print("تعداد خبر:", len(items))

        for item in items:
            print("--------------------")
            print("عنوان:", item.findtext("title", ""))
            print("لینک:", item.findtext("link", ""))
            print("تاریخ:", item.findtext("pubDate", ""))

    except Exception as error:
        print("خطا:", error)


if __name__ == "__main__":
    for query in SEARCHES:
        search_news(query)
