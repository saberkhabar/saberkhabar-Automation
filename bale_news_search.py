
import requests
import xml.etree.ElementTree as ET
import re
import html
import time

from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse, parse_qs, urljoin


# =====================================
# تنظیمات
# =====================================

DAYS_BACK = 7

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

RSS_SOURCES = {
    "خبرگزاری مهر": "https://www.mehrnews.com/rss",
    "ایسنا": "https://www.isna.ir/rss",
    "صداوسیما": "https://www.irib-news.ir/fa/rss/allnews?",
    "باشگاه خبرنگاران جوان": "https://www.yjc.ir/fa/rss/allnews",
    "تابناک": "https://www.tabnak.ir/fa/rss/allnews",
}

TELEGRAM_CHANNELS = {
    "شفت خبر": "shaft_khabar",
    "گیل خبر": "gilkhabar",
    "ندای گیلان": "guilannews",
    "احمدسرگوراب": "ahmadsargoorab",
    "گیلانستان": "gilanestan",
    "رادیو گیلان": "namayandeh3oma",
    "اخبار گیلان": "akhbaregilan",
    "گیلان فارس": "gilanfars",
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
    '"ویسرود گیلان"',
]

LOCAL_WORDS = [
    "شفت",
    "شهرستان شفت",
    "احمدسرگوراب",
    "احمد سرگوراب",
    "امامزاده ابراهیم",
    "سیاهمزگی",
    "چوبر",
    "نصیرمحله",
    "نصیر محله",
    "جیرده",
    "ملاسرا",
    "ویسرود",
    "لاسک",
    "بداب",
    "خرمکش",
    "علیسرا",
    "شالده",
    "خمیران",
    "گوراب پس",
    "چماچا",
    "چناررودخان",
]


# =====================================
# آمار منابع و خطاها
# =====================================

source_counts = {}
source_errors = {}


def register_source(name, count):
    source_counts[name] = count


def register_error(name, error):
    source_errors[name] = str(error)


# =====================================
# پاک‌سازی متن
# =====================================

def clean_text(text):

    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_text(text):

    text = clean_text(text)

    text = (
        text.replace("ي", "ی")
        .replace("ك", "ک")
        .replace("ۀ", "ه")
        .replace("ة", "ه")
        .replace("\u200c", " ")
    )

    text = re.sub(r"[^\w\s]", " ", text)

    return " ".join(text.split()).lower()


# =====================================
# استخراج لینک اصلی
# =====================================

def extract_real_link(link):

    if not link:
        return ""

    try:

        parsed = urlparse(link)
        params = parse_qs(parsed.query)

        if "url" in params:
            return params["url"][0]

    except Exception:
        pass

    return link.strip()


# =====================================
# خواندن اطلاعات RSS
# =====================================

def get_child_text(element, name):

    for child in element:

        tag = child.tag.split("}")[-1].lower()

        if tag == name.lower():

            if name.lower() == "link":

                return child.attrib.get(
                    "href",
                    child.text or ""
                )

            return " ".join(
                part for part in child.itertext() if part
            ).strip()

    return ""


def get_news_items(root):

    return [
        element
        for element in root.iter()
        if element.tag.split("}")[-1].lower()
        in ("item", "entry")
    ]


# =====================================
# تشخیص خبر محلی
# =====================================

def is_local_news(title, description):

    combined = normalize_text(
        title + " " + description
    )

    return any(
        normalize_text(word) in combined
        for word in LOCAL_WORDS
    )


# =====================================
# تبدیل تاریخ
# =====================================

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


# =====================================
# استخراج خبر از RSS
# =====================================

