import os
import platform
import argparse
import subprocess
import tempfile
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat

def compressed_size_file(path, zip_tool):
    archive = tempfile.mktemp(suffix='.7z')
    try:
        subprocess.run([zip_tool, 'a', '-t7z', '-mx=9', archive, path],
                       capture_output=True, check=True)
        return os.path.getsize(archive) or 1
    except subprocess.CalledProcessError:
        return 1
    finally:
        if os.path.exists(archive):
            os.remove(archive)

def _compute_pair_ratio(args):
    file_j, file_i, first_j, second_i, zip_tool = args
    combo = tempfile.mktemp(suffix='.txt')
    try:
        with open(combo, 'wb') as c, open(file_j, 'rb') as a, open(file_i, 'rb') as b:
            c.write(a.read()); c.write(b.read())
        combined_size = compressed_size_file(combo, zip_tool)
        return (combined_size - first_j) / second_i if second_i > 0 else 0
    finally:
        if os.path.exists(combo):
            os.remove(combo)

def build_compression_matrix(files, zip_tool):
    n = len(files)

    with ProcessPoolExecutor() as executor:
        first = list(executor.map(compressed_size_file, files, repeat(zip_tool)))
    second = first.copy()

    args = [
        (files[j], files[i], first[j], second[i], zip_tool)
        for i in range(n) for j in range(n)
    ]

    with ProcessPoolExecutor() as executor:
        results = list(executor.map(_compute_pair_ratio, args))

    return np.array(results).reshape(n, n)

def select_core_indices(mat, k):
    idxs = list(range(mat.shape[0]))
    core = []
    m = mat.copy()
    while len(core) < k and m.size:
        avg = m.mean(axis=0)
        idx = int(np.argmin(avg))
        core.append(idxs[idx])
        m = np.delete(np.delete(m, idx, axis=0), idx, axis=1)
        del idxs[idx]
    return core

def main():
    p = argparse.ArgumentParser(description="Собрать ядра по методу компрессии")
    p.add_argument("core_size", nargs="?", type=int, default=10,
                   help="Число файлов в каждом ядре (default: 10)")
    p.add_argument("txt_folder", nargs="?", default="Articless2",
                   help="Папка с TXT-файлами по темам (default: Articless2)")
    p.add_argument("core_folder", nargs="?", default="Cores",
                   help="Куда сохранять архивы .7z (default: Cores)")
    args = p.parse_args()

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    txt_root = os.path.join(SCRIPT_DIR, args.txt_folder)
    core_root = os.path.join(SCRIPT_DIR, args.core_folder)
    os.makedirs(core_root, exist_ok=True)

    if platform.system() == "Windows":
        zip_tool = os.path.join(SCRIPT_DIR, "tools", "7zip", "7za.exe")
    else:
        zip_tool = os.path.join(SCRIPT_DIR, "tools", "7zip", "7z")

    if not os.path.isdir(txt_root) or not os.path.isfile(zip_tool):
        print("Ошибка: проверьте пути к папкам и 7-Zip")
        return

    for cat in os.listdir(txt_root):
        d = os.path.join(txt_root, cat)
        if not os.path.isdir(d):
            continue
        files = [
            os.path.join(d, f)
            for f in os.listdir(d)
            if f.lower().endswith('.txt') and os.path.getsize(os.path.join(d, f)) > 0
        ]
        if len(files) < args.core_size:
            continue

        mat = build_compression_matrix(files, zip_tool)
        core_idx = select_core_indices(mat, args.core_size)
        core_files = [files[i] for i in core_idx]

        archive = os.path.join(core_root, f"{cat}.7z")
        subprocess.run([zip_tool, 'a', '-t7z', '-mx=9', archive] + core_files, check=True)
        print(f"{cat}: создан архив {archive} из {len(core_files)} файлов")

if __name__ == "__main__":
    main()

