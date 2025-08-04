# app.py
from flask import Flask, request, render_template, jsonify
import joblib
import numpy as np
import pandas as pd
import random

app = Flask(__name__)
model = joblib.load('logistic_model.pkl')
scaler = joblib.load('scaler.pkl')

# Load the dataset to calculate mean values
df = pd.read_csv('data.csv')
# Remove the unnamed column if it exists
if df.columns[-1].startswith('Unnamed'):
    df = df.iloc[:, :-1]

# Get feature columns (excluding diagnosis and id)
feature_columns = [col for col in df.columns if col not in ['diagnosis', 'id']]
# Calculate mean values for each feature
feature_means = df[feature_columns].mean().to_dict()

# Feature names for display
feature_names = {
    'radius_mean': 'Radius Mean',
    'texture_mean': 'Texture Mean', 
    'perimeter_mean': 'Perimeter Mean',
    'area_mean': 'Area Mean',
    'smoothness_mean': 'Smoothness Mean',
    'compactness_mean': 'Compactness Mean',
    'concavity_mean': 'Concavity Mean',
    'concave points_mean': 'Concave Points Mean',
    'symmetry_mean': 'Symmetry Mean',
    'fractal_dimension_mean': 'Fractal Dimension Mean',
    'radius_se': 'Radius SE',
    'texture_se': 'Texture SE',
    'perimeter_se': 'Perimeter SE',
    'area_se': 'Area SE',
    'smoothness_se': 'Smoothness SE',
    'compactness_se': 'Compactness SE',
    'concavity_se': 'Concavity SE',
    'concave points_se': 'Concave Points SE',
    'symmetry_se': 'Symmetry SE',
    'fractal_dimension_se': 'Fractal Dimension SE',
    'radius_worst': 'Radius Worst',
    'texture_worst': 'Texture Worst',
    'perimeter_worst': 'Perimeter Worst',
    'area_worst': 'Area Worst',
    'smoothness_worst': 'Smoothness Worst',
    'compactness_worst': 'Compactness Worst',
    'concavity_worst': 'Concavity Worst',
    'concave points_worst': 'Concave Points Worst',
    'symmetry_worst': 'Symmetry Worst',
    'fractal_dimension_worst': 'Fractal Dimension Worst'
}

@app.route('/')
def home():
    return render_template('index.html', features=feature_names, means=feature_means)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Generate random ID
        random_id = random.randint(100000, 999999)
        
        # Initialize features with mean values
        features = []
        
        # Add random ID as first feature
        features.append(random_id)
        
        # Process each feature input
        for feature in feature_columns:
            value = request.form.get(f'feature_{feature}', '').strip()
            if value == '':
                # Use mean value if not provided
                features.append(feature_means[feature])
            else:
                try:
                    features.append(float(value))
                except ValueError:
                    error_msg = f"Invalid value for {feature_names[feature]}. Please enter a valid number."
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'error': error_msg}), 400
                    return render_template('index.html', 
                                         features=feature_names, 
                                         means=feature_means,
                                         error=error_msg)
        
        # Make prediction
        features_array = np.array(features).reshape(1, -1)
        scaled_features = scaler.transform(features_array)
        prediction = model.predict(scaled_features)[0]
        prediction_proba = model.predict_proba(scaled_features)[0]
        
        # Debug prints
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
        
        # Prepare response data
        response_data = {
            'result': result,
            'confidence': f"{confidence:.2f}%",
            'used_features': dict(zip(feature_columns, features[1:])),
            'random_id': random_id,
            'prediction_probability': f"{confidence:.2f}%"
        }
        
        print(f"Response data: {response_data}")
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(response_data)
        
        # Regular form submission
        return render_template('index.html', 
                             features=feature_names, 
                             means=feature_means,
                             result=result, 
                             confidence=f"{confidence:.2f}%",
                             used_features=dict(zip(feature_columns, features[1:])))
    
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        print(f"Error in predict: {error_msg}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': error_msg}), 500
        return render_template('index.html', 
                             features=feature_names, 
                             means=feature_means,
                             error=error_msg)

if __name__ == "__main__":
    app.run(debug=True)
