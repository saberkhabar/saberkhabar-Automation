
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
# تنظیمات اصلی
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
# کلمات فیلتر
# =====================================

AD_WORDS = [
    "تخفیف ویژه",
    "فروش ویژه",
    "حراج",
    "قیمت استثنایی",
    "خرید مستقیم",
    "فروش فوری",
    "فروش اقساطی",
    "ارسال رایگان",
    "سفارش دهید",
    "جهت سفارش",
    "جهت خرید",
    "ثبت سفارش",
    "تماس جهت خرید",
    "معرفی محصول",
    "محصولات ما",
    "خدمات ما",
    "نمایندگی فروش",
    "فروشگاه",
    "تبلیغات",
    "آگهی تبلیغاتی",
    "تور گردشگری",
    "تور زیارتی",
    "کاروان زیارتی",
    "کاروان کربلا",
    "ظرفیت محدود",
    "رزرو کنید",
    "مشاوره رایگان",
]

NON_NEWS_WORDS = [
    "تبریک و تهنیت",
    "تبریک عرض می نماییم",
    "تبریک عرض می‌کنیم",
    "سالروز تولد",
    "تولدتان مبارک",
    "پیام تبریک",
    "پیام تسلیت",
    "درگذشت پدر گرامی",
    "درگذشت مادر گرامی",
    "مصیبت وارده",
    "تسلیت عرض می نماییم",
    "تسلیت عرض می‌کنیم",
    "یادبود شخصی",
]

IMPORTANT_NOTICE_WORDS = [
    "تعطیلی مدارس",
    "مدارس تعطیل",
    "غیرحضوری شدن مدارس",
    "غیرحضوری مدارس",
    "قطعی آب",
    "قطعی برق",
    "افت فشار آب",
    "قطعی گاز",
    "هشدار هواشناسی",
    "هشدار سیل",
    "هشدار بارندگی",
    "هشدار زلزله",
    "اطلاعیه فرمانداری",
    "اطلاعیه بخشداری",
    "اطلاعیه آموزش و پرورش",
    "اطلاعیه آب و فاضلاب",
    "اطلاعیه برق",
    "اطلاعیه اورژانس",
    "اطلاعیه پلیس",
    "اطلاعیه مدیریت بحران",
]

MEMORIAL_PHRASES = [
    "مراسم سومین و هفتمین روز",
    "مراسم سوم و هفتم",
    "مراسم سومین روز",
    "مراسم هفتمین روز",
    "اولین سالگرد درگذشت",
    "دومین سالگرد درگذشت",
    "سالگرد درگذشت",
    "مجلس ترحیم",
    "آگهی ترحیم",
    "اطلاعیه ترحیم",
    "مراسم چهلم",
    "چهلمین روز درگذشت",
    "مراسم سوم",
    "مراسم هفتم",
    "یادبود مرحوم",
    "یادبود مرحومه",
    "مراسم یادبود",
    "مجلس یادبود",
]

MUSIC_WORDS = [
    "آهنگساز",
    "خواننده",
    "ترانه سرا",
    "ترانه‌سرا",
    "متن آهنگ",
    "موزیک",
    "آلبوم موسیقی",
    "قطعه موسیقی",
    "آهنگ جدید",
    "اثری از خواننده",
]

CEREMONIAL_WORDS = [
    "گرامیداشت هفته بسیج",
    "هفته بسیج گرامی باد",
    "فرارسیدن هفته بسیج",
    "بسم الله الرحمن الرحیم",
    "پیام فرمانده",
    "پیام تبریک فرمانده",
]

REAL_EVENT_WORDS = [
    "برگزار شد",
    "آغاز شد",
    "افتتاح شد",
    "افتتاحیه",
    "شرکت کردند",
    "شرکت کرد",
    "حضور یافت",
    "مسابقات",
    "مسابقه",
    "بازدید",
    "تصادف",
    "حادثه",
    "امدادرسانی",
    "نجات",
    "دستگیری",
    "آتش سوزی",
    "آتش‌سوزی",
    "توسعه",
    "پیگیری",
    "تجهیز",
    "راه اندازی",
    "راه‌اندازی",
    "قهرمان",
    "کسب مقام",
    "مدال",
    "افتتاح",
    "بهره برداری",
    "بهره‌برداری",
    "کلنگ زنی",
    "کلنگ‌زنی",
    "توزیع شد",
    "پروژه عمرانی",
    "برنامه اجرا",
    "برنامه‌های اجرا",
    "برنامه های اجرا",
]


