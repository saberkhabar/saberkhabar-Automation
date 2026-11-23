
import os
import re
import html
import time
import requests
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse, parse_qs, urljoin


# =====================================================
# نسخه 28 - اخبار شهرستان شفت همراه تصویر
# انتشار خودکار غیرفعال است.
# =====================================================

VERSION = 28
DAYS_BACK = 7
HEADERS = {"User-Agent": "Mozilla/5.0"}

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
    '"چوبر" شفت',
    '"نصیرمحله" شفت',
    '"جیرده" شفت',
    '"ملاسرا" شفت',
    '"ویسرود" شفت',
    '"چناررودخان" شفت',
]

LOCAL_WORDS = [
    "شفت", "شهرستان شفت",
    "احمدسرگوراب", "احمد سرگوراب",
    "امامزاده ابراهیم", "سیاهمزگی",
    "چوبر", "نصیرمحله", "نصیر محله",
    "جیرده", "ملاسرا", "ویسرود",
    "لاسک", "بداب", "خرمکش",
    "علیسرا", "شالده", "خمیران",
    "گوراب پس", "چماچا", "چناررودخان",
]

PROMOTION_MARKERS = [
    "کانال شفت خبر در تلگرام",
    "کانال شفت خبر در ایتا",
    "کانال شفت خبر در روبیکا",
    "کانال شفت خبر در بله",
    "ما را به دوستان خود معرفی کنید",
    "مارا به دوستان خود معرفی کنید",
    "ما را به دوستانتان معرفی کنید",
    "جهت عضویت در کانال",
    "برای عضویت در کانال",
    "آدرس ما در ایتا",
    "آدرس ما در بله",
    "ما را در فضای مجازی دنبال کنید",
    "با ما همراه باشید در",
    "کانال ما در پیام رسان",
    "کانال رسمی ما",
    "لینک کانال",
]

PROMOTION_URL_RE = re.compile(
    r"(https?://)?(t\.me/|telegram\.me/|ble\.ir/|"
    r"eitaa\.com/|rubika\.ir/)",
    re.IGNORECASE,
)

AD_WORDS = [
    "تخفیف ویژه", "فروش ویژه", "حراج",
    "قیمت استثنایی", "خرید مستقیم",
    "فروش فوری", "فروش اقساطی",
    "ارسال رایگان", "سفارش دهید",
    "جهت سفارش", "جهت خرید", "ثبت سفارش",
    "تماس جهت خرید", "معرفی محصول",
    "محصولات ما", "خدمات ما",
    "نمایندگی فروش", "فروشگاه",
    "تبلیغات", "آگهی تبلیغاتی",
    "تور گردشگری", "تور زیارتی",
    "کاروان زیارتی", "کاروان کربلا",
    "ظرفیت محدود", "رزرو کنید",
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
    "تعطیلی مدارس", "مدارس تعطیل",
    "غیرحضوری شدن مدارس", "غیرحضوری مدارس",
    "قطعی آب", "قطعی برق", "افت فشار آب",
    "قطعی گاز", "هشدار هواشناسی",
    "هشدار سیل", "هشدار بارندگی",
    "هشدار زلزله", "اطلاعیه فرمانداری",
    "اطلاعیه بخشداری",
    "اطلاعیه آموزش و پرورش",
    "اطلاعیه آب و فاضلاب",
    "اطلاعیه برق", "اطلاعیه اورژانس",
    "اطلاعیه پلیس", "اطلاعیه مدیریت بحران",
]

MUSIC_WORDS = [
    "آهنگساز", "خواننده", "ترانه سرا",
    "ترانه‌سرا", "متن آهنگ", "موزیک",
    "آلبوم موسیقی", "قطعه موسیقی",
    "آهنگ جدید", "اثری از خواننده",
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
    "برگزار شد", "آغاز شد", "افتتاح شد",
    "افتتاحیه", "شرکت کردند", "شرکت کرد",
    "حضور یافت", "مسابقات", "مسابقه",
    "بازدید", "تصادف", "حادثه",
    "امدادرسانی", "نجات", "دستگیری",
    "آتش سوزی", "آتش‌سوزی",
    "توسعه", "پیگیری", "تجهیز",
    "راه اندازی", "راه‌اندازی",
    "قهرمان", "کسب مقام", "مدال",
    "افتتاح", "بهره برداری", "بهره‌برداری",
    "کلنگ زنی", "کلنگ‌زنی", "توزیع شد",
    "پروژه عمرانی", "برنامه اجرا",
    "برنامه‌های اجرا", "برنامه های اجرا",
    "یادواره شهدا", "یادواره شهدای",
]

