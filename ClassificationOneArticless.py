import os
import sys
import subprocess
import shutil
import argparse
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed

def compress_text_and_get_diff(zip_tool, core_path, text_path, temp_archive):
    """
    Скопировать core_path -> temp_archive, добавить text_path в temp_archive,
    вернуть (new_size - original_size) или None при ошибке.
    """
    try:
        shutil.copy(core_path, temp_archive)
        orig = os.path.getsize(temp_archive)
        subprocess.run(
            [zip_tool, "a", temp_archive, text_path],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        new = os.path.getsize(temp_archive)
        return new - orig
    except Exception as e:
        return None

def classify_text_with_zips(zip_tool, zip_cores, text_path, max_workers=None):
    temp_files = []
    diffs = {}

    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        futures = {}
        for category, core in zip_cores.items():
            ta = f"tmp_{category}.7z"
            temp_files.append(ta)
            futures[exe.submit(compress_text_and_get_diff, zip_tool, core, text_path, ta)] = category

        for fut in as_completed(futures):
            cat = futures[fut]
            diff = fut.result()
            if diff is not None:
                diffs[cat] = diff

    for ta in temp_files:
        try:
            os.remove(ta)
        except OSError:
            pass

    if not diffs:
        return None
    return min(diffs.items(), key=lambda x: x[1])[0]

def find_7z():
    base = os.path.dirname(os.path.abspath(__file__))
    if platform.system().lower().startswith("win"):
        return os.path.join(base, "tools", "7zip", "7za.exe")
    else:
        return os.path.join(base, "tools", "7zip", "7z")

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Классификация одного .txt файла по .7z-ядрам"
    )
    p.add_argument("-c", "--cores",   required=True,
                   help="Папка с .7z-архивами ядер (имя архива = категория)")
    p.add_argument("-i", "--input",   required=True,
                   help="Текстовый файл для классификации (.txt)")
    p.add_argument("-w", "--workers", type=int, default=None,
                   help="(опционально) число потоков")
    args = p.parse_args()

    cores_folder = args.cores
    text_file    = args.input
    workers      = args.workers

    if not os.path.isdir(cores_folder):
        sys.exit(f"ERROR: cores-folder не найден: {cores_folder}")
    if not os.path.isfile(text_file) or not text_file.lower().endswith(".txt"):
        sys.exit(f"ERROR: input должен быть .txt и существовать: {text_file}")

    zip_tool = find_7z()
    if not os.path.isfile(zip_tool):
        sys.exit(f"ERROR: не найден 7z по пути: {zip_tool}")

    zip_cores = {
        os.path.splitext(f)[0]: os.path.join(cores_folder, f)
        for f in os.listdir(cores_folder)
        if f.lower().endswith(".7z")
    }
    if not zip_cores:
        sys.exit(f"ERROR: в {cores_folder} нет .7z-файлов")

    predicted = classify_text_with_zips(zip_tool, zip_cores, text_file, workers)
    if predicted:
        print(predicted)
        sys.exit(0)
    else:
        print("Не удалось определить тему.")
        sys.exit(2)
