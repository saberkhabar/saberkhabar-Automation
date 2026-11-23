
import requests
import xml.etree.ElementTree as ET
import re
import html
import time

RSS_SOURCES = {
    "خبرگزاری مهر": "https://www.mehrnews.com/rss",
    "ایسنا": "https://www.isna.ir/rss",
    "صداوسیما": "https://www.irib-news.ir/fa/rss/allnews?",
    "باشگاه خبرنگاران جوان": "https://www.yjc.ir/fa/rss/allnews",
    "تابناک": "https://www.tabnak.ir/fa/rss/allnews",
}

LOCAL_WORDS = [
    "شهرستان شفت",
    "شفت گیلان",
    "شفت",
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
    "علیسرا",
]


def clean_text(text):
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def normalize_text(text):
    text = text.replace("ي", "ی").replace("ك", "ک")
    return " ".join(text.split()).strip()


def get_child_text(element, name):
    for child in element:
        if child.tag.split("}")[-1] == name:
            if name == "link":
                return child.attrib.get("href", child.text or "")
            return child.text or ""
    return ""


def get_news_items(root):
    return [
        element
        for element in root.iter()
        if element.tag.split("}")[-1] in ("item", "entry")
    ]


def is_local_news(title):
    title = normalize_text(title)

    for word in LOCAL_WORDS:
        word = normalize_text(word)

        if word == "شفت":
            # شفت به‌تنهایی فقط وقتی پذیرفته شود
            # که عنوان صریحاً به شهرستان اشاره کند.
            if "شهرستان شفت" in title or "شفت گیلان" in title:
                return True
        elif word in title:
            return True

    return False


def fetch_source(source_name, rss_url):
    print("\n==============================")
    print("منبع:", source_name)

    try:
        response = requests.get(
            rss_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=25
        )

        print("وضعیت اتصال:", response.status_code)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        items = get_news_items(root)

        print("تعداد خبرهای دریافتی:", len(items))

        found = []

        for item in items:
            title = normalize_text(
                clean_text(get_child_text(item, "title"))
            )

            description = clean_text(
                get_child_text(item, "description")
                or get_child_text(item, "summary")
                or get_child_text(item, "content")
            )

            link = get_child_text(item, "link")

            pub_date = (
                get_child_text(item, "pubDate")
                or get_child_text(item, "published")
                or get_child_text(item, "updated")
            )

            if is_local_news(title):
                found.append({
                    "title": title,
                    "description": description,
                    "link": link,
                    "date": pub_date,
                    "source": source_name
                })

        print("خبرهای محلی احتمالی:", len(found))

        return found

    except Exception as error:
        print("خطا در دریافت منبع:", error)
        return []


def search_news():
    all_news = []
    checked_links = set()
    checked_titles = set()

    for source_name, rss_url in RSS_SOURCES.items():
        news_list = fetch_source(source_name, rss_url)

        for news in news_list:
            link = news["link"].strip()
            title = news["title"].strip()

            if link and link in checked_links:
                continue

            if title and title in checked_titles:
                continue

            if link:
                checked_links.add(link)

            if title:
                checked_titles.add(title)

            all_news.append(news)

        time.sleep(1)

    print("\n================================")
    print("نتیجه نهایی جست‌وجو")
    print("================================")
    print("تعداد خبرهای محلی احتمالی:", len(all_news))

    for index, news in enumerate(all_news, start=1):
        print("\n------------------------------")
        print("شماره:", index)
        print("عنوان:", news["title"])
        print("منبع:", news["source"])
        print("تاریخ:", news["date"])
        print("لینک:", news["link"])


if __name__ == "__main__":
    search_news()
