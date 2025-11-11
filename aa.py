
from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
import pdfplumber
from PIL import Image
import pytesseract
import shutil
import os
import requests

app = Flask(__name__)
#added comment
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

#added nothing
@app.route('/wellnessclasses')
def wellnessclasses():
    return render_template('/wellnessclasses.html')


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
                        # Try to extract embedded text first
                        pages = [page.extract_text() or "" for page in pdf.pages]
                        extracted_text = "\n".join(pages)
                        # If no text found, fall back to rendering pages as images and OCR them
                        if not extracted_text.strip():
                                texts = []
                                # Ensure pytesseract points to the tesseract binary if available
                                tpath = _get_tesseract_path()
                                if tpath:
                                    pytesseract.pytesseract.tesseract_cmd = tpath
                                for page in pdf.pages:
                                    page_text = page.extract_text() or ""
                                    if not page_text:
                                        # Fallback: render page to an image and OCR it
                                        try:
                                            imgobj = page.to_image(resolution=300)
                                            pil_img = imgobj.original
                                            ocr = pytesseract.image_to_string(pil_img)
                                            page_text = ocr or ""
                                        except Exception:
                                            # If rendering/OCR fails, keep page_text empty
                                            page_text = page_text
                                    texts.append(page_text)
                                extracted_text = "\n".join(texts)
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


def _generate_simple_reply(user_input: str) -> str:
    """Very small, local reply generator for demo/chat placeholder.

    This is intentionally simple — replace with a real AI integration
    or external API when available.
    """
    text = (user_input or "").strip()
    if not text:
        return "I'm here to help — tell me your symptom or question."
    l = text.lower()
    if any(g in l for g in ("hi", "hello", "hey")):
        return "Hi! Tell me about your symptom and I'll try to help or suggest next steps."
    if any(k in l for k in ("fever", "cough", "cold", "temperature")):
        return ("If you're experiencing fever or cough, monitor your temperature, rest, "
                "stay hydrated, and seek medical advice if symptoms worsen.")
    if any(k in l for k in ("pain", "ache", "hurt")):
        return "For pain management, consider rest and OTC analgesics if appropriate — consult a provider for persistent pain."
    # default echo-like helpful reply
    return f"You said: {text}. For specific medical guidance, consult a healthcare professional."


@app.route('/chat_ai', methods=['POST'])
def chat_ai():
    """Handle AI chat form POSTs. Renders a simple `chat.html` showing question + reply.

    This endpoint is intentionally minimal and synchronous. Swap in an async
    external AI call if needed.
    """
    user_input = request.form.get('user_input', '').strip()
    if not user_input:
        return redirect(url_for('dashboard'))
    reply = _generate_simple_reply(user_input)
    return render_template('chat.html', question=user_input, reply=reply)

@app.route('/zumba', methods=['GET', 'POST'])
def zumba():
    if request.method == 'POST':
        name = request.form.get('name')
        date = request.form.get('date')
        # read the selected class from the posted form (fallback to Yoga)
        selected_class = request.form.get('class', 'zumba')
        return render_template('wellness/yoga.html', name=name, date=date, selected_class=selected_class)
    # GET: show the page; default selected_class is zumba
    return render_template('wellness/yoga.html', selected_class='zumba')

@app.route('/Meditation', methods=['GET', 'POST'])
def Meditation():
    if request.method == 'POST':
        name = request.form.get('name')
        date = request.form.get('date')
        # read the selected class from the posted form (fallback to Yoga)
        selected_class = request.form.get('class', 'Meditation')
        return render_template('wellness/yoga.html', name=name, date=date, selected_class=selected_class)
    # GET: show the page; default selected_class is Meditation
    return render_template('wellness/yoga.html', selected_class='Meditation')

@app.route('/Fitness', methods=['GET', 'POST'])
def Fitness():
    if request.method == 'POST':
        name = request.form.get('name')
        date = request.form.get('date')
        # read the selected class from the posted form (fallback to Yoga)
        selected_class = request.form.get('class', 'Fitness')
        return render_template('wellness/yoga.html', name=name, date=date, selected_class=selected_class)
    # GET: show the page; default selected_class is Fitness
    return render_template('wellness/yoga.html', selected_class='Fitness')

    
@app.route('/wellness')
def wellness():
    return render_template('wellness/wellness.html')


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    """Render chat interface and forward queries to Infermedica-like API.

    Uses environment variables INFERMEDICA_APP_ID and INFERMEDICA_APP_KEY. If
    those are not set, the route will return a helpful error message.
    """
    ai_response = None
    error = None
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        # Read API credentials from environment
        INFERMEDICA_APP_ID = os.environ.get('INFERMEDICA_APP_ID')
        INFERMEDICA_APP_KEY = os.environ.get('INFERMEDICA_APP_KEY')

        if not INFERMEDICA_APP_ID or not INFERMEDICA_APP_KEY:
            error = "Infermedica API credentials not set. Please set INFERMEDICA_APP_ID and INFERMEDICA_APP_KEY in the environment."
        else:
            try:
                # Step 1: parse symptoms
                url_parse = 'https://api.infermedica.com/v3/parse'
                headers = {
                    'App-Id': INFERMEDICA_APP_ID,
                    'App-Key': INFERMEDICA_APP_KEY,
                    'Content-Type': 'application/json'
                }
                data_parse = {
                    "text": user_input,
                    "context": "symptoms"
                }
                resp = requests.post(url_parse, headers=headers, json=data_parse, timeout=10)
                resp.raise_for_status()
                mentions = resp.json().get('mentions', [])
                if not mentions:
                    ai_response = "Sorry, I couldn't identify any health symptoms in your input."
                else:
                    evidence = []
                    for m in mentions:
                        evidence.append({
                            'id': m.get('id'),
                            'choice_id': m.get('choice_id')
                        })
                    # Simple diagnosis call (demo): in a real app collect sex/age
                    url_diag = 'https://api.infermedica.com/v3/diagnosis'
                    data_diag = {
                        'sex': os.environ.get('DEMO_SEX', 'male'),
                        'age': int(os.environ.get('DEMO_AGE', '30')),
                        'evidence': evidence
                    }
                    diag_resp = requests.post(url_diag, headers=headers, json=data_diag, timeout=10)
                    diag_resp.raise_for_status()
                    conditions = diag_resp.json().get('conditions', [])
                    if conditions:
                        ai_response = "Possible conditions:\n" + "\n".join([f"{c['name']} ({c['probability']*100:.1f}%)" for c in conditions])
                    else:
                        ai_response = "Sorry, I could not determine any conditions from your input."
            except Exception as e:
                error = str(e)

    return render_template('chatWithAI.html', ai_response=ai_response, error=error)

if __name__ == '__main__':
    app.run(debug=True) 
 #JUST A TESTING