import subprocess
import sys

REQUIRED_PACKAGES = [
    "requests",
    "beautifulsoup4",
    "arxiv",
    "PyPDF2",
    "numpy"
]

def install_package(package_name: str):
    try:
        __import__(package_name)
    except ImportError:
        print(f"[INFO] Пакет '{package_name}' не найден — устанавливаю...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            package_name,
            "--disable-pip-version-check"
        ])
    print(f"[INFO] Обновляю пакет '{package_name}' до последней версии...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "--upgrade", package_name,
        "--disable-pip-version-check"
    ])

def main():
    for pkg in REQUIRED_PACKAGES:
        install_package(pkg)
    print("[OK] Все зависимости установлены и обновлены.")

if __name__ == "__main__":
    main()
