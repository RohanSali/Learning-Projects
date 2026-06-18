# app.py
from flask import Flask, request, render_template, jsonify
import joblib
import numpy as np
import pandas as pd
import random

app = Flask(__name__)

# Compatibility shim for older pickles that reference `numpy._core`.
# Some models serialized with older NumPy versions expect `numpy._core` to exist.
# Map `numpy._core` to `numpy.core` in sys.modules so unpickling succeeds.
import sys, importlib
try:
    if 'numpy._core' not in sys.modules:
        sys.modules['numpy._core'] = importlib.import_module('numpy.core')
except Exception as shim_exc:
    # Log the shim failure; loading may still fail later and raise a clear error.
    print(f"Warning: numpy._core compatibility shim failed: {shim_exc}")

# Load the dataset early to compute means/stds and support a fallback scaler
# (needed before attempting to load the scaler below)
df = pd.read_csv('data.csv')
# Remove the unnamed column if it exists
if df.columns[-1].startswith('Unnamed'):
    df = df.iloc[:, :-1]

# Get feature columns (excluding diagnosis and id)
feature_columns = [col for col in df.columns if col not in ['diagnosis', 'id']]
# Calculate mean and std values for each feature
feature_means = df[feature_columns].mean().to_dict()
feature_stds = df[feature_columns].std(ddof=0).to_dict()

# Load the trained model
model = joblib.load('logistic_model.pkl')

# Attempt to load the scaler; first check whether the pickle references
# `numpy._core` (which can trigger incompatible C-extension imports). If it
# does, skip loading and use a fallback computed from the dataset.
import os
scaler_path = 'scaler.pkl'
_use_fallback = False
if os.path.exists(scaler_path):
    try:
        with open(scaler_path, 'rb') as f:
            content = f.read()
        if b'numpy._core' in content:
            print('scaler.pkl references numpy._core; skipping joblib load and using fallback')
            _use_fallback = True
    except Exception as e:
        print(f'Warning while inspecting scaler.pkl: {e}; will attempt joblib.load and fallback on error')

if not _use_fallback:
    try:
        scaler = joblib.load(scaler_path)
    except Exception as e:
        print(f"Warning: could not load scaler.pkl ({e}). Using fallback scaler computed from dataset.")
        _use_fallback = True

if _use_fallback:
    # Prepare fallback mean/std arrays matching expected input order (id, then features)
    id_mean = df['id'].mean() if 'id' in df.columns else 0.0
    id_std = df['id'].std(ddof=0) if 'id' in df.columns else 1.0
    means = [id_mean] + [feature_means[f] for f in feature_columns]
    stds = [id_std] + [max(feature_stds.get(f, 0.0), 1.0) for f in feature_columns]

    class FallbackScaler:
        def __init__(self, mean, scale):
            import numpy as _np
            self.mean_ = _np.array(mean, dtype=float)
            self.scale_ = _np.array(scale, dtype=float)
            # avoid division by zero
            self.scale_[self.scale_ == 0] = 1.0
            self.n_features_in_ = int(self.mean_.shape[0])

        def transform(self, X):
            import numpy as _np
            X = _np.asarray(X, dtype=float)
            return (X - self.mean_) / self.scale_

    scaler = FallbackScaler(means, stds)

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

print('app module initialized')

if __name__ == "__main__":
    app.run(debug=True)
