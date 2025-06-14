import requests
import json

try:
    response = requests.get("http://localhost:4222/api/system/info")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}") 