source_counts = {}
source_errors = {}


# =====================================================
# پاک‌سازی متن
# =====================================================

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

    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"

    for i in range(10):
        text = text.replace(persian_digits[i], str(i))
        text = text.replace(arabic_digits[i], str(i))

    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split()).lower()


def register_source(name, count):
    source_counts[name] = count


def register_error(name, error):
    source_errors[name] = str(error)


# =====================================================
# حذف تبلیغات انتهای متن
# =====================================================

def strip_channel_promotion(text):

    if not text:
        return "", False

    raw = html.unescape(str(text))
    raw = raw.replace("\r", "\n")

    raw = re.sub(
        r"<br\s*/?>",
        "\n",
        raw,
        flags=re.IGNORECASE
    )

    raw = re.sub(
        r"</p\s*>",
        "\n",
        raw,
        flags=re.IGNORECASE
    )

    raw = re.sub(r"<[^>]+>", " ", raw)

    lowered = raw.lower()
    positions = []

    for marker in PROMOTION_MARKERS:
        pos = lowered.find(marker.lower())
        if pos >= 0:
            positions.append(pos)

    if positions:
        raw = raw[:min(positions)]
        return clean_text(raw), True

    kept = []
    removed = False

    for line in raw.splitlines():

        low = line.lower()

        promotional = (
            "@shaft_khabar" in low
            or "ما را دنبال کنید" in line
            or "ما رو دنبال کنید" in line
            or "به کانال بپیوندید" in line
            or "عضو کانال شوید" in line
            or bool(PROMOTION_URL_RE.search(line))
        )

        if promotional:
            removed = True
        else:
            kept.append(line)

    return clean_text("\n".join(kept)), removed


def prepare_news_text(title, description):

    title, title_promo = strip_channel_promotion(title)
    description, desc_promo = strip_channel_promotion(description)

    return title, description, title_promo or desc_promo


# =====================================================
# استخراج تصویر از RSS
# =====================================================

def get_image_url(item):

    # تصویرهای enclosure، media:content و media:thumbnail
    for element in item.iter():

        tag = element.tag.split("}")[-1].lower()

        if tag in ("content", "thumbnail", "enclosure"):

            image_url = element.attrib.get("url", "")

            media_type = element.attrib.get("type", "").lower()

            if image_url and (
                tag != "enclosure"
                or media_type.startswith("image/")
                or not media_type
            ):
                return image_url

    # جست‌وجوی تصویر در توضیحات HTML خبر
    for element in item.iter():

        tag = element.tag.split("}")[-1].lower()

        if tag in ("description", "encoded", "content"):

            raw = "".join(element.itertext())

            soup = BeautifulSoup(raw, "html.parser")

            img = soup.find("img")

            if img:

                image_url = (
                    img.get("src")
                    or img.get("data-src")
                    or img.get("data-original")
                )

                if image_url:
                    return image_url

    return ""


# =====================================================
# استخراج اطلاعات RSS
# =====================================================

def get_child_text(element, name):

    for child in element:

        tag = child.tag.split("}")[-1].lower()

        if tag == name.lower():

            if name.lower() == "link":
                return child.attrib.get("href", child.text or "")

            return " ".join(
                part for part in child.itertext() if part
            ).strip()

    return ""


def get_news_items(root):

    return [
        element for element in root.iter()
        if element.tag.split("}")[-1].lower()
        in ("item", "entry")
    ]


