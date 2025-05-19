import os
import shutil
from random import sample

def move_files_with_limit(source_dir, target_dir, files_per_folder):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    for folder_name in os.listdir(source_dir):
        folder_path = os.path.join(source_dir, folder_name)

        if not os.path.isdir(folder_path):
            continue

        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        if not files:
            continue

        files_to_move = sample(files, min(files_per_folder, len(files)))

        target_folder_path = os.path.join(target_dir, folder_name)
        if not os.path.exists(target_folder_path):
            os.makedirs(target_folder_path)

        for file_name in files_to_move:
            source_file_path = os.path.join(folder_path, file_name)
            target_file_path = os.path.join(target_folder_path, file_name)
            shutil.move(source_file_path, target_file_path)

        print(f"Перенесено {len(files_to_move)} файлов из папки '{folder_name}' в '{target_folder_path}'.")

source_directory = 'Articless'
target_directory = 'Articless2'
files_per_folder_to_move = 1

move_files_with_limit(source_directory, target_directory, files_per_folder_to_move)
