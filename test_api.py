import requests
import json

url = "http://localhost:8080/products/stream"
headers = {"Content-Type": "application/json"}
data = ["papel higienico", "papel toalha"]

response = requests.post(url, headers=headers, json=data)
print(response.text) 