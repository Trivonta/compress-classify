import os
import subprocess
import sys
import platform
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_FOLDER = os.path.join(SCRIPT_DIR, "Articless2")
OUT_FOLDER = os.path.join(SCRIPT_DIR, "Cores")
os.makedirs(OUT_FOLDER, exist_ok=True)

if platform.system() == "Windows":
    ZIP_TOOL = os.path.join(SCRIPT_DIR, "tools", "7zip", "7z.exe")
else:
    ZIP_TOOL = os.path.join(SCRIPT_DIR, "tools", "7zip", "7z")

if not os.path.isdir(ROOT_FOLDER):
    sys.exit(f"Не найдена папка категорий: {ROOT_FOLDER}")

if not os.path.isfile(ZIP_TOOL):
    sys.exit(f"Не найден 7-Zip по пути: {ZIP_TOOL}")

def create_7zip_for_each_folder(src_root, dst_root, zip_tool_path):
    for entry in os.listdir(src_root):
        folder_path = os.path.join(src_root, entry)
        if not os.path.isdir(folder_path):
            continue

        zip_file = os.path.join(dst_root, f"{entry}.7z")
        print(f"Архивируем «{folder_path}» - «{zip_file}»…")

        try:
            subprocess.run(
                [zip_tool_path, "a", "-t7z", zip_file, os.path.join(folder_path, "*")],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            print(f"  Архив создан: {zip_file}")
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode(errors="ignore").strip()
            print(f"  Ошибка при архивировании «{entry}»: {err}")
            continue
        except Exception as ex:
            print(f"  Непредвиденная ошибка для «{entry}»: {ex}")
            continue

        try:
            shutil.rmtree(folder_path)
            print(f"  Удалена исходная папка: {folder_path}")
        except Exception as ex:
            print(f"  Не удалось удалить папку «{folder_path}»: {ex}")

if __name__ == "__main__":
    print(f"Исходная папка:  {ROOT_FOLDER}")
    print(f"Папка для архивов: {OUT_FOLDER}")
    create_7zip_for_each_folder(ROOT_FOLDER, OUT_FOLDER, ZIP_TOOL)
