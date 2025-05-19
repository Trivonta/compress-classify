import os
import time
import requests
from bs4 import BeautifulSoup
import re
from requests.exceptions import ChunkedEncodingError, SSLError, RequestException

BASE_URL             = "https://cyberleninka.ru"
HEADERS              = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0.0.0 Safari/537.36"
}
DOWNLOAD_FOLDER      = "Articless"
START_PAGE           = 65
TOTAL_DOWNLOAD_LIMIT = 2000
REQUEST_DELAY        = 5  

def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def get_topics(n):
    try:
        resp = requests.get(BASE_URL, headers=HEADERS, timeout=10, verify=False)
        resp.raise_for_status()
    except RequestException as e:
        print(f"Ошибка при загрузке главной страницы: {e}")
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")
    topics = {}
    for link in soup.select("a[href^='/article/c/']"):
        name = link.get_text(strip=True)
        href = link.get("href")
        if href:
            topics[name] = BASE_URL + href
    print("Извлечено тем:", len(topics))
    return topics

def get_article_links(topic_url):
    try:
        resp = requests.get(topic_url, headers=HEADERS, timeout=10, verify=False)
        resp.raise_for_status()
    except RequestException as e:
        print(f"Ошибка при загрузке темы {topic_url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    links = [
        BASE_URL + a["href"]
        for a in soup.select("a[href^='/article/n/']")
        if a.get("href")
    ]
    return links

def download_article_text(article_url, folder_name):
    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=10, verify=False)
        resp.raise_for_status()
        html = resp.text
    except (ChunkedEncodingError, SSLError) as e:
        print(f"Ошибка протокола при чтении {article_url}: {e}. Повтор через {REQUEST_DELAY}s...")
        time.sleep(REQUEST_DELAY)
        try:
            resp = requests.get(article_url, headers=HEADERS, timeout=10, verify=False)
            resp.raise_for_status()
            html = resp.text
        except RequestException as e2:
            print(f"Повтор не удался: {e2}")
            return False
    except RequestException as e:
        print(f"Ошибка при открытии {article_url}: {e}")
        return False

    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("h1")
    if not title_tag:
        print(f"Не найден заголовок: {article_url}")
        return False

    article_title = title_tag.get_text(strip=True)
    safe_name = re.sub(r'[<>:"/\\|?*]', "", article_title)[:100]

    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    if not paragraphs:
        print(f"Пустой текст: {article_url}")
        return False

    create_folder(folder_name)
    file_path = os.path.join(folder_name, safe_name + ".txt")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(paragraphs))
    except OSError as e:
        print(f"Ошибка при сохранении {file_path}: {e}")
        return False

    print(f"Скачано: {safe_name}.txt")
    return True

def remove_files_without_extension(folder_path):
    for root, _, files in os.walk(folder_path):
        for fn in files:
            if "." not in fn:
                fp = os.path.join(root, fn)
                os.remove(fp)
                print(f"Удалён безрасширенный файл: {fp}")

def scrape_balanced_cyberleninka(limit_per_topic):
    total_downloaded = 0
    create_folder(DOWNLOAD_FOLDER)
    page = START_PAGE

    while total_downloaded < TOTAL_DOWNLOAD_LIMIT:
        topics = get_topics(page)
        if not topics:
            print("Не удалось извлечь темы, выходим.")
            return

        state = {
            name: {"url": url, "links": get_article_links(url), "downloaded": 0}
            for name, url in topics.items()
        }
        state = {k: v for k, v in state.items() if v["links"]}

        if not state:
            print(f"Нет статей на странице {page}, переходим к {page+1}")
            page += 1
            continue

        while state and total_downloaded < TOTAL_DOWNLOAD_LIMIT:
            for name in list(state):
                data = state[name]
                if data["downloaded"] >= limit_per_topic:
                    del state[name]
                    continue
                if not data["links"]:
                    del state[name]
                    continue

                url = data["links"].pop(0)
                topic_folder = os.path.join(DOWNLOAD_FOLDER, name.replace(" ", "_"))
                print(f"Скачиваю ({total_downloaded+1}/{TOTAL_DOWNLOAD_LIMIT}): {url} (тема: {name})")
                if download_article_text(url, topic_folder):
                    data["downloaded"] += 1
                    total_downloaded += 1
                time.sleep(REQUEST_DELAY)

                if total_downloaded >= TOTAL_DOWNLOAD_LIMIT:
                    print(f"Достигнут глобальный лимит {TOTAL_DOWNLOAD_LIMIT}.")
                    remove_files_without_extension(DOWNLOAD_FOLDER)
                    return

            print("Раунд скачивания завершён, делаем паузу перед следующим раундом.")
            time.sleep(REQUEST_DELAY)

        page += 1
        print(f"Переходим к странице {page}")

    remove_files_without_extension(DOWNLOAD_FOLDER)

if __name__ == "__main__":
    scrape_balanced_cyberleninka(limit_per_topic=50)