def get_news_data(item):

    title = clean_text(
        get_child_text(item, "title")
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

    date_text = (
        get_child_text(item, "pubDate")
        or get_child_text(item, "published")
        or get_child_text(item, "updated")
        or get_child_text(item, "date")
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


# =====================================
# دریافت RSS
# =====================================

def fetch_rss(name, url):

    print("\n==============================")
    print("منبع RSS:", name)

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        print("وضعیت اتصال:", response.status_code)

        response.raise_for_status()

        root = ET.fromstring(response.content)

        items = get_news_items(root)

        print("تعداد خبرهای دریافتی:", len(items))

        news_list = []

        for item in items:

            news = get_news_data(item)
            news["source"] = news["source"] or name

            news_list.append(news)

        register_source(name, len(news_list))

        return news_list

    except Exception as error:

        print("خطا در RSS:", error)

        register_source(name, 0)
        register_error(name, error)

        return []


# =====================================
# دریافت تلگرام
# =====================================

def fetch_telegram_channel(name, username):

    print("\n==============================")
    print("کانال تلگرام:", name)

    url = f"https://t.me/s/{username}"

    news_list = []

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        print("وضعیت اتصال:", response.status_code)

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        blocks = soup.select(
            "div.tgme_widget_message"
        )

        print("تعداد پست‌های صفحه:", len(blocks))

        for block in blocks:

            text_element = block.select_one(
                ".tgme_widget_message_text"
            )

            if not text_element:
                continue

            description = clean_text(
                text_element.get_text(" ", strip=True)
            )

            if not description:
                continue

            time_element = block.select_one("time")

            date_text = ""

            if time_element:
                date_text = time_element.get(
                    "datetime",
                    ""
                )

            date = parse_news_date(date_text)

            link_element = block.select_one(
                "a.tgme_widget_message_date"
            )

            link = ""

            if link_element:

                href = link_element.get("href", "")

                if href:
                    link = urljoin("https://t.me", href)

            if not link:
                link = f"https://t.me/{username}"

            title = re.split(
                r"[\n.!؟]",
                description,
                maxsplit=1
            )[0]

            title = clean_text(title)

            if len(title) > 150:
                title = title[:147] + "..."

            news_list.append({

                "title": title,
                "description": description,
                "link": link,
                "date_text": date_text,
                "date": date,
                "source": "تلگرام - " + name

            })

        register_source(
            "تلگرام - " + name,
            len(news_list)
        )

        return news_list

    except Exception as error:

        print("خطا در تلگرام:", error)

        register_source("تلگرام - " + name, 0)
        register_error("تلگرام - " + name, error)

        return []


# =====================================
# جست‌وجوی Bing
# =====================================

def search_bing(query):

    try:

        response = requests.get(
            "https://www.bing.com/news/search",
            params={
                "q": query,
                "format": "rss",
                "setlang": "fa"
            },
            headers=HEADERS,
            timeout=20
        )

        print("\nجست‌وجوی Bing:", query)

        response.raise_for_status()

        root = ET.fromstring(response.content)

        items = get_news_items(root)

        print("تعداد نتایج:", len(items))

        news_list = []

        for item in items:

            news = get_news_data(item)
            news["source"] = news["source"] or "Bing News"

            news_list.append(news)

        return news_list

    except Exception as error:

        print("خطا در Bing:", error)

        register_error("Bing: " + query, error)

        return []


# =====================================
# تشخیص خبر تکراری
# =====================================

def is_duplicate(news, accepted_news):

    title = normalize_text(news["title"])
    link = news["link"].strip()

    for old_news in accepted_news:

        old_link = old_news["link"].strip()

        if link and old_link and link == old_link:
            return True

        old_title = normalize_text(old_news["title"])

        if min(len(title), len(old_title)) >= 25:

            similarity = SequenceMatcher(
                None,
                title,
                old_title
            ).ratio()

            if similarity >= 0.88:
                return True

    return False


# =====================================
# جست‌وجوی اصلی
# =====================================

def search_news():

    all_news = []

    now = datetime.now(timezone.utc)

    seven_days_ago = now - timedelta(days=DAYS_BACK)

    # دریافت RSS

    for name, url in RSS_SOURCES.items():

        all_news.extend(
            fetch_rss(name, url)
        )

        time.sleep(1)

    # دریافت تلگرام

    for name, username in TELEGRAM_CHANNELS.items():

        all_news.extend(
            fetch_telegram_channel(name, username)
        )

        time.sleep(1)

    # دریافت Bing

    bing_count = 0

    for query in BING_QUERIES:

        news_list = search_bing(query)

        bing_count += len(news_list)

        all_news.extend(news_list)

        time.sleep(1)

    register_source("Bing", bing_count)

    # آمار فیلترها

    local_count = 0
    old_news_count = 0
    missing_date_count = 0
    future_date_count = 0
    not_local_count = 0
    empty_count = 0

    local_news = []

    for news in all_news:

        title = news["title"].strip()
        description = news["description"].strip()
        date = news["date"]

        if not title and not description:

            empty_count += 1
            continue

        if not is_local_news(title, description):

            not_local_count += 1
            continue

        local_count += 1

        if date is None:

            missing_date_count += 1
            continue

        if date < seven_days_ago:

            old_news_count += 1
            continue

        if date > now:

            future_date_count += 1
            continue

        local_news.append(news)

    # مرتب‌سازی تاریخ

    local_news.sort(
        key=lambda item: item["date"],
        reverse=True
    )

    # حذف تکراری‌ها

    recent_news = []

    for news in local_news:

        if not is_duplicate(news, recent_news):

            recent_news.append(news)

    duplicate_count = len(local_news) - len(recent_news)

    # گزارش نهایی

    print("\n")
    print("=" * 45)
    print("گزارش نهایی جست‌وجوی اخبار شهرستان شفت")
    print("=" * 45)

    print("بازه بررسی:", DAYS_BACK, "روز اخیر")
    print("کل موارد دریافتی:", len(all_news))
    print("خبرهای محلی شناسایی‌شده:", local_count)
    print("خبرهای محلی در بازه زمانی:", len(local_news))
    print("خبرهای تکراری حذف‌شده:", duplicate_count)
    print("خبرهای قدیمی:", old_news_count)
    print("خبرهای بدون تاریخ:", missing_date_count)
    print("خبرهای دارای تاریخ آینده:", future_date_count)
    print("موارد نامرتبط:", not_local_count)
    print("موارد خالی:", empty_count)

    print("\nتعداد دریافتی از هر منبع:")

    for source, count in source_counts.items():

        print(f"- {source}: {count}")

    if source_errors:

        print("\nخطاهای منابع:")

        for source, error in source_errors.items():

            print(f"- {source}: {error}")

    print("\n")
    print("=" * 45)
    print("خبرهای نهایی قابل بررسی:", len(recent_news))
    print("=" * 45)

    for index, news in enumerate(recent_news, start=1):

        print("\n------------------------------")

        print("شماره:", index)
        print("عنوان:", news["title"])
        print("متن:", news["description"][:500])
        print("منبع:", news["source"])
        print("تاریخ:", news["date_text"])
        print("لینک:", news["link"])

    print("\nپایان گزارش")
    print("انتشار خودکار غیرفعال است.")

    return recent_news


if __name__ == "__main__":

    search_news()
