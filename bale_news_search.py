
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlencode

SEARCHES = [
    "اخبار شهرستان شفت",
    "شفت گیلان خبر"
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
        print("نوع محتوا:", response.headers.get("Content-Type"))

        response.raise_for_status()

        print("ابتدای پاسخ دریافتی:")
        print(response.text[:700])

        root = ET.fromstring(response.content)

        print("نوع سند:", root.tag)

        items = root.findall(".//item")
        print("تعداد خبرها:", len(items))

        for item in items:
            print("عنوان:", item.findtext("title", ""))
            print("لینک:", item.findtext("link", ""))

    except Exception as error:
        print("خطا:", error)


if __name__ == "__main__":
    for query in SEARCHES:
        print("\nجست‌وجوی:", query)
        search_news(query)
