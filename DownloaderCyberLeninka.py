import os
import time
import requests
from bs4 import BeautifulSoup
import re
from requests.exceptions import ChunkedEncodingError, SSLError, RequestException
import argparse
import logging
import warnings
from urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter("ignore", InsecureRequestWarning)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
fh = logging.FileHandler('downloader_errors.log', encoding='utf-8')
fh.setLevel(logging.WARNING)
fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(fh)
# ----------------------------------------------------

BASE_URL        = "https://cyberleninka.ru"
HEADERS         = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0.0.0 Safari/537.36"
}
DOWNLOAD_FOLDER = "Articless"
REQUEST_DELAY   = 5

def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def get_topics():
    try:
        resp = requests.get(BASE_URL, headers=HEADERS, timeout=10, verify=False)
        resp.raise_for_status()
    except RequestException as e:
        logger.error(f"Ошибка при загрузке главной страницы: {e}")
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")
    topics = {}
    for link in soup.select("a[href^='/article/c/']"):
        name = link.get_text(strip=True)
        href = link.get("href")
        if href:
            topics[name] = BASE_URL + href
    print(f"[INFO] Извлечено тем: {len(topics)}")
    return topics

def get_article_links(topic_url):
    try:
        resp = requests.get(topic_url, headers=HEADERS, timeout=10, verify=False)
        resp.raise_for_status()
    except RequestException as e:
        logger.error(f"Ошибка при загрузке темы {topic_url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    return [
        BASE_URL + a["href"]
        for a in soup.select("a[href^='/article/n/']")
        if a.get("href")
    ]

def download_article_text(article_url, folder_name):
    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=10, verify=False)
        resp.raise_for_status()
        html = resp.text
    except (ChunkedEncodingError, SSLError) as e:
        logger.warning(f"Протокольная ошибка при чтении {article_url}: {e}. Повтор через {REQUEST_DELAY}s...")
        time.sleep(REQUEST_DELAY)
        try:
            resp = requests.get(article_url, headers=HEADERS, timeout=10, verify=False)
            resp.raise_for_status()
            html = resp.text
        except RequestException as e2:
            logger.error(f"Повтор загрузки не удался для {article_url}: {e2}")
            return False
    except RequestException as e:
        logger.error(f"Ошибка при открытии {article_url}: {e}")
        return False

    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("h1")
    if not title_tag:
        logger.warning(f"Не найден заголовок: {article_url}")
        return False

    article_title = title_tag.get_text(strip=True)
    safe_name = re.sub(r'[<>:"/\\|?*]', "", article_title)[:100]
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    if not paragraphs:
        logger.warning(f"Пустой текст: {article_url}")
        return False

    create_folder(folder_name)
    file_path = os.path.join(folder_name, safe_name + ".txt")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(paragraphs))
    except OSError as e:
        logger.error(f"Ошибка при сохранении {file_path}: {e}")
        return False

    print(f"[DOWNLOAD] {safe_name}.txt")
    return True

def remove_files_without_extension(folder_path):
    for root, _, files in os.walk(folder_path):
        for fn in files:
            if "." not in fn:
                fp = os.path.join(root, fn)
                os.remove(fp)
                print(f"[CLEANUP] Удалён безрасширенный файл: {fp}")

def scrape_balanced_cyberleninka(limit_per_topic):
    create_folder(DOWNLOAD_FOLDER)
    topics = get_topics()
    if not topics:
        print("[ERROR] Не удалось извлечь темы, выходим.")
        return

    state = {}
    for name, url in topics.items():
        links = get_article_links(url)
        if links:
            state[name] = {"links": links, "downloaded": 0}

    while any(v["downloaded"] < limit_per_topic and v["links"] for v in state.values()):
        for name, data in state.items():
            if data["downloaded"] >= limit_per_topic or not data["links"]:
                continue

            article_url = data["links"].pop(0)
            topic_folder = os.path.join(DOWNLOAD_FOLDER, name.replace(" ", "_"))
            print(f"[INFO] ({data['downloaded']+1}/{limit_per_topic}) тема '{name}': {article_url}")
            if download_article_text(article_url, topic_folder):
                data["downloaded"] += 1

            time.sleep(REQUEST_DELAY)

    remove_files_without_extension(DOWNLOAD_FOLDER)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Скрипт для скачивания статей с CyberLeninka"
    )
    parser.add_argument(
        "-n", "--per-topic",
        type=int,
        required=True,
        help="Точное число статей для скачивания в каждую тему"
    )
    args = parser.parse_args()
    scrape_balanced_cyberleninka(limit_per_topic=args.per_topic)
