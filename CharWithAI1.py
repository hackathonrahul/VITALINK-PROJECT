import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# Replace these with your Infermedica API credentials
INFERMEDICA_APP_ID = 'your_app_id'
INFERMEDICA_APP_KEY = 'your_app_key'

@app.route('/chat_ai', methods=['GET', 'POST'])
def chat_ai():
    ai_response = None
    error = None

    if request.method == 'POST':
        user_input = request.form.get('user_input')
        # Step 1: parse symptoms (using Infermedica's /parse endpoint)
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
        try:
            response = requests.post(url_parse, headers=headers, json=data_parse)
            response.raise_for_status()
            mentions = response.json().get("mentions", [])
            if not mentions:
                ai_response = "Sorry, I couldn't identify any health symptoms in your input."
            else:
                # Compose Evidence for /diagnosis
                evidence = []
                for m in mentions:
                    evidence.append({
                        "id": m['id'],
                        "choice_id": m['choice_id']  # usually "present"
                    })
                # For a real system, you would need to keep track of session/question state and user sex/age
                url_diag = 'https://api.infermedica.com/v3/diagnosis'
                data_diag = {
                    "sex": "male",  # Or ask user for their gender
                    "age": 30,      # Or ask user for their age
                    "evidence": evidence
                }
                diag_response = requests.post(url_diag, headers=headers, json=data_diag)
                diag_response.raise_for_status()
                conditions = diag_response.json().get("conditions", [])
                if conditions:
                    ai_response = "Possible conditions:\n" + "\n".join([f"{c['name']} ({c['probability']*100:.1f}%)" for c in conditions])
                else:
                    ai_response = "Sorry, I could not determine any conditions from your input."
        except Exception as e:
            error = str(e)

    return render_template('chat_ai.html', ai_response=ai_response, error=error)
