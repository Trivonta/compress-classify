import os
import platform
from pathlib import Path
import subprocess
import tempfile
import numpy as np
from concurrent.futures import ProcessPoolExecutor


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TXT_FOLDER = "Articless2"
CORE_FOLDER = "Cores"
CORE_SIZE = 10
if platform.system() == "Windows":
    ZIP_TOOL = os.path.join(SCRIPT_DIR, "tools", "7zip", "7z.exe")
else:
    ZIP_TOOL = os.path.join(SCRIPT_DIR, "tools", "7zip", "7z")

def compressed_size_file(path):
    archive = tempfile.mktemp(suffix='.7z')
    try:
        subprocess.run([ZIP_TOOL, 'a', '-t7z', '-mx=9', archive, path],
                       capture_output=True, check=True)
        return os.path.getsize(archive) or 1
    except subprocess.CalledProcessError:
        return 1
    finally:
        if os.path.exists(archive): os.remove(archive)

def _compute_pair_ratio(args):
    file_j, file_i, first_j, second_i = args
    combo = tempfile.mktemp(suffix='.txt')
    try:
        with open(combo, 'wb') as c, open(file_j, 'rb') as a, open(file_i, 'rb') as b:
            c.write(a.read()); c.write(b.read())
        combined_size = compressed_size_file(combo)
        return (combined_size - first_j) / second_i if second_i > 0 else 0
    finally:
        if os.path.exists(combo): os.remove(combo)

def build_compression_matrix(files):
    n = len(files)
    with ProcessPoolExecutor() as executor:
        first = list(executor.map(compressed_size_file, files))
        second = first.copy()
        args = [ (files[j], files[i], first[j], second[i])
                 for i in range(n) for j in range(n) ]
        results = list(executor.map(_compute_pair_ratio, args))
    mat = np.array(results).reshape(n, n)
    return mat

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

if __name__ == '__main__':
    if not os.path.isdir(TXT_FOLDER) or not os.path.isfile(ZIP_TOOL): exit(1)
    os.makedirs(CORE_FOLDER, exist_ok=True)
    for cat in os.listdir(TXT_FOLDER):
        d = os.path.join(TXT_FOLDER, cat)
        if not os.path.isdir(d): continue
        files = [os.path.join(d, f) for f in os.listdir(d)
                 if f.lower().endswith('.txt') and os.path.getsize(os.path.join(d, f))]
        if len(files) < CORE_SIZE: continue
        mat = build_compression_matrix(files)
        core_idx = select_core_indices(mat, CORE_SIZE)
        core_files = [files[i] for i in core_idx]
        archive = os.path.join(CORE_FOLDER, f"{cat}.7z")
        subprocess.run([ZIP_TOOL, 'a', '-t7z', '-mx=9', archive] + core_files)
        print(f"{cat}: создан архив {archive} из {len(core_files)} файлов")
