# test_api.py
import requests

url = "https://sunpich.onrender.com/api/chat"
data = {
    "message": "Hola, soy William Mosquera. Necesito consejo sobre estrategias de innovación."
}

response = requests.post(url, json=data)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    print(response.json())
else:
    print(f"Error: {response.text}")