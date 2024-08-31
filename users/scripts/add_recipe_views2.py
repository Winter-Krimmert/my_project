import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Sample data for the recipe
recipe_data = {
    "title": "What to make for dinner tonight?? Bruschetta Style Pork & Pasta",
    "photo": "https://img.spoonacular.com/recipes/715538-556x370.jpg",
    "description": "What to make for dinner tonight?? Bruschetta Style Pork & Pasta might be a good recipe to expand your main course recipe box...",
    "servings": 5,
    "cook_time": "35 minutes",
    "ingredients": [
        {
            "name": "Bow Tie Pasta",
            "image": "https://spoonacular.com/cdn/ingredients_100x100/farfalle.png",
            "amount": {
                "us_value": 3.0,
                "us_unit": "cups",
                "metric_value": 180.0,
                "metric_unit": "g"
            }
        },
        {
            "name": "Parmigiano Reggiano",
            "image": "https://spoonacular.com/cdn/ingredients_100x100/parmesan.jpg",
            "amount": {
                "us_value": 0.5,
                "us_unit": "cup",
                "metric_value": 50.0,
                "metric_unit": "g"
            }
        },
        {
            "name": "Kraft Recipe Makers Chicken Bruschetta Pasta",
            "image": "https://spoonacular.com/cdn/ingredients_100x100/fusilli.jpg",
            "amount": {
                "value": 5.0,
                "unit": "servings"
            }
        },
        {
            "name": "Pork Chops",
            "image": "https://spoonacular.com/cdn/ingredients_100x100/pork-chops.jpg",
            "amount": {
                "us_value": 1.5,
                "us_unit": "lb",
                "metric_value": 680.389,
                "metric_unit": "g"
            }
        }
    ],
    "instructions": [
        {"step_number": 1, "description": "Wash and rinse pork chops and place into the skillet."},
        {"step_number": 2, "description": "Cut them into bite-sized pieces and add half of the Basil Garlic simmer sauce."},
        {"step_number": 3, "description": "Boil your water and start working on cooking your bow-tie pasta."},
        {"step_number": 4, "description": "When you have finished boiling and draining your pasta, add it to the pork along with the rest of the Basil Garlic Simmering Sauce, mixing lightly."},
        {"step_number": 5, "description": "Next, you will top with the Chunky Bruschetta Finishing Sauce, cover with Parmesan, and cover."},
        {"step_number": 6, "description": "Cook on low heat 2 to 3 minutes or until heated through."}
    ]
}

# Replace these with your actual values
api_url = 'http://localhost:8000/api/recipes/'  # Update with your API endpoint
auth_token = os.getenv('AUTH_TOKEN')  # Ensure this is correctly set in your .env file

# Headers including the bearer token
headers = {
    "Authorization": f"token {auth_token}",
    "Content-Type": "application/json"
}

# Test creating a recipe via the Django view
response = requests.post(api_url, json=recipe_data, headers=headers)

if response.status_code == 201:
    recipe_id = response.json().get('id')
    print(f"Recipe successfully created: {recipe_id}")
else:
    print(f"Failed to create recipe: {response.status_code} - {response.text}")