# =====================================
# آمار منابع
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

    # تبدیل اعداد فارسی و عربی به انگلیسی
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"

    for i in range(10):
        text = text.replace(persian_digits[i], str(i))
        text = text.replace(arabic_digits[i], str(i))

    text = re.sub(r"[^\w\s]", " ", text)

    return " ".join(text.split()).lower()


# =====================================
# تشخیص اطلاعیه مهم
# =====================================

def is_important_notice(text):

    normalized = normalize_text(text)

    return any(
        normalize_text(word) in normalized
        for word in IMPORTANT_NOTICE_WORDS
    )


# =====================================
# تشخیص رویداد واقعی
# =====================================

def has_real_event(text):

    normalized = normalize_text(text)

    return any(
        normalize_text(word) in normalized
        for word in REAL_EVENT_WORDS
    )


# =====================================
# تشخیص آگهی ترحیم
# =====================================

def is_memorial_announcement(title, description):

    text = normalize_text(title + " " + description)

    if any(
        normalize_text(word) in text
        for word in MEMORIAL_PHRASES
    ):
        return True

    memorial_context = [
        "مرحوم",
        "مرحومه",
        "درگذشت",
        "فوت",
    ]

    private_context = [
        "خانواده",
        "بازماندگان",
        "مسجد",
        "مراسم",
        "مجلس",
        "سالگرد",
    ]

    has_memorial = any(
        word in text
        for word in memorial_context
    )

    has_private_context = any(
        word in text
        for word in private_context
    )

    return has_memorial and has_private_context


# =====================================
# تشخیص محتوای موسیقی
# =====================================

def is_music_content(title, description):

    text = normalize_text(title + " " + description)

    music_count = sum(
        1 for word in MUSIC_WORDS
        if normalize_text(word) in text
    )

    if music_count >= 2:
        return True

    if "متن ترانه" in text and music_count >= 1:
        return True

    return False


# =====================================
# تشخیص پیام مناسبتی بدون خبر
# =====================================

def is_empty_ceremonial_message(title, description):

    text = normalize_text(title + " " + description)

    has_ceremonial = any(
        normalize_text(word) in text
        for word in CEREMONIAL_WORDS
    )

    if not has_ceremonial:
        return False

    if has_real_event(text):
        return False

    has_program = "برنامه" in text
    has_number = bool(re.search(r"\d+", text))

    if has_program and has_number:
        return False

    return True


# =====================================
# فیلتر اصلی تبلیغات
# =====================================

def is_advertisement(title, description):

    text = normalize_text(title + " " + description)

    if is_important_notice(text):
        return False, ""

    if is_memorial_announcement(title, description):
        return True, "آگهی مراسم ترحیم و یادبود خانوادگی"

    for word in NON_NEWS_WORDS:

        if normalize_text(word) in text:
            return True, "پیام تبریک یا تسلیت غیرخبری"

    if is_music_content(title, description):
        return True, "محتوای موسیقی غیرخبری"

    if is_empty_ceremonial_message(title, description):
        return True, "متن مناسبتی بدون خبر مشخص"

    for word in AD_WORDS:

        if normalize_text(word) in text:
            return True, "عبارت تبلیغاتی: " + word

    commercial_words = [
        "فروش",
        "خرید",
        "سفارش",
        "ثبت نام",
        "رزرو",
        "قیمت",
        "محصول",
        "خدمات",
    ]

    has_phone = bool(
        re.search(r"09\d{9}", text)
    )

    has_commercial_word = any(
        normalize_text(word) in text
        for word in commercial_words
    )

    if has_phone and has_commercial_word:
        return True, "شماره تماس همراه با عبارت تجاری"

    return False, ""


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
# دریافت پست‌های عمومی تلگرام
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
# جست‌وجوی Bing News
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
# جست‌وجوی اصلی اخبار
# =====================================

