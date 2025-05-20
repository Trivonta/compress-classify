import argparse
from pathlib import Path
from PyPDF2 import PdfReader

def pdf_to_txt(pdf_path: Path, txt_path: Path):
    """Извлекает текст из pdf_path и записывает его в txt_path."""
    try:
        reader = PdfReader(str(pdf_path))
        text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
        txt_path.write_text("\n".join(text), encoding="utf-8")
        print(f"Готово: {pdf_path} → {txt_path}")
    except Exception as e:
        print(f"Ошибка при обработке {pdf_path}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Конвертация одного PDF-файла в TXT"
    )
    parser.add_argument(
        "pdf_file",
        help="Путь к входному PDF-файлу"
    )
    parser.add_argument(
        "txt_file",
        nargs="?",
        help="Путь к выходному TXT-файлу (по умолчанию — тот же, что PDF, но с расширением .txt)"
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf_file)
    if not pdf_path.is_file():
        print(f"Файл не найден: {pdf_path}")
        return

    if args.txt_file:
        txt_path = Path(args.txt_file)
    else:
        txt_path = pdf_path.with_suffix(".txt")

    pdf_to_txt(pdf_path, txt_path)

if __name__ == "__main__":
    main()
