# VITALINK-PROJECT

This project uses Tesseract OCR (the native `tesseract` binary) via the Python package `pytesseract` to extract text from images. If you see an error like:

"Failed to process file: tesseract is not installed or it's not in your PATH. See README file for more information."

follow the steps below to install and configure Tesseract on Ubuntu/Debian-based systems.

## Install system packages (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y tesseract-ocr libtesseract-dev
```

Optionally install language packs (example: English):

```bash
sudo apt install -y tesseract-ocr-eng
```

## Python dependencies

Create a virtual environment and install Python packages:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt  # if present, or:
pip install Pillow pytesseract pdfplumber flask
```

## If tesseract is installed in a non-standard location

If `tesseract` is not on PATH (for example installed under `/usr/local/bin/tesseract`), set the environment variable before running the app:

```bash
export TESSERACT_CMD=/usr/local/bin/tesseract
# or set in Python: pytesseract.pytesseract.tesseract_cmd = r"/usr/local/bin/tesseract"
```

## Quick test

After installing, verify Tesseract is available:

```bash
which tesseract
# or
tesseract --version
```

If the command returns a path or a version, the binary is installed and on PATH.

## Notes

- This README was added to help with the runtime error described above.
- The app now performs a runtime check for the `tesseract` binary and will return a helpful error message in the web UI if it is missing.
