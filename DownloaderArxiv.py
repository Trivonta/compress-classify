import os
import re
import json
import time
import argparse
import requests
import tempfile
from concurrent.futures import ThreadPoolExecutor
from PyPDF2 import PdfReader
import arxiv
from arxiv import Client, Search, Result

def download_pdf_with_timeout(self, filename, dirpath, timeout):
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", self.title)[:255]
    filename = filename or f"{safe_title}.pdf"
    filepath = os.path.join(dirpath, filename)
    response = requests.get(self.pdf_url, timeout=timeout, stream=True)
    response.raise_for_status()
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return filepath

Result.download_pdf = download_pdf_with_timeout

def is_valid_pdf(path):
    try:
        PdfReader(path)
        return True
    except Exception:
        return False

def download_paper_safe(result, subdivision_dir, log_data, max_attempts, timeout, log_file):
    safe_title = re.sub(r'[\\/*?:"<>|]', '_', result.title)[:255]
    pdf_filename = f"{safe_title}.pdf"
    pdf_path = os.path.join(subdivision_dir, pdf_filename)
    if os.path.exists(pdf_path) and is_valid_pdf(pdf_path):
        return False
    for attempt in range(1, max_attempts + 1):
        try:
            if attempt > 1:
                time.sleep(5)
            result.download_pdf(filename=pdf_filename, dirpath=subdivision_dir, timeout=timeout)
            if is_valid_pdf(pdf_path):
                entry = {
                    "filename": pdf_filename,
                    "categories": result.categories,
                    "url": result.entry_id,
                    "submitted_date": result.updated.isoformat()
                }
                log_data.append(entry)
                with open(log_file, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, ensure_ascii=False, indent=2)
                return True
            else:
                os.remove(pdf_path)
        except Exception:
            continue
    return False

def process_subdivision(subdivision, base_dir, log_data,
                        files_per, max_attempts, timeout, log_file):
    subdivision_dir = os.path.join(base_dir, subdivision)
    os.makedirs(subdivision_dir, exist_ok=True)
    search = Search(
        query=f'cat:{subdivision}',
        max_results=files_per * 3,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    downloaded = 0
    client = Client()
    for result in client.results(search):
        if downloaded >= files_per:
            break
        if download_paper_safe(result, subdivision_dir, log_data,
                               max_attempts, timeout, log_file):
            downloaded += 1

def main():
    parser = argparse.ArgumentParser(
        description="Скачать PDF-статьи с arXiv по категориям"
    )
   
    parser.add_argument(
        "per_category", type=int, nargs="?", default=5,
        help="Сколько PDF скачать из каждой категории (по умолчанию %(default)s)"
    )
    parser.add_argument(
        "base_dir", nargs="?", default="Articless_pdf",
        help="Куда сохранять папки с PDF (по умолчанию '%(default)s')"
    )

    parser.add_argument(
        "--log-file", "-l", default="arxiv_log.json",
        help="Имя JSON-файла лога (по умолчанию arxiv_log.json)"
    )
    parser.add_argument(
        "--attempts", "-a", type=int, default=3,
        help="Сколько попыток при неудаче скачать один PDF (по умолчанию 3)"
    )
    parser.add_argument(
        "--timeout", "-t", type=int, default=60,
        help="Таймаут HTTP-запроса в секундах (по умолчанию 60)"
    )
    parser.add_argument(
        "--threads", "-T", type=int, default=5,
        help="Число потоков для параллельной загрузки (по умолчанию 5)"
    )
    args = parser.parse_args()

    base_dir = os.path.abspath(args.base_dir)
    os.makedirs(base_dir, exist_ok=True)
    log_file = args.log_file
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
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

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = [
            executor.submit(
                process_subdivision,
                sub, base_dir, log_data,
                args.per_category, args.attempts,
                args.timeout, log_file
            )
            for sub in subdivisions
        ]
        for f in futures:
            f.result()

if __name__ == "__main__":
    main()
