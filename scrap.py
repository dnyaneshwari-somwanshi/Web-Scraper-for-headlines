import requests
import time
import argparse
import logging
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib.robotparser as robotparser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

HEADERS = {"User-Agent": "Mozilla/5.0"}

SOURCES = {
    "bbc": "https://www.bbc.com/news",
    "cnn": "https://edition.cnn.com/world"
}

def allowed_by_robots(url):
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    rp.set_url(robots_url)
    rp.read()
    return rp.can_fetch("*", url)

def scrape(source_name, keyword=None, delay=2):
    url = SOURCES[source_name]

    if not allowed_by_robots(url):
        logging.error(f"Blocked by robots.txt: {url}")
        return []

    logging.info(f"Scraping {source_name.upper()}")
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    articles = []

    for tag in soup.find_all("a", href=True):
        title = tag.get_text(strip=True)
        link = urljoin(url, tag["href"])

        if not title or len(title) < 20:
            continue

        if keyword and keyword.lower() not in title.lower():
            continue

        articles.append({
            "source": source_name,
            "title": title,
            "url": link,
            "time": None
        })

    time.sleep(delay)
    return articles

def save_output(data, fmt, output_file):
    df = pd.DataFrame(data)
    if fmt == "csv":
        df.to_csv(output_file, index=False)
    else:
        df.to_json(output_file, orient="records", indent=2)
    logging.info(f"Saved {len(df)} records to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Web Scraper for Headlines")
    parser.add_argument("--sources", nargs="+", default=["bbc"])
    parser.add_argument("--keyword", help="Filter headlines by keyword")
    parser.add_argument("--format", choices=["csv", "json"], default="json")
    parser.add_argument("--output", default="output/headlines.json")
    parser.add_argument("--delay", type=int, default=2)

    args = parser.parse_args()
    all_articles = []

    for source in args.sources:
        if source in SOURCES:
            try:
                all_articles.extend(scrape(source, args.keyword, args.delay))
            except Exception as e:
                logging.error(f"Error scraping {source}: {e}")

    if all_articles:
        save_output(all_articles, args.format, args.output)
    else:
        logging.warning("No articles scraped.")

if __name__ == "__main__":
    main()