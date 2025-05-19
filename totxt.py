import os
from pathlib import Path
from PyPDF2 import PdfReader
from concurrent.futures import ThreadPoolExecutor

def extract_text_from_pdf(pdf_path, txt_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        with open(txt_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(text)
    except Exception as e:
        print(f"Ошибка при обработке файла {pdf_path}: {e}")

def process_file(pdf_path, txt_path):
    if not os.path.exists(txt_path):
        print(f"Обработка: {pdf_path} -> {txt_path}")
        extract_text_from_pdf(pdf_path, txt_path)
    else:
        print(f"Пропущен: {txt_path} уже существует")

def process_folder(input_folder, output_folder):
    tasks = []
    with ThreadPoolExecutor() as executor:
        for root, dirs, files in os.walk(input_folder):
            relative_path = os.path.relpath(root, input_folder)
            target_folder = os.path.join(output_folder, relative_path)
            os.makedirs(target_folder, exist_ok=True)

            for file_name in files:
                if file_name.lower().endswith(".pdf"):
                    pdf_path = os.path.join(root, file_name)
                    txt_path = os.path.join(target_folder, f"{Path(file_name).stem}.txt")
                    tasks.append(executor.submit(process_file, pdf_path, txt_path))

        for task in tasks:
            task.result()

def main():
    input_folder = "Articless_pdf"  # Укажите путь к папке с PDF
    output_folder = "Articless"  # Укажите путь к папке для сохранения TXT

    if not os.path.exists(input_folder):
        print(f"Папка с PDF не найдена: {input_folder}")
        return

    os.makedirs(output_folder, exist_ok=True)

    process_folder(input_folder, output_folder)
    print("Обработка завершена!")

if __name__ == "__main__":
    main()