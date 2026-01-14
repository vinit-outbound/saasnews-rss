import requests
from bs4 import BeautifulSoup
from datetime import datetime
from email.utils import format_datetime
import os
import time

BASE_URL = "https://www.thesaasnews.com"

PAGES = {
    "series-a": "/news/series-a",
    "series-b": "/news/series-b",
    "series-c": "/news/series-c",
    "series-d": "/news/series-d",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

os.makedirs("feeds", exist_ok=True)
os.makedirs("state", exist_ok=True)


def get_last_seen(slug):
    path = f"state/{slug}.txt"
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read().strip()
    return None


def set_last_seen(slug, url):
    with open(f"state/{slug}.txt", "w") as f:
        f.write(url)


def scrape_page(slug, path):
    print(f"Scraping {slug}")
    last_seen = get_last_seen(slug)
    articles = []
    page = 1
    stop = False

    while not stop:
        url = BASE_URL + path
        if page > 1:
            url += f"?page={page}"

        res = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(res.text, "html.parser")

        cards = soup.select("a.blog-listing-snippet")
        if not cards:
            break

        for card in cards:
            href = card.get("href")
            full_url = BASE_URL + href

            if last_seen and full_url == last_seen:
                stop = True
                break

            title_el = card.select_one("header h2")
            summary_el = card.select_one("article p")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            summary = summary_el.get_text(strip=True) if summary_el else ""

            articles.append({
                "title": title,
                "link": full_url,
                "description": summary,
                "pubDate": format_datetime(datetime.utcnow())
            })

        # pagination
        next_link = soup.select_one("a.page-next")
        if not next_link:
            break

        page += 1
        time.sleep(1)

    if articles:
        set_last_seen(slug, articles[0]["link"])
        write_rss(slug, articles)


def write_rss(slug, articles):
    items = ""
    for a in articles:
        items += f"""
        <item>
            <title><![CDATA[{a['title']}]]></title>
            <link>{a['link']}</link>
            <description><![CDATA[{a['description']}]]></description>
            <pubDate>{a['pubDate']}</pubDate>
        </item>
        """

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>SaaS News – {slug.upper()}</title>
    <link>{BASE_URL}</link>
    <description>Funding news for {slug.upper()}</description>
    {items}
  </channel>
</rss>
"""

    with open(f"feeds/{slug}.xml", "w", encoding="utf-8") as f:
        f.write(rss)


if __name__ == "__main__":
    for slug, path in PAGES.items():
        scrape_page(slug, path)
