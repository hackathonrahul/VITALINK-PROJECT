
from flask import Flask, render_template, request, redirect, url_for
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

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == '123':
            # redirect to the dashboard view (function name 'dashboard')
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid credentials. Please try again."
    return render_template('login.html', error=error)

@app.route('/vitalink')
def dashboard():
    return render_template('vitalink.html')


@app.route('/bookdoctor', methods=['GET', 'POST'])
def bookdoctor():
    if request.method == 'POST':
        # grab fields and redirect to the appointment confirmation page (Post-Redirect-Get)
        name = request.form.get('name')
        date = request.form.get('date')
        # In a real app you'd persist this booking. For now redirect and show confirmation.
        return redirect(url_for('appointment', name=name, date=date))
    return render_template('bookdoctor.html')


@app.route('/appointment')
def appointment():
    # Read confirmation data from query params (set by the POST redirect)
    name = request.args.get('name', 'Patient')
    date = request.args.get('date', '')
    return render_template('book doctor/appointment.html', name=name, date=date)

@app.route('/wellnessclasses')
def wellnessclasses():
    return render_template('wellnessclasses.html')


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
                    # Check that the tesseract binary is available before calling pytesseract
                    tpath = _get_tesseract_path()
                    if not tpath:
                        error = ("Tesseract is not installed or it's not in your PATH. "
                                 "Install tesseract-ocr (see README) or set TESSERACT_CMD env var.")
                    else:
                        # Explicitly point pytesseract to the binary we found
                        pytesseract.pytesseract.tesseract_cmd = tpath
                        img = Image.open(path)
                        extracted_text = pytesseract.image_to_string(img)
            except Exception as e:
                error = f"Failed to process file: {str(e)}"
        else:
            error = "Invalid file type. Only PDF or image files allowed."
    # Note: template filename is `healthReport.html` in templates/ directory
    return render_template('healthReport.html', extracted_text=extracted_text, error=error)

@app.route('/yoga', methods=['GET', 'POST'])
def yoga():
    if request.method == 'POST':
        name = request.form.get('name')
        date = request.form.get('date')
        # read the selected class from the posted form (fallback to Yoga)
        selected_class = request.form.get('class', 'Yoga')
        return render_template('wellness/yoga.html', name=name, date=date, selected_class=selected_class)
    # GET: show the page; default selected_class is Yoga
    return render_template('wellness/yoga.html', selected_class='Yoga')

if __name__ == '__main__':
    app.run(debug=True) 