
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

PAGE_URL = "https://khabarfarsi.com/city/1138"

LOCAL_MARKERS = [
    "شهرستان شفت",
    "شفت گیلان",
    "فرماندار شفت",
    "پلیس شفت",
    "مردم شفت",
    "شفتی",
    "احمدسرگوراب",
    "ملاسرا",
    "نصیرمحله",
    "چوبر",
    "جیرده",
    "امامزاده ابراهیم",
    "کلاشم",
    "گوراب پس"
]

BAD_MARKERS = [
    "شفت گیربکس",
    "شفت ورودی",
    "شفت موتور",
    "شفت بالانسر",
    "بلبرینگ",
    "صفحه کلاچ",
    "شفت انتقال قدرت"
]

def get_news():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(
            PAGE_URL,
            headers=headers,
            timeout=30
        )

        print("وضعیت اتصال:", response.status_code)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        headings = soup.select("h2, h3")
        print("تعداد عنوان‌های صفحه:", len(headings))

        news = []
        seen_links = set()

        for heading in headings:
            link_tag = heading.find("a", href=True)

            if not link_tag:
                continue

            title = link_tag.get_text(" ", strip=True)

            if len(title) < 8:
                continue

            card = heading

            for _ in range(3):
                if card.parent:
                    card = card.parent

            card_text = card.get_text(" ", strip=True)
            combined = title + " " + card_text

            if not any(
                marker in combined for marker in LOCAL_MARKERS
            ):
                continue

            if any(
                marker in title for marker in BAD_MARKERS
            ):
                continue

            link = urljoin(PAGE_URL, link_tag["href"])

            if link in seen_links:
                continue

            seen_links.add(link)

            excerpt = card_text.replace(title, "", 1).strip()

            news.append({
                "title": title,
                "link": link,
                "excerpt": excerpt[:300]
            })

        print("تعداد خبرهای محلی احتمالی:", len(news))

        for item in news[:20]:
            print("\n" + "=" * 40)
            print("عنوان:", item["title"])
            print("منبع گردآورنده: خبر فارسی")
            print("لینک:", item["link"])
            print("خلاصه صفحه:", item["excerpt"])

    except Exception as error:
        print("خطا در دریافت خبرها:", error)


if __name__ == "__main__":
    get_news()
