import requests
from decouple import config

# Load environment variables
BASE_URL = config('BASE_URL')
LOGIN_ENDPOINT = config('LOGIN_ENDPOINT')
USER_EMAIL = config('USER_EMAIL')
USER_PASSWORD = config('USER_PASSWORD')

def get_auth_token(email, password):
    login_url = f"{BASE_URL}{LOGIN_ENDPOINT}"
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(login_url, data=login_data)
        if response.status_code == 200:
            token = response.cookies.get('auth_token')
            print(f"Successfully logged in. Token: {token}")
            return token
        else:
            print(f"Failed to log in. Status code: {response.status_code}, Response: {response.json()}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return None

if __name__ == "__main__":
    token = get_auth_token(USER_EMAIL, USER_PASSWORD)
    if token:
        # Use the token for subsequent requests
        print(f"Authentication token: {token}")
