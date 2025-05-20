import os
import shutil
import argparse
from random import sample

def move_files_with_limit(source_dir: str, target_dir: str, files_per_folder: int):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    for folder_name in os.listdir(source_dir):
        folder_path = os.path.join(source_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        files = [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f))
        ]
        if not files:
            continue

        files_to_move = sample(files, min(files_per_folder, len(files)))
        target_folder_path = os.path.join(target_dir, folder_name)
        os.makedirs(target_folder_path, exist_ok=True)

        for file_name in files_to_move:
            shutil.move(
                os.path.join(folder_path, file_name),
                os.path.join(target_folder_path, file_name)
            )

        print(f"Перенесено {len(files_to_move)} файлов из '{folder_name}' → '{target_folder_path}'.")

def main():
    parser = argparse.ArgumentParser(
        description="Переносит указанное количество файлов из каждой папки-источника в целевую папку."
    )
    parser.add_argument(
        "files_per_folder",
        type=int,
        nargs="?",
        default=1,
        help="Максимальное число файлов для переноса из каждой папки (по умолчанию 1)."
    )
    parser.add_argument(
        "source_directory",
        nargs="?",
        default="Articless",
        help="Директория-источник с подкаталогами (по умолчанию 'Articless')."
    )
    parser.add_argument(
        "target_directory",
        nargs="?",
        default="Articless2",
        help="Целевая директория для переноса (по умолчанию 'Articless2')."
    )
    args = parser.parse_args()

    move_files_with_limit(
        source_dir=args.source_directory,
        target_dir=args.target_directory,
        files_per_folder=args.files_per_folder
    )

if __name__ == "__main__":
    main()