# app.py
from flask import Flask, request, render_template
import joblib
import numpy as np

app = Flask(__name__)
model = joblib.load('logistic_model.pkl')
scaler = joblib.load('scaler.pkl')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    features = [float(x) for x in request.form.values()]
    final_features = scaler.transform([features])
    prediction = model.predict(final_features)
    return render_template('index.html', result='Malignant' if prediction[0] == 1 else 'Benign')

if __name__ == "__main__":
    app.run(debug=True)
