from flask import Flask, render_template, request
import requests

app = Flask(__name__)

education_mapping = {
    'No high school degree': 1,
    'Bachelor degree': 2,
    'Master degree': 3,
    'PhD': 4
}

occupation_mapping = {
    'Entrepreneur': 1,
    'Managerial': 2,
    'Salarial': 3,
    'Unemployed': 4
}


@app.route('/')
def index():
    return render_template('form.html', step=1)  # Pass step=1 for the form page


@app.route('/submit', methods=['POST'])
def submit():
    # Capture the form data
    age = request.form['age']
    education = request.form['education']
    occupation = request.form['occupation']
    kids = request.form['kids']
    income = request.form['income']
    net_worth = request.form['net_worth_income']
    risk = request.form['risk']
    married = request.form['married']

    # Encode education and occupation using the defined mappings
    education_encoded = education_mapping.get(education, 0)
    occupation_encoded = occupation_mapping.get(occupation, 0)

    # Prepare the payload to send to FastAPI microservice
    payload = {
        'age': float(age),
        'education': education_encoded,
        'occupation': occupation_encoded,
        'kids': float(kids),
        'income': float(income),
        'net_worth': float(net_worth),
        'risk': int(risk),
        'married': int(married)
    }

    fastapi_url = 'http://fastapi-service:8000/predict/'

    try:
        # Send the POST request to FastAPI
        response = requests.post(fastapi_url, json=payload)
        prediction = response.json()
        risk_aversion_estimate = prediction.get('risk_aversion_estimate', 'Not available')
        return render_template('result.html', risk_aversion_estimate=risk_aversion_estimate, step=2)  # Pass step=2 for the result page
    except Exception as e:
        return f"An error occurred: {e}"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
