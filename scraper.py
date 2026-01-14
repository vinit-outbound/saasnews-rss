import requests
from bs4 import BeautifulSoup
from datetime import datetime
from email.utils import format_datetime
import os

BASE_URL = "https://www.thesaasnews.com"
PAGES = {
    "series-a": "/news/series-a",
    "series-b": "/news/series-b",
    "series-c": "/news/series-c",
    "series-d": "/news/series-d",
}

os.makedirs("feeds", exist_ok=True)

def scrape_page(slug, path):
    res = requests.get(BASE_URL + path, timeout=30)
    soup = BeautifulSoup(res.text, "html.parser")

    articles = []

    for card in soup.select("article"):
        title_el = card.select_one("h2 a")
        date_el = card.select_one("time")

        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        link = BASE_URL + title_el["href"]

        if date_el and date_el.has_attr("datetime"):
            pub_date = format_datetime(
                datetime.fromisoformat(date_el["datetime"].replace("Z", "+00:00"))
            )
        else:
            pub_date = format_datetime(datetime.utcnow())

        articles.append({
            "title": title,
            "link": link,
            "pubDate": pub_date
        })

    write_rss(slug, articles)

def write_rss(slug, articles):
    rss_items = ""
    for a in articles:
        rss_items += f"""
        <item>
            <title><![CDATA[{a['title']}]]></title>
            <link>{a['link']}</link>
            <pubDate>{a['pubDate']}</pubDate>
        </item>
        """

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>SaaS News – {slug.upper()}</title>
        <link>{BASE_URL}</link>
        <description>Funding news for {slug.upper()}</description>
        {rss_items}
      </channel>
    </rss>
    """

    with open(f"feeds/{slug}.xml", "w", encoding="utf-8") as f:
        f.write(rss)

if __name__ == "__main__":
    for slug, path in PAGES.items():
        scrape_page(slug, path)
