import os
import sys
import shutil
import subprocess
import platform
import argparse
from random import sample

def move_and_archive(source_dir, output_dir, files_per_category):
    if platform.system() == "Windows":
        zip_tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "7zip", "7za.exe")
    else:
        zip_tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "7zip", "7z")
    os.makedirs(output_dir, exist_ok=True)

    for category in os.listdir(source_dir):
        cat_path = os.path.join(source_dir, category)
        if not os.path.isdir(cat_path):
            continue

        files = [f for f in os.listdir(cat_path) if os.path.isfile(os.path.join(cat_path, f))]
        if not files:
            print(f"Skipping empty category: {category}")
            continue

        num_to_move = min(files_per_category, len(files))
        to_move = sample(files, num_to_move)

        staging_folder = os.path.join(output_dir, category)
        os.makedirs(staging_folder, exist_ok=True)

        for fname in to_move:
            src = os.path.join(cat_path, fname)
            dst = os.path.join(staging_folder, fname)
            shutil.move(src, dst)
        print(f"Moved {num_to_move} files from '{category}' to staging.")

        archive_path = os.path.join(output_dir, f"{category}.7z")
        print(f"Archiving '{staging_folder}' -> '{archive_path}'...")
        try:
            subprocess.run(
                [zip_tool, "a", "-t7z", archive_path, os.path.join(staging_folder, "*")],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            print(f"Archive created: {archive_path}")
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode(errors="ignore").strip()
            print(f"Error archiving '{category}': {err}")
            continue

        try:
            shutil.rmtree(staging_folder)
            print(f"Removed staging folder: {staging_folder}")
        except Exception as ex:
            print(f"Could not remove staging folder '{staging_folder}': {ex}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="..."
    )
    parser.add_argument(
        '-n', '--number', type=int, required=True,
        help="..."
    )
    parser.add_argument(
        '-s', '--source', type=str, required=True,
        help="..."
    )
    parser.add_argument(
        '-o', '--output', type=str, required=True,
        help="..."
    )
    args = parser.parse_args()

    if not os.path.isdir(args.source):
        sys.exit(f"...")

    move_and_archive(args.source, args.output, args.number)
