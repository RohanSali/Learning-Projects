import joblib
import numpy as np

# Load model and scaler
model = joblib.load('logistic_model.pkl')
scaler = joblib.load('scaler.pkl')

# Example: replace this with your own data (same order and shape as training data)
# 30 feature values as in the original dataset
input_data = [15.1, 20.5, 98.6, 700.0, 0.12, 0.23, 0.14, 0.09, 0.19, 0.07,
              0.35, 1.2, 2.4, 25.0, 0.007, 0.04, 0.05, 0.015, 0.02, 0.003,
              16.5, 22.4, 105.0, 850.0, 0.14, 0.3, 0.25, 0.1, 0.25, 0.08, 0.001]

# Scale the data
input_scaled = scaler.transform([input_data])

# Make prediction
prediction = model.predict(input_scaled)

# Output result
print("Prediction:", "Malignant" if prediction[0] == 1 else "Benign")