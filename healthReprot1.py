from flask import Flask, render_template, request
import os
from werkzeug.utils import secure_filename
import pdfplumber
from PIL import Image
import pytesseract

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
                    with pdfplumber.open(path) as pdf:
                        pages = [page.extract_text() or "" for page in pdf.pages]
                    extracted_text = "\n".join(pages)
                else:
                    img = Image.open(path)
                    extracted_text = pytesseract.image_to_string(img)
            except Exception as e:
                error = f"Failed to process file: {str(e)}"
        else:
            error = "Invalid file type. Only PDF or image files allowed."
    return render_template('health_report.html', extracted_text=extracted_text, error=error)

if __name__ == '__main__':
    app.run(debug=True)
