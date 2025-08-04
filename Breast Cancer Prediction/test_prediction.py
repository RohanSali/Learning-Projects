import joblib
import numpy as np
import pandas as pd

# Load the model and scaler
model = joblib.load('logistic_model.pkl')
scaler = joblib.load('scaler.pkl')

# Load the dataset
df = pd.read_csv('data.csv')
if df.columns[-1].startswith('Unnamed'):
    df = df.iloc[:, :-1]

# Get feature columns (excluding diagnosis and id)
feature_columns = [col for col in df.columns if col not in ['diagnosis', 'id']]

# Test with first row from dataset
test_features = df.iloc[0][feature_columns].values
test_id = df.iloc[0]['id']

# Prepare features (add ID as first feature)
features = [test_id] + list(test_features)

print(f"Test features shape: {len(features)}")
print(f"Features: {features[:5]}...")  # Show first 5 features

# Make prediction
features_array = np.array(features).reshape(1, -1)
scaled_features = scaler.transform(features_array)
prediction = model.predict(scaled_features)[0]
prediction_proba = model.predict_proba(scaled_features)[0]

print(f"Raw prediction: {prediction}")
print(f"Prediction probabilities: {prediction_proba}")

# Get prediction label and confidence
if prediction == 1:
    result = "Malignant"
    confidence = prediction_proba[1] * 100
else:
    result = "Benign"
    confidence = prediction_proba[0] * 100

print(f"Final result: {result}")
print(f"Confidence: {confidence:.2f}%")

# Test with a benign case (if available)
benign_cases = df[df['diagnosis'] == 'B']
if len(benign_cases) > 0:
    print("\n--- Testing with benign case ---")
    benign_features = benign_cases.iloc[0][feature_columns].values
    benign_id = benign_cases.iloc[0]['id']
    
    benign_input = [benign_id] + list(benign_features)
    benign_array = np.array(benign_input).reshape(1, -1)
    benign_scaled = scaler.transform(benign_array)
    benign_pred = model.predict(benign_scaled)[0]
    benign_proba = model.predict_proba(benign_scaled)[0]
    
    print(f"Benign case prediction: {benign_pred}")
    print(f"Benign case probabilities: {benign_proba}")
    
    if benign_pred == 1:
        benign_result = "Malignant"
        benign_confidence = benign_proba[1] * 100
    else:
        benign_result = "Benign"
        benign_confidence = benign_proba[0] * 100
    
    print(f"Benign case result: {benign_result}")
    print(f"Benign case confidence: {benign_confidence:.2f}%") 