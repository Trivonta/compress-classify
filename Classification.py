import os
import subprocess
import shutil
import logging
import sys
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    filename='classification2.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def get_archive_size(zip_tool_path, zip_core):
    try:
        return os.path.getsize(zip_core)
    except Exception as e:
        logger.error(f"Ошибка при получении размера архива {zip_core}: {e}")
        return None

def compress_text_and_get_diff(zip_tool_path, zip_core, text_file, temp_archive):
    try:
        shutil.copy(zip_core, temp_archive)
        initial_size = os.path.getsize(temp_archive)
        subprocess.run([
            zip_tool_path,
            "a",
            temp_archive,
            text_file
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        new_size = os.path.getsize(temp_archive)
        return new_size - initial_size
    except Exception as e:
        logger.error(f"Ошибка при добавлении текста в архив {temp_archive}: {e}")
        return None

def classify_text_with_zips(zip_tool_path, zip_cores, text_file, max_workers=None):
    temp_archives = []
    diffs = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_cat = {}
        for category, zip_core in zip_cores.items():
            temp_archive = f"temp_{category}.7z"
            temp_archives.append(temp_archive)
            future = executor.submit(
                compress_text_and_get_diff,
                zip_tool_path, zip_core, text_file, temp_archive
            )
            future_to_cat[future] = category

        for future in as_completed(future_to_cat):
            cat = future_to_cat[future]
            diff = future.result()
            if diff is not None:
                diffs[cat] = diff

    for ta in temp_archives:
        try:
            if os.path.exists(ta):
                os.remove(ta)
        except Exception as e:
            logger.warning(f"Не удалось удалить {ta}: {e}")

    if not diffs:
        logger.warning(f"Нет результатов для {text_file}")
        return None

    sorted_diffs = sorted(diffs.items(), key=lambda x: x[1])
    logger.info(f"Результаты для '{os.path.basename(text_file)}':")
    for cat, diff in sorted_diffs:
        logger.info(f"    {cat}: +{diff} байт")
    best = sorted_diffs[0][0]
    return best

def classify_texts(root_folder, cores_folder, zip_tool_path):
    zip_cores = {
        os.path.splitext(f)[0]: os.path.join(cores_folder, f)
        for f in os.listdir(cores_folder) if f.endswith(".7z")
    }

    total = 0
    correct = 0
    per_cat_total = {}
    per_cat_correct = {}

    for true_cat in os.listdir(root_folder):
        cat_path = os.path.join(root_folder, true_cat)
        if not os.path.isdir(cat_path):
            continue

        for fname in os.listdir(cat_path):
            if not fname.endswith(".txt"):
                continue
            text_file = os.path.join(cat_path, fname)
            predicted = classify_text_with_zips(zip_tool_path, zip_cores, text_file)

            per_cat_total.setdefault(true_cat, 0)
            per_cat_total[true_cat] += 1
            total += 1

            if predicted == true_cat:
                correct += 1
                per_cat_correct.setdefault(true_cat, 0)
                per_cat_correct[true_cat] += 1

    overall_acc = (correct / total * 100) if total else 0.0
    logger.info(f"Всего файлов: {total}, Правильно: {correct}, "
                f"Общая точность: {overall_acc:.2f}%")

    acc_per_cat = {
        cat: (per_cat_correct.get(cat, 0) / cnt * 100)
        for cat, cnt in per_cat_total.items()
    }
    for cat, acc in sorted(acc_per_cat.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"    {cat}: {acc:.2f}%")

if __name__ == "__main__":
    ROOT_FOLDER = "Articless"
    CORES_FOLDER = "Cores"
    if platform.system() == "Windows":
        ZIP_TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "7zip", "7z.exe")
    else:
        ZIP_TOOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "7zip", "7z")
    classify_texts(ROOT_FOLDER, CORES_FOLDER, ZIP_TOOL)

