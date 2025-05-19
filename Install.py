import subprocess
import sys

REQUIRED_PACKAGES = [
    "requests",
    "beautifulsoup4",
    "arxiv",
    "PyPDF2",
    "numpy"
]

def ensure_up_to_date(package_name: str):
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "--upgrade", package_name,
        "--disable-pip-version-check"
    ])

def main():
    for pkg in REQUIRED_PACKAGES:
        ensure_up_to_date(pkg)

if __name__ == "__main__":
    main()