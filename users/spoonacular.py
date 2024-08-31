import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Function to fetch basic recipe details
def get_recipe_information(recipe_id):
    api_key = os.getenv('SPOONACULAR_API_KEY')
    url = f'https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={api_key}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        return None
    except Exception as err:
        print(f'Other error occurred: {err}')
        return None

# Function to search recipes with advanced filters
def search_recipes(query_params):
    api_key = os.getenv('SPOONACULAR_API_KEY')
    url = f'https://api.spoonacular.com/recipes/complexSearch?apiKey={api_key}'
    try:
        response = requests.get(url, params=query_params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        return None
    except Exception as err:
        print(f'Other error occurred: {err}')
        return None

# Function to search recipes by ingredients
def search_recipes_by_ingredients(ingredients, exclude_ingredients=None):
    api_key = os.getenv('SPOONACULAR_API_KEY')
    url = f'https://api.spoonacular.com/recipes/findByIngredients?apiKey={api_key}'
    params = {
        'ingredients': ','.join(ingredients),
        'number': 10
    }
    if exclude_ingredients:
        params['excludeIngredients'] = ','.join(exclude_ingredients)
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        return None
    except Exception as err:
        print(f'Other error occurred: {err}')
        return None

# Function to search recipes by nutrients
def search_recipes_by_nutrients(nutrients):
    api_key = os.getenv('SPOONACULAR_API_KEY')
    url = f'https://api.spoonacular.com/recipes/findByNutrients?apiKey={api_key}'
    try:
        response = requests.get(url, params=nutrients)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        return None
    except Exception as err:
        print(f'Other error occurred: {err}')
        return None
