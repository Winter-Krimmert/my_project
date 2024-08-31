import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

# Fetch variables from .env
api_url = os.getenv('RECIPE_CREATE_URL')
auth_token = os.getenv('AUTH_TOKEN')

# Set up headers with the authentication token
headers = {
    'Authorization': f'Token {auth_token}',  # Use 'Bearer' if your API uses bearer tokens
    'Content-Type': 'application/json'
}

# Make a GET request to the protected endpoint
response = requests.get(api_url, headers=headers)

# Print the status code and response text
print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text}")

# Print headers and cookies for debugging
print(f"Request Headers: {response.request.headers}")
print(f"Cookies: {response.cookies}")
