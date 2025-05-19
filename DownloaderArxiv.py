import arxiv
import os
import time
import re
import json
import requests
from PyPDF2 import PdfReader
from arxiv import Client, Search, Result

# === Конфигурация ===
BASE_DIR = 'Articless_pdf'  # Папка для сохранения всех тем
LOG_FILE = 'arxiv_log.json'      # Имя файла лога
FILES_TO_DOWNLOAD_PER_SUBDIVISION = 5  # Количество новых PDF для каждой темы
MAX_ATTEMPTS = 3  # Попыток на скачивание одного файла
DOWNLOAD_TIMEOUT = 60  # Таймаут HTTP-запроса в секундах
THREADS = 5  # Число потоков для параллельной загрузки


BASE_DIR = os.path.abspath(BASE_DIR)
print(f"Директория для сохранения: {BASE_DIR}")


client = Client()


def download_pdf_with_timeout(self, filename=None, dirpath='.', timeout=DOWNLOAD_TIMEOUT):
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", self.title)[:255]
    filename = filename or (safe_title + '.pdf')
    filepath = os.path.join(dirpath, filename)
    try:
        response = requests.get(self.pdf_url, timeout=timeout, stream=True)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Скачан: {filepath}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка скачивания PDF {filename}: {e}")
        raise RuntimeError(e)
    return filepath

Result.download_pdf = download_pdf_with_timeout


def is_valid_pdf(path):
    try:
        PdfReader(path)
        return True
    except Exception:
        return False


def download_paper_safe(result, subdivision_dir, log_data):
    safe_title = re.sub(r'[\\/*?:"<>|]', '_', result.title)[:255]
    pdf_filename = f"{safe_title}.pdf"
    pdf_path = os.path.join(subdivision_dir, pdf_filename)

    if os.path.exists(pdf_path) and is_valid_pdf(pdf_path):
        print(f"Уже есть, пропускаем: {pdf_path}")
        return False

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            if attempt > 1:
                time.sleep(5)
            result.download_pdf(filename=pdf_filename, dirpath=subdivision_dir)
            if is_valid_pdf(pdf_path):
                entry = {
                    "filename": pdf_filename,
                    "categories": result.categories,
                    "url": result.entry_id,
                    "submitted_date": result.updated.isoformat()
                }
                log_data.append(entry)
                with open(LOG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, ensure_ascii=False, indent=2)
                return True
            else:
                os.remove(pdf_path)
                print(f"Файл битый, удаляем: {pdf_filename}")
        except RuntimeError as e:
            print(f"Попытка {attempt} не удалась: {e}")
    print(f"Не удалось скачать после {MAX_ATTEMPTS} попыток: {pdf_filename}")
    return False


def process_subdivision(subdivision, log_data):
    subdivision_dir = os.path.join(BASE_DIR, subdivision)
    os.makedirs(subdivision_dir, exist_ok=True)
    print(f"=== Тема {subdivision}: нужно скачать {FILES_TO_DOWNLOAD_PER_SUBDIVISION} ===")

    search = Search(
        query=f'cat:{subdivision}',
        max_results=FILES_TO_DOWNLOAD_PER_SUBDIVISION * 3,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    downloaded = 0
    for result in client.results(search):
        if downloaded >= FILES_TO_DOWNLOAD_PER_SUBDIVISION:
            break
        if download_paper_safe(result, subdivision_dir, log_data):
            downloaded += 1
    print(f"Тема {subdivision}: скачано {downloaded}/{FILES_TO_DOWNLOAD_PER_SUBDIVISION}\n")


def main():
    os.makedirs(BASE_DIR, exist_ok=True)

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
    else:
        log_data = []

    subdivisions = [
        'cs.AR', 'cs.FL', 'cs.GL', 'cs.GR', 'cs.HC', 'cs.IR', 'cs.IT', 'cs.LG', 'cs.LO', 'cs.MA',
        'cs.MM', 'cs.MS', 'cs.NA', 'cs.NE', 'cs.NI', 'cs.OH', 'cs.OS', 'cs.PF', 'cs.PL', 'cs.RO',
        'cs.SC', 'cs.SD', 'cs.SE', 'cs.SI', 'cs.SY',
        'econ.EM', 'econ.GN', 'econ.TH',
        'eess.AS', 'eess.IV', 'eess.SP', 'eess.SY',
        'math.AP', 'math.AT', 'math.CA', 'math.CO', 'math.CT', 'math.CV', 'math.DG', 'math.DS', 'math.FA',
        'math.GM', 'math.GN', 'math.GR', 'math.GT', 'math.HO', 'math.IT', 'math.KT', 'math.LO', 'math.MG',
        'math.MP', 'math.NA', 'math.NT', 'math.OA', 'math.OC', 'math.PR', 'math.QA', 'math.RA', 'math.RT',
        'math.SG', 'math.SP', 'math.ST',
        'nlin.AO', 'nlin.CD', 'nlin.CG', 'nlin.PS', 'nlin.SI',
        'nucl-ex', 'nucl-th', 'papers',
        'physics.acc-ph', 'physics.ao-ph', 'physics.app-ph', 'physics.atm-clus', 'physics.atom-ph',
        'physics.bio-ph', 'physics.chem-ph', 'physics.class-ph', 'physics.comp-ph', 'physics.data-an',
        'physics.ed-ph', 'physics.flu-dyn', 'physics.gen-ph', 'physics.geo-ph', 'physics.hist-ph',
        'physics.ins-det', 'physics.med-ph', 'physics.optics', 'physics.plasm-ph', 'physics.pop-ph',
        'physics.soc-ph', 'physics.space-ph',
        'q-bio.BM', 'q-bio.CB', 'q-bio.GN', 'q-bio.MN', 'q-bio.NC', 'q-bio.OT', 'q-bio.PE',
        'q-bio.QM', 'q-bio.SC', 'q-bio.TO',
        'q-fin.CP', 'q-fin.EC', 'q-fin.GN', 'q-fin.MF', 'q-fin.PM', 'q-fin.PR', 'q-fin.RM',
        'q-fin.ST', 'q-fin.TR',
        'quant-ph',
        'stat.AP', 'stat.CO', 'stat.ME', 'stat.ML', 'stat.OT', 'stat.TH'
    ]

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(process_subdivision, sub, log_data) for sub in subdivisions]
        for f in futures:
            f.result()

if __name__ == '__main__':
    main()