def search_news():

    all_news = []

    now = datetime.now(timezone.utc)

    date_limit = now - timedelta(days=DAYS_BACK)

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

    # =================================
    # فیلتر خبرها
    # =================================

    local_count = 0
    ad_count = 0
    old_count = 0
    missing_date_count = 0
    future_count = 0
    not_local_count = 0
    empty_count = 0

    local_news = []
    removed_ads = []

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

        # حذف تبلیغات و پیام‌های غیرخبری
        is_ad, reason = is_advertisement(
            title,
            description
        )

        if is_ad:

            ad_count += 1

            if len(removed_ads) < 20:

                removed_ads.append({
                    "title": title,
                    "reason": reason,
                    "source": news["source"]
                })

            continue

        if date is None:

            missing_date_count += 1
            continue

        if date < date_limit:

            old_count += 1
            continue

        if date > now:

            future_count += 1
            continue

        local_news.append(news)

    # =================================
    # مرتب‌سازی خبرها
    # =================================

    local_news.sort(
        key=lambda item: item["date"],
        reverse=True
    )

    # =================================
    # حذف خبرهای تکراری
    # =================================

    final_news = []

    for news in local_news:

        if not is_duplicate(news, final_news):

            final_news.append(news)

    duplicate_count = len(local_news) - len(final_news)

    # =================================
    # گزارش نهایی
    # =================================

    print("\n")
    print("=" * 45)
    print("گزارش نهایی جست‌وجوی اخبار شهرستان شفت - نسخه 26")
    print("=" * 45)

    print("بازه بررسی:", DAYS_BACK, "روز اخیر")
    print("کل موارد دریافتی:", len(all_news))
    print("موارد محلی شناسایی‌شده:", local_count)
    print("تبلیغات و پیام‌های غیرخبری حذف‌شده:", ad_count)
    print("خبرهای قدیمی:", old_count)
    print("خبرهای بدون تاریخ:", missing_date_count)
    print("خبرهای دارای تاریخ آینده:", future_count)
    print("موارد نامرتبط:", not_local_count)
    print("موارد خالی:", empty_count)
    print("خبرهای محلی در بازه زمانی:", len(local_news))
    print("خبرهای تکراری حذف‌شده:", duplicate_count)

    # =================================
    # آمار منابع
    # =================================

    print("\n")
    print("=" * 45)
    print("تعداد دریافتی از هر منبع")
    print("=" * 45)

    for source, count in source_counts.items():

        print(f"- {source}: {count}")

    if source_errors:

        print("\nخطاهای منابع:")

        for source, error in source_errors.items():

            print(f"- {source}: {error}")

    # =================================
    # نمونه تبلیغات حذف‌شده
    # =================================

    print("\n")
    print("=" * 45)
    print("نمونه تبلیغات حذف‌شده")
    print("=" * 45)

    if removed_ads:

        for index, item in enumerate(removed_ads, start=1):

            print("\nشماره:", index)
            print("عنوان:", item["title"])
            print("علت حذف:", item["reason"])
            print("منبع:", item["source"])

    else:

        print("تبلیغی شناسایی نشد.")

    # =================================
    # نمایش خبرهای نهایی
    # =================================

    print("\n")
    print("=" * 45)
    print("خبرهای نهایی قابل بررسی:", len(final_news))
    print("=" * 45)

    for index, news in enumerate(final_news, start=1):

        print("\n------------------------------")

        print("شماره:", index)
        print("عنوان:", news["title"])
        print("متن:", news["description"][:500])
        print("منبع:", news["source"])
        print("تاریخ:", news["date_text"])
        print("لینک:", news["link"])

    print("\nپایان گزارش")
    print("نسخه 26 اجرا شد.")
    print("انتشار خودکار غیرفعال است.")

    return final_news


# =====================================
# اجرای برنامه
# =====================================

if __name__ == "__main__":

    search_news()