def extract_real_link(link):

    if not link:
        return ""

    try:
        params = parse_qs(urlparse(link).query)

        if "url" in params:
            return params["url"][0]

    except Exception:
        pass

    return link.strip()


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

    title = clean_text(get_child_text(item, "title"))

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

    return {
        "title": title,
        "description": description,
        "link": link,
        "date_text": date_text,
        "date": parse_news_date(date_text),
        "image_url": get_image_url(item),
        "source": "",
    }


# =====================================================
# دریافت RSS
# =====================================================

def fetch_rss(name, url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        root = ET.fromstring(response.content)
        items = get_news_items(root)

        news_list = []

        for item in items:

            news = get_news_data(item)
            news["source"] = name

            news_list.append(news)

        register_source(name, len(news_list))

        print(f"RSS دریافت شد: {len(news_list)} مورد")

        return news_list

    except Exception as error:

        register_source(name, 0)
        register_error(name, error)

        print("خطا در دریافت یک منبع RSS")

        return []


# =====================================================
# استخراج تصویر از تلگرام
# =====================================================

def get_telegram_image(block):

    photo = block.select_one(
        ".tgme_widget_message_photo_wrap"
    )

    if photo:

        style = photo.get("style", "")

        match = re.search(
            r"background-image\s*:\s*url\(['\"]?(.*?)['\"]?\)",
            style,
            re.IGNORECASE
        )

        if match:
            return html.unescape(match.group(1))

    # تصویرهای احتمالی دیگر در پست
    img = block.select_one(
        ".tgme_widget_message_photo img"
    )

    if img:
        return (
            img.get("src")
            or img.get("data-src")
            or ""
        )

    return ""


# =====================================================
# دریافت پست‌های تلگرام
# =====================================================

def fetch_telegram_channel(name, username):

    url = f"https://t.me/s/{username}"
    news_list = []

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        blocks = soup.select(
            "div.tgme_widget_message"
        )

        for block in blocks:

            text_element = block.select_one(
                ".tgme_widget_message_text"
            )

            if not text_element:
                continue

            raw_description = text_element.get_text(
                "\n",
                strip=True
            )

            description, promo_found = strip_channel_promotion(
                raw_description
            )

            if not description:
                continue

            if promo_found and len(normalize_text(description)) < 45:
                continue

            time_element = block.select_one("time")

            date_text = (
                time_element.get("datetime", "")
                if time_element else ""
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
                "image_url": get_telegram_image(block),
                "source": "تلگرام - " + name,
            })

        register_source(
            "تلگرام - " + name,
            len(news_list)
        )

        print(f"پست تلگرام دریافت شد: {len(news_list)} مورد")

        return news_list

    except Exception as error:

        register_source("تلگرام - " + name, 0)
        register_error("تلگرام - " + name, error)

        print("خطا در دریافت یک کانال تلگرام")

        return []


# =====================================================
# جست‌وجوی Bing News
# =====================================================

