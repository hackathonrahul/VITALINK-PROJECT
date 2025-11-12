from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, send_from_directory
import os
from werkzeug.utils import secure_filename
import pdfplumber
from PIL import Image
import pytesseract
import shutil
import os
import requests
import json
from datetime import datetime
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
#added comment
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['APPOINTMENTS_FILE'] = 'appointments.json'
app.config['USERS_FILE'] = 'users.json'
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret-please-change')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _load_appointments():
    """Load appointments from JSON file."""
    if os.path.exists(app.config['APPOINTMENTS_FILE']):
        try:
            with open(app.config['APPOINTMENTS_FILE'], 'r') as f:
                return json.load(f)
        except:
            # Attempt a simple repair: if file is truncated, try appending a closing bracket
            try:
                with open(app.config['APPOINTMENTS_FILE'], 'a') as f:
                    f.write('\n]')
                with open(app.config['APPOINTMENTS_FILE'], 'r') as f2:
                    return json.load(f2)
            except Exception:
                return []
    return []


def _load_users():
    """Load users from JSON file."""
    p = app.config.get('USERS_FILE')
    if p and os.path.exists(p):
        try:
            with open(p, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_user(user):
    p = app.config.get('USERS_FILE')
    users = _load_users()
    users.append(user)
    temp = p + '.tmp'
    with open(temp, 'w') as f:
        json.dump(users, f, indent=2)
    os.replace(temp, p)


def _update_user(user_id, updates: dict):
    """Update an existing user by id with fields from updates dict.

    Returns True if updated, False if user not found.
    """
    p = app.config.get('USERS_FILE')
    users = _load_users()
    changed = False
    for u in users:
        if u.get('id') == user_id:
            # update allowed fields only
            for k, v in updates.items():
                if k in ('name', 'email', 'phone'):
                    u[k] = v
            changed = True
            break
    if changed:
        temp = p + '.tmp'
        with open(temp, 'w') as f:
            json.dump(users, f, indent=2)
        os.replace(temp, p)
    return changed


def _find_user_by_username(username):
    for u in _load_users():
        if u.get('username') == username:
            return u
    return None


def _get_user_by_id(uid):
    for u in _load_users():
        if u.get('id') == uid:
            return u
    return None


def _save_appointment(appointment):
    """Save a new appointment to the JSON file."""
    # Write atomically to avoid truncation / concurrent write issues
    appointments = _load_appointments()
    appointments.append(appointment)
    temp_path = app.config['APPOINTMENTS_FILE'] + '.tmp'
    with open(temp_path, 'w') as f:
        json.dump(appointments, f, indent=2)
    # Replace the original file
    os.replace(temp_path, app.config['APPOINTMENTS_FILE'])


def _get_day_name(date_str):
    """Convert date string (YYYY-MM-DD) to day name (e.g., 'Monday')."""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%A')
    except:
        return ""


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
    # If user is already logged in, redirect to dashboard
    if session.get('user_id'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Distinguish between register and login actions by a hidden field
        action = request.form.get('action')
        if action == 'register':
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                error = 'Username and password are required for registration.'
            elif _find_user_by_username(username):
                error = 'Username already exists. Choose another.'
            else:
                uid = str(uuid4())
                user = {
                    'id': uid,
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'username': username,
                    'password_hash': generate_password_hash(password)
                }
                _save_user(user)
                session['user_id'] = uid
                return redirect(url_for('dashboard'))
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            # admin fallback
            if username == 'admin' and password == '123':
                session['user_id'] = 'admin'
                return redirect(url_for('dashboard'))
            user = _find_user_by_username(username)
            if not user or not check_password_hash(user.get('password_hash', ''), password):
                error = 'Invalid username or password.'
            else:
                session['user_id'] = user.get('id')
                return redirect(url_for('dashboard'))

    return render_template('login.html', error=error)

@app.route('/vitalink')
def dashboard():
    # Load appointments and pass to template
    all_appointments = _load_appointments()
    # Sort by date (empty dates sort first)
    all_appointments.sort(key=lambda x: x.get('date', '') or '')

    current_user = None
    my_appointments = []
    other_appointments = []
    
    uid = session.get('user_id')
    if uid:
        if uid == 'admin':
            # admin sees everything
            current_user = {'id': 'admin', 'name': 'Administrator', 'email': ''}
            my_appointments = all_appointments
            other_appointments = []
        else:
            current_user = _get_user_by_id(uid)
            # Separate user's appointments from others
            my_appointments = [a for a in all_appointments if a.get('user_id') == uid]
            other_appointments = [a for a in all_appointments if a.get('user_id') != uid]
    else:
        # not logged in: no personal appointments
        my_appointments = []
        other_appointments = []

    return render_template('vitalink.html', 
                         my_appointments=my_appointments, 
                         other_appointments=other_appointments,
                         current_user=current_user)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """Show and allow editing of the logged-in user's profile (name, email).

    Admin is shown a read-only profile.
    """
    uid = session.get('user_id')
    if not uid:
        return redirect(url_for('login'))

    if uid == 'admin':
        current_user = {'id': 'admin', 'name': 'Administrator', 'email': ''}
        if request.method == 'POST':
            flash('Administrator profile cannot be edited here.')
            return redirect(url_for('profile'))
        return render_template('profile.html', current_user=current_user)

    current_user = _get_user_by_id(uid)
    if not current_user:
        flash('User not found. Please log in again.')
        session.pop('user_id', None)
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        updates = {}
        if name:
            updates['name'] = name
        if email:
            updates['email'] = email
        if phone:
            updates['phone'] = phone
        if updates:
            ok = _update_user(uid, updates)
            if ok:
                flash('Profile updated.')
                # refresh current_user from storage
                current_user = _get_user_by_id(uid)
            else:
                flash('Failed to update profile.')
        else:
            flash('No changes submitted.')
        return redirect(url_for('profile'))

    return render_template('profile.html', current_user=current_user)


@app.route('/bookdoctor', methods=['GET', 'POST'])
def bookdoctor():
    if request.method == 'POST':
        # grab fields and save appointment
        name = request.form.get('name')
        date = request.form.get('date')
        reason = request.form.get('reason', '')
        
        # Save to appointments.json
        appointment = {
            'type': 'doctor',
            'name': name,
            'date': date,
            'day': _get_day_name(date),
            'reason': reason,
            'user_id': session.get('user_id'),
            'timestamp': datetime.now().isoformat()
        }
        _save_appointment(appointment)
        
        # Redirect to confirmation with params
        return redirect(url_for('appointment', name=name, date=date))
    return render_template('bookdoctor.html')


@app.route('/appointment')
def appointment():
    # Read confirmation data from query params (set by the POST redirect)
    name = request.args.get('name', 'Patient')
    date = request.args.get('date', '')
    
    # Load and display all appointments from appointments.json
    all_appointments = _load_appointments()
    all_appointments.sort(key=lambda x: x.get('date', '') or '', reverse=True)
    
    return render_template('book doctor/appointment.html', 
                         name=name, 
                         date=date, 
                         appointments=all_appointments)

#added nothing
@app.route('/wellnessclasses')
def wellnessclasses():
    return render_template('/wellnessclasses.html')


@app.route('/book_wellness', methods=['GET', 'POST'])
def book_wellness():
    # Dedicated booking page for a single wellness class. cls is passed as query param.
    cls = request.args.get('cls', '')
    if request.method == 'POST':
        name = request.form.get('name')
        date = request.form.get('date')
        class_name = request.form.get('class') or request.form.get('class_name') or cls

        appointment = {
            'type': 'wellness',
            'name': name,
            'date': date,
            'day': _get_day_name(date),
            'class_name': class_name,
            'user_id': session.get('user_id'),
            'timestamp': datetime.now().isoformat()
        }
        _save_appointment(appointment)
        # Render a simple confirmation page (reuse existing wellness success template)
        return render_template('wellness/yoga.html', name=name, date=date, selected_class=class_name)

    # GET: show booking form with class prefilled
    return render_template('book_wellness.html', cls=cls)


@app.route('/health_report', methods=['GET', 'POST'])
def health_report():
    extracted_text = None
    error = None
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Save uploads under a per-user folder when possible so users can
            # access their own previous uploads.
            user_id = session.get('user_id') or 'anonymous'
            user_dir = os.path.join(app.config['UPLOAD_FOLDER'], user_id)
            os.makedirs(user_dir, exist_ok=True)
            path = os.path.join(user_dir, filename)
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
    # Build a per-user list of past uploaded reports (file name + relative URL)
    user_id = session.get('user_id') or 'anonymous'
    user_dir = os.path.join(app.config['UPLOAD_FOLDER'], user_id)
    past_reports = []
    if os.path.exists(user_dir):
        for fname in sorted(os.listdir(user_dir), key=lambda f: os.path.getmtime(os.path.join(user_dir, f)), reverse=True):
            fpath = os.path.join(user_dir, fname)
            if os.path.isfile(fpath):
                past_reports.append({
                    'name': fname,
                    'url': url_for('uploaded_file', filepath=f"{user_id}/{fname}"),
                    'mtime': datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat()
                })

    # Note: template filename is `healthReport.html` in templates/ directory
    return render_template('healthReport.html', extracted_text=extracted_text, error=error, past_reports=past_reports)


@app.route('/uploads/<path:filepath>')
def uploaded_file(filepath):
    # Serve uploaded files from the uploads directory, allowing subpaths for per-user files
    return send_from_directory(app.config['UPLOAD_FOLDER'], filepath)

@app.route('/yoga', methods=['GET', 'POST'])
def yoga():
    if request.method == 'POST':
        name = request.form.get('name')
        date = request.form.get('date')
        selected_class = request.form.get('class', 'Yoga')
        
        # Save to appointments.json
        appointment = {
            'type': 'wellness',
            'name': name,
            'date': date,
            'day': _get_day_name(date),
            'class_name': selected_class,
            'user_id': session.get('user_id'),
            'timestamp': datetime.now().isoformat()
        }
        _save_appointment(appointment)
        
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
        selected_class = request.form.get('class', 'Zumba')
        
        # Save to appointments.json
        appointment = {
            'type': 'wellness',
            'name': name,
            'date': date,
            'day': _get_day_name(date),
            'class_name': selected_class,
            'user_id': session.get('user_id'),
            'timestamp': datetime.now().isoformat()
        }
        _save_appointment(appointment)
        
        return render_template('wellness/yoga.html', name=name, date=date, selected_class=selected_class)
    # GET: show the page; default selected_class is zumba
    return render_template('wellness/yoga.html', selected_class='zumba')

@app.route('/Meditation', methods=['GET', 'POST'])
def Meditation():
    if request.method == 'POST':
        name = request.form.get('name')
        date = request.form.get('date')
        selected_class = request.form.get('class', 'Meditation')
        
        # Save to appointments.json
        appointment = {
            'type': 'wellness',
            'name': name,
            'date': date,
            'day': _get_day_name(date),
            'class_name': selected_class,
            'user_id': session.get('user_id'),
            'timestamp': datetime.now().isoformat()
        }
        _save_appointment(appointment)
        
        return render_template('wellness/yoga.html', name=name, date=date, selected_class=selected_class)
    # GET: show the page; default selected_class is Meditation
    return render_template('wellness/yoga.html', selected_class='Meditation')

@app.route('/mudra', methods=['GET', 'POST'])
def mudra():
    if request.method == 'POST':
        name = request.form.get('name')
        date = request.form.get('date')
        selected_class = request.form.get('class', 'mudra')
        
        # Save to appointments.json
        appointment = {
            'type': 'wellness',
            'name': name,
            'date': date,
            'day': _get_day_name(date),
            'class_name': selected_class,
            'user_id': session.get('user_id'),
            'timestamp': datetime.now().isoformat()
        }
        _save_appointment(appointment)
        
        return render_template('wellness/yoga.html', name=name, date=date, selected_class=selected_class)
    # GET: show the page; default selected_class is mudra
    return render_template('wellness/yoga.html', selected_class='mudra')

    
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
    app.run(host='0.0.0.0', port=5000, debug=True)
 