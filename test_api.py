# test_api.py
import os
from dotenv import load_dotenv
import requests

load_dotenv()
api_key = os.getenv("FOOTBALL_API_KEY")
print(f"API Key: {api_key}")
headers = {
    "X-RapidAPI-Key": api_key,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}
response = requests.get(
    "https://api-football-v1.p.rapidapi.com/v3/teams",
    headers=headers,
    params={"search": "Manchester United"}
)
print(f"Status: {response.status_code}, Response: {response.text[:200]}")