def search_bing(query):

    try:

        response = requests.get(
            "https://www.bing.com/news/search",
            params={
                "q": query,
                "format": "rss",
                "setlang": "fa",
            },
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        root = ET.fromstring(response.content)
        items = get_news_items(root)

        news_list = []

        for item in items:

            news = get_news_data(item)
            news["source"] = "Bing News"

            news_list.append(news)

        return news_list

    except Exception as error:

        register_error("Bing", error)

        print("خطا در جست‌وجوی Bing")

        return []


# =====================================================
# فیلترهای محلی و خبری
# =====================================================

def is_local_news(title, description):

    text = title + " " + description

    text = re.sub(
        r"(?<!\S)#[\w\u0600-\u06FF]+",
        " ",
        text
    )

    normalized = normalize_text(text)

    return any(
        normalize_text(word) in normalized
        for word in LOCAL_WORDS
    )


def is_important_notice(text):

    normalized = normalize_text(text)

    return any(
        normalize_text(word) in normalized
        for word in IMPORTANT_NOTICE_WORDS
    )


def has_real_event(text):

    normalized = normalize_text(text)

    return any(
        normalize_text(word) in normalized
        for word in REAL_EVENT_WORDS
    )


def is_memorial_announcement(title, description):

    text = normalize_text(title + " " + description)

    if "یادواره شهدا" in text or "یادواره شهدای" in text:
        return False

    death_words = [
        "مرحوم", "مرحومه", "درگذشت",
        "فوت", "مصیبت وارده",
    ]

    private_words = [
        "خانواده", "بازماندگان", "پدر",
        "مادر", "همسر", "فرزند", "برادر",
        "خواهر", "مجلس ترحیم", "آگهی ترحیم",
        "مراسم سوم", "مراسم هفتم",
        "مراسم چهلم", "سالگرد درگذشت",
        "یادبود مرحوم",
    ]

    has_death = any(
        normalize_text(word) in text
        for word in death_words
    )

    has_private = any(
        normalize_text(word) in text
        for word in private_words
    )

    return has_death and has_private


def is_music_content(title, description):

    text = normalize_text(title + " " + description)

    count = sum(
        1 for word in MUSIC_WORDS
        if normalize_text(word) in text
    )

    return count >= 2 or (
        "متن ترانه" in text and count >= 1
    )


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

    return not (has_program and has_number)


def is_advertisement(title, description):

    text = normalize_text(title + " " + description)

    if is_important_notice(text):
        return False, ""

    if is_memorial_announcement(title, description):
        return True, "آگهی ترحیم خانوادگی"

    for word in NON_NEWS_WORDS:

        if normalize_text(word) in text:
            return True, "پیام تبریک یا تسلیت غیرخبری"

    if is_music_content(title, description):
        return True, "محتوای موسیقی غیرخبری"

    if is_empty_ceremonial_message(title, description):
        return True, "پیام مناسبتی بدون خبر مشخص"

    for word in AD_WORDS:

        if normalize_text(word) in text:
            return True, "عبارت تبلیغاتی"

    commercial_words = [
        "فروش", "خرید", "سفارش",
        "ثبت نام", "رزرو", "قیمت",
        "محصول", "خدمات",
    ]

    has_phone = bool(re.search(r"09\d{9}", text))

    has_commercial = any(
        normalize_text(word) in text
        for word in commercial_words
    )

    if has_phone and has_commercial:
        return True, "شماره تماس همراه با عبارت تجاری"

    return False, ""


# =====================================================
# تشخیص تکراری بودن خبر
# =====================================================

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

            if similarity >= 0.86:
                return True

    return False


# =====================================================
# ساخت گزارش تصویری GitHub Actions
# =====================================================

def write_github_summary(news_list):

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")

    if not summary_path:
        print("محیط GitHub Summary در دسترس نیست.")
        return

    lines = [
        "# گزارش اخبار شهرستان شفت - نسخه 28",
        "",
        "محدوده: شفت، احمدسرگوراب و روستاهای مرتبط",
        "",
        "انتشار خودکار غیرفعال است.",
        "",
        "---",
        "",
    ]

    if not news_list:
        lines.append("خبری برای نمایش پیدا نشد.")

    for index, news in enumerate(news_list, start=1):

        title = news["title"].replace("\n", " ").strip()
        description = news["description"].strip()
        date_text = news["date_text"] or "نامشخص"
        image_url = news.get("image_url", "").strip()

        lines.append(f"## {index}. {title}")
        lines.append("")
        lines.append(description[:1000])
        lines.append("")
        lines.append(f"**تاریخ:** {date_text}")
        lines.append("")

        if image_url.startswith(("https://", "http://")):
            lines.append(
                f"![تصویر خبر {index}]({image_url})"
            )
            lines.append("")
        else:
            lines.append("*برای این خبر تصویری دریافت نشد.*")
            lines.append("")

        lines.append("---")
        lines.append("")

    try:

        with open(
            summary_path,
            "a",
            encoding="utf-8"
        ) as file:

            file.write("\n".join(lines))

        print("گزارش تصویری در GitHub Actions ثبت شد.")

    except Exception:

        print("ثبت گزارش تصویری در GitHub Actions ناموفق بود.")


# =====================================================
# اجرای جست‌وجوی اصلی
# =====================================================

def search_news():

    all_news = []

    now = datetime.now(timezone.utc)
    date_limit = now - timedelta(days=DAYS_BACK)

    # دریافت RSS
    for name, url in RSS_SOURCES.items():

        all_news.extend(fetch_rss(name, url))
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

        results = search_bing(query)

        bing_count += len(results)
        all_news.extend(results)

        time.sleep(1)

    register_source("Bing", bing_count)

    # شمارنده‌ها
    local_count = 0
    ad_count = 0
    old_count = 0
    missing_date_count = 0
    future_count = 0
    not_local_count = 0
    empty_count = 0
    promo_count = 0
    image_count = 0

    local_news = []
    removed_ads = []

    # فیلتر خبرها
    for news in all_news:

        title, description, promo_found = prepare_news_text(
            news["title"],
            news["description"]
        )

        if promo_found:
            promo_count += 1

        if not title and not description:
            empty_count += 1
            continue

        if not is_local_news(title, description):
            not_local_count += 1
            continue

        local_count += 1

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
                })

            continue

        date = news["date"]

        if date is None:
            missing_date_count += 1
            continue

        if date < date_limit:
            old_count += 1
            continue

        if date > now:
            future_count += 1
            continue

        cleaned_news = dict(news)

        cleaned_news["title"] = title or description[:120]
        cleaned_news["description"] = description

        if cleaned_news.get("image_url"):
            image_count += 1

        local_news.append(cleaned_news)

    # مرتب‌سازی جدیدترین خبرها
    local_news.sort(
        key=lambda item: item["date"],
        reverse=True
    )

    # حذف تکراری‌ها
    final_news = []

    for news in local_news:

        if not is_duplicate(news, final_news):
            final_news.append(news)

    duplicate_count = len(local_news) - len(final_news)

    # گزارش متنی
    print("\n")
    print("=" * 50)
    print("گزارش اخبار شهرستان شفت - نسخه 28")
    print("=" * 50)

    print("محدوده: شفت، احمدسرگوراب و روستاهای مرتبط")
    print("اخبار عمومی رشت و فومن پذیرفته نمی‌شوند.")
    print("بازه بررسی:", DAYS_BACK, "روز اخیر")

    print("کل موارد دریافتی:", len(all_news))
    print("موارد دارای تبلیغات کانال:", promo_count)
    print("موارد محلی شناسایی‌شده:", local_count)
    print("تبلیغات حذف‌شده:", ad_count)
    print("خبرهای قدیمی:", old_count)
    print("خبرهای بدون تاریخ:", missing_date_count)
    print("خبرهای دارای تاریخ آینده:", future_count)
    print("موارد نامرتبط:", not_local_count)
    print("موارد خالی:", empty_count)
    print("خبرهای محلی در بازه زمانی:", len(local_news))
    print("خبرهای تکراری حذف‌شده:", duplicate_count)
    print("خبرهای دارای تصویر:", image_count)
    print("خبرهای نهایی:", len(final_news))

    # نمونه تبلیغات حذف‌شده، بدون نمایش نام منبع
    print("\nنمونه تبلیغات حذف‌شده:")

    for index, item in enumerate(removed_ads, start=1):

        print("\nشماره:", index)
        print("عنوان:", item["title"])
        print("علت حذف:", item["reason"])

    # نمایش خبرهای نهایی، بدون نام منبع و لینک
    print("\n")
    print("=" * 50)
    print("خبرهای نهایی")
    print("=" * 50)

    for index, news in enumerate(final_news, start=1):

        print("\n------------------------------")
        print("شماره:", index)
        print("عنوان:", news["title"])
        print("متن:", news["description"][:700])
        print("تاریخ:", news["date_text"])

        if news.get("image_url"):
            print("تصویر:", news["image_url"])
        else:
            print("تصویر: موجود نیست")

    # ایجاد گزارش تصویری در GitHub Actions
    write_github_summary(final_news)

    print("\nپایان گزارش")
    print("نسخه 28 اجرا شد.")
    print("انتشار خودکار غیرفعال است.")

    return final_news


# =====================================================
# اجرای برنامه
# =====================================================

if __name__ == "__main__":
    search_news()
