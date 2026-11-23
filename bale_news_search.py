
import requests
import xml.etree.ElementTree as ET
import re
import html
import time
from urllib.parse import urlparse, parse_qs, urlencode

# پنج منبع خبری عمومی
RSS_SOURCES = {
    "خبرگزاری مهر": "https://www.mehrnews.com/rss",
    "ایسنا": "https://www.isna.ir/rss",
    "صداوسیما": "https://www.irib-news.ir/fa/rss/allnews?",
    "باشگاه خبرنگاران جوان": "https://www.yjc.ir/fa/rss/allnews",
    "تابناک": "https://www.tabnak.ir/fa/rss/allnews",
}

# جست‌وجوهای اختصاصی اخبار شفت
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

# عبارت‌هایی که در عنوان خبر نشانه قوی‌تری از محلی بودن هستند
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

# عبارت‌هایی برای شناسایی خبرهای احتمالی در توضیحات
LOCAL_DESCRIPTION_WORDS = LOCAL_TITLE_WORDS + [
    "شهرستان شفت",
    "شفت گیلان",
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


def extract_real_link(link):
    if not link:
        return ""

    try:
        parsed = urlparse(link)
        params = parse_qs(parsed.query)

        # باز کردن لینک واسطه‌ای Bing
        if "url" in params:
            return params["url"][0]

    except Exception:
        pass

    return link


def is_local_title(title):
    title = normalize_text(title)

    return any(
        normalize_text(word) in title
        for word in LOCAL_TITLE_WORDS
    )


def is_local_description(description):
    description = normalize_text(description)

    return any(
        normalize_text(word) in description
        for word in LOCAL_DESCRIPTION_WORDS
    )


def get_news_data(item):
    title = normalize_text(
        clean_text(get_child_text(item, "title"))
    )

    description = clean_text(
        get_child_text(item, "description")
        or get_child_text(item, "summary")
        or get_child_text(item, "encoded")
        or get_child_text(item, "content")
    )

    link = extract_real_link(
        get_child_text(item, "link")
    )

    date = (
        get_child_text(item, "pubDate")
        or get_child_text(item, "published")
        or get_child_text(item, "updated")
    )

    source = (
        get_child_text(item, "source")
        or get_child_text(item, "Source")
    )

    return {
        "title": title,
        "description": description,
        "link": link,
        "date": date,
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
    url = "https://www.bing.com/news/search"

    try:
        response = requests.get(
            url,
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
        print("خطا در جست‌وجوی Bing:", error)
        return []


def search_news():
    strong_news = []
    review_news = []

    checked_links = set()
    checked_titles = set()

    def save_news(news):
        title = news["title"].strip()
        link = news["link"].strip()

        if not title:
            return

        if link and link in checked_links:
            return

        if title in checked_titles:
            return

        if link:
            checked_links.add(link)

        checked_titles.add(title)

        if is_local_title(title):
            strong_news.append(news)

        elif is_local_description(news["description"]):
            review_news.append(news)

    # بررسی پنج منبع عمومی
    for name, url in RSS_SOURCES.items():
        news_list = fetch_rss(name, url)

        for news in news_list:
            news["source"] = news["source"] or name
            save_news(news)

        time.sleep(1)

    # جست‌وجوی اختصاصی مناطق شفت
    for query in BING_QUERIES:
        news_list = search_bing(query)

        for news in news_list:
            news["source"] = news["source"] or "Bing News"
            save_news(news)

        time.sleep(1)

    print("\n================================")
    print("نتیجه نهایی جست‌وجو")
    print("================================")

    print("\nخبرهایی که عنوانشان نشانه محلی دارد:")
    print("تعداد:", len(strong_news))

    for index, news in enumerate(strong_news, start=1):
        print("\n------------------------------")
        print("شماره:", index)
        print("عنوان:", news["title"])
        print("منبع:", news["source"])
        print("تاریخ:", news["date"])
        print("لینک:", news["link"])

    print("\nخبرهای نیازمند بررسی بیشتر:")
    print("تعداد:", len(review_news))

    for index, news in enumerate(review_news, start=1):
        print("\n------------------------------")
        print("شماره:", index)
        print("عنوان:", news["title"])
        print("منبع:", news["source"])
        print("تاریخ:", news["date"])
        print("لینک:", news["link"])


if __name__ == "__main__":
    search_news()
