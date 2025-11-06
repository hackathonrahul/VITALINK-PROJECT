from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

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