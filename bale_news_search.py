
import requests
import xml.etree.ElementTree as ET
import re
import html
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

RSS_SOURCES = {
    "خبرگزاری مهر": "https://www.mehrnews.com/rss",
    "ایسنا": "https://www.isna.ir/rss",
    "صداوسیما": "https://www.irib-news.ir/fa/rss/allnews?",
    "باشگاه خبرنگاران جوان": "https://www.yjc.ir/fa/rss/allnews",
    "تابناک": "https://www.tabnak.ir/fa/rss/allnews",
}

BING_QUERIES = [
    '"شهرستان شفت"',
    '"شفت گیلان"',
    '"احمدسرگوراب"',
    '"امامزاده ابراهیم" شفت',
    '"سیاهمزگی"',
    '"چوبر" گیلان',
    '"نصیرمحله" شفت',
    '"جیرده" شفت',
    '"ملاسرا" شفت',
    '"ویسرود" گیلان',
]

LOCAL_TITLE_WORDS = [
    "شهرستان شفت",
    "شفت گیلان",
    "احمدسرگوراب",
    "احمد سرگوراب",
    "امامزاده ابراهیم شفت",
    "چوبر گیلان",
    "سیاهمزگی",
    "نصیرمحله",
    "جیرده شفت",
    "ملاسرا شفت",
    "ویسرود",
    "لاسک شفت",
    "بداب شفت",
    "خرمکش شفت",
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
        if child.tag.split("}")[-1].lower() == name.lower():
            if name == "link":
                return child.attrib.get("href", child.text or "")
            return child.text or ""
    return ""


def get_news_items(root):
    return [
        element for element in root.iter()
        if element.tag.split("}")[-1] in ("item", "entry")
    ]


def is_local_title(title):
    title = normalize_text(title)

    return any(
        normalize_text(word) in title
        for word in LOCAL_TITLE_WORDS
    )


def parse_news_date(date_text):
    if not date_text:
        return None

    try:
        date = parsedate_to_datetime(date_text)

        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        return date.astimezone(timezone.utc)

    except Exception:
        pass

    try:
        date = datetime.fromisoformat(
            date_text.replace("Z", "+00:00")
        )

        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        return date.astimezone(timezone.utc)

    except Exception:
        return None


def get_news_data(item):
    title = normalize_text(
        clean_text(get_child_text(item, "title"))
    )

    description = clean_text(
        get_child_text(item, "description")
        or get_child_text(item, "summary")
        or get_child_text(item, "content")
    )

    link = get_child_text(item, "link")

    date_text = (
        get_child_text(item, "pubDate")
        or get_child_text(item, "published")
        or get_child_text(item, "updated")
    )

    source = get_child_text(item, "source")

    return {
        "title": title,
        "description": description,
        "link": link,
        "date_text": date_text,
        "date": parse_news_date(date_text),
        "source": clean_text(source)
    }


def fetch_rss(name, url):
    print("\n==============================")
    print("منبع:", name)

    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )

        print("وضعیت اتصال:", response.status_code)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        items = get_news_items(root)

        print("تعداد خبرهای دریافتی:", len(items))

        return [get_news_data(item) for item in items]

    except Exception as error:
        print("خطا:", error)
        return []


def search_bing(query):
    try:
        response = requests.get(
            "https://www.bing.com/news/search",
            params={
                "q": query,
                "format": "rss",
                "setlang": "fa"
            },
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )

        print("\nجست‌وجوی Bing:", query)
        print("وضعیت اتصال:", response.status_code)

        response.raise_for_status()

        root = ET.fromstring(response.content)
        items = get_news_items(root)

        print("تعداد نتایج:", len(items))

        return [get_news_data(item) for item in items]

    except Exception as error:
        print("خطا در Bing:", error)
        return []


def search_news():
    recent_news = []
    old_news_count = 0
    missing_date_count = 0

    checked_links = set()
    checked_titles = set()

    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    def process_news(news):
        nonlocal old_news_count, missing_date_count

        title = news["title"].strip()
        link = news["link"].strip()
        date = news["date"]

        if not title:
            return

        if not is_local_title(title):
            return

        if link and link in checked_links:
            return

        if title in checked_titles:
            return

        if link:
            checked_links.add(link)

        checked_titles.add(title)

        if date is None:
            missing_date_count += 1
            return

        if date < seven_days_ago or date > now:
            old_news_count += 1
            return

        recent_news.append(news)

    for name, url in RSS_SOURCES.items():
        news_list = fetch_rss(name, url)

        for news in news_list:
            news["source"] = news["source"] or name
            process_news(news)

        time.sleep(1)

    for query in BING_QUERIES:
        news_list = search_bing(query)

        for news in news_list:
            news["source"] = news["source"] or "Bing News"
            process_news(news)

        time.sleep(1)

    print("\n================================")
    print("گزارش نهایی جست‌وجوی شفت")
    print("================================")

    print("بازه بررسی: ۷ روز اخیر")
    print("خبرهای جدید و مرتبط:", len(recent_news))
    print("خبرهای قدیمی یا خارج از بازه:", old_news_count)
    print("خبرهای بدون تاریخ معتبر:", missing_date_count)

    for index, news in enumerate(recent_news, start=1):
        print("\n------------------------------")
        print("شماره:", index)
        print("عنوان:", news["title"])
        print("منبع:", news["source"])
        print("تاریخ:", news["date_text"])
        print("لینک:", news["link"])


if __name__ == "__main__":
    search_news()
