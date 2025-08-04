import requests
import json

# Test the API endpoint
url = "http://localhost:5000/predict"
headers = {
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/x-www-form-urlencoded'
}

# Test data with just a few parameters
data = {
    'feature_radius_mean': '14.1273',
    'feature_texture_mean': '19.2896',
    'feature_perimeter_mean': '91.9690'
}

try:
    response = requests.post(url, headers=headers, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Text: {response.text}")
    
    if response.status_code == 200:
        try:
            json_data = response.json()
            print(f"JSON Response: {json.dumps(json_data, indent=2)}")
            
            # Check if result is present
            if 'result' in json_data:
                print(f"✅ Diagnosis Result: {json_data['result']}")
            else:
                print("❌ No 'result' field in response")
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
    else:
        print(f"❌ Request failed with status {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}") 