import os
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path, txt_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        with open(txt_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(text)
    except Exception as e:
        print(f"Ошибка при обработке файла {pdf_path}: {e}")

def process_file(pdf_path, txt_path):
    if not os.path.exists(txt_path):
        print(f"Обработка: {pdf_path} → {txt_path}")
        extract_text_from_pdf(pdf_path, txt_path)
    else:
        print(f"Пропущен: {txt_path} уже существует")

def process_folder(input_folder, output_folder):
    tasks = []
    with ThreadPoolExecutor() as executor:
        for root, _, files in os.walk(input_folder):
            rel = os.path.relpath(root, input_folder)
            target_dir = os.path.join(output_folder, rel)
            os.makedirs(target_dir, exist_ok=True)
            for name in files:
                if name.lower().endswith(".pdf"):
                    pdf_path = os.path.join(root, name)
                    txt_path = os.path.join(target_dir, f"{Path(name).stem}.txt")
                    tasks.append(executor.submit(process_file, pdf_path, txt_path))
        for t in tasks:
            t.result()

def main():
    parser = argparse.ArgumentParser(
        description="Конвертирует PDF-файлы в текстовые файлы, сохраняя структуру каталогов."
    )
    parser.add_argument(
        "input_folder", nargs="?", default="Articless_pdf",
        help="Папка с исходными PDF (по умолчанию %(default)s)"
    )
    parser.add_argument(
        "output_folder", nargs="?", default="Articless_arXiv",
        help="Папка для сохранения TXT (по умолчанию %(default)s)"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.input_folder):
        print(f"Папка с PDF не найдена: {args.input_folder}")
        return

    os.makedirs(args.output_folder, exist_ok=True)
    process_folder(args.input_folder, args.output_folder)
    print("Обработка завершена!")

if __name__ == "__main__":
    main()

