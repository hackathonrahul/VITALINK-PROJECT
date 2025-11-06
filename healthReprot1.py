from flask import Flask, render_template, request
import os
from werkzeug.utils import secure_filename
import pdfplumber
from PIL import Image
import pytesseract
import shutil
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _get_tesseract_path():
    """Return the tesseract binary path if available.

    Priority:
    - Environment variable TESSERACT_CMD if set and executable
    - which('tesseract') on PATH
    Returns None if not found.
    """
    env = os.environ.get('TESSERACT_CMD')
    if env and os.path.isfile(env) and os.access(env, os.X_OK):
        return env
    return shutil.which('tesseract')

@app.route('/health_report', methods=['GET', 'POST'])
def health_report():
    extracted_text = None
    error = None
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            ext = filename.rsplit('.', 1)[1].lower()
            try:
                if ext == 'pdf':
                    texts = []
                    # Ensure pytesseract points to the tesseract binary if available
                    tpath = _get_tesseract_path()
                    if tpath:
                        pytesseract.pytesseract.tesseract_cmd = tpath
                    with pdfplumber.open(path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text() or ""
                            if not page_text:
                                try:
                                    imgobj = page.to_image(resolution=300)
                                    pil_img = imgobj.original
                                    ocr = pytesseract.image_to_string(pil_img)
                                    page_text = ocr or ""
                                except Exception:
                                    page_text = page_text
                            texts.append(page_text)
                    extracted_text = "\n".join(texts)
                else:
                    tpath = _get_tesseract_path()
                    if not tpath:
                        error = ("Tesseract is not installed or it's not in your PATH. "
                                 "Install tesseract-ocr (see README) or set TESSERACT_CMD env var.")
                    else:
                        pytesseract.pytesseract.tesseract_cmd = tpath
                        img = Image.open(path)
                        extracted_text = pytesseract.image_to_string(img)
            except Exception as e:
                error = f"Failed to process file: {str(e)}"
        else:
            error = "Invalid file type. Only PDF or image files allowed."
    return render_template('health_report.html', extracted_text=extracted_text, error=error)

if __name__ == '__main__':
    app.run(debug=True)
