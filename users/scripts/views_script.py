import requests
from decouple import config

# Load environment variables
BASE_URL = config('BASE_URL')
LOGIN_ENDPOINT = config('LOGIN_ENDPOINT')
RECIPE_ENDPOINT = config('RECIPE_ENDPOINT')
USER_EMAIL = config('USER_EMAIL')
USER_PASSWORD = config('USER_PASSWORD')

# Login credentials
login_data = {
    "email": USER_EMAIL,
    "password": USER_PASSWORD
}

# Attempt to log in and get the token
login_response = requests.post(f"{BASE_URL}{LOGIN_ENDPOINT}", data=login_data)

if login_response.status_code == 200:
    # Extract the token from the response cookies
    token = login_response.cookies.get('auth_token')
    print(f"Successfully logged in. Token: {token}")

    # Recipe data to submit
    recipe_data = {
        "title": "What to make for dinner tonight?? Bruschetta Style Pork & Pasta",
        "photo": "https://img.spoonacular.com/recipes/715538-556x370.jpg",
        "description": "What to make for dinner tonight?? Bruschetta Style Pork & Pasta might be a good recipe to expand your main course recipe box. This recipe serves 5 and costs $1.96 per serving. One portion of this dish contains approximately <b>45g of protein</b>, <b>13g of fat</b>, and a total of <b>591 calories</b>. This recipe from Pink When requires bow tie pasta, parmigiano reggiano, recipe makers chicken bruschetta pasta, and pork chops. From preparation to the plate, this recipe takes about <b>35 minutes</b>. 163 people were impressed by this recipe. This recipe is typical of Mediterranean cuisine. Taking all factors into account, this recipe <b>earns a spoonacular score of 95%</b>, which is excellent. Similar recipes are <a href=\"https://spoonacular.com/recipes/how-to-make-a-louisiana-style-gumbo-1055614\">How to Make a Louisiana Style Gumbo</a>, <a href=\"https://spoonacular.com/recipes/bruschetta-stuffed-portobellos-636355\">BRUSCHETTA STUFFED PORTOBELLOS</a>, and <a href=\"https://spoonacular.com/recipes/bruschetta-stuffed-potatoes-636356\">Bruschetta Stuffed Potatoes</a>.",
        "servings": 5,
        "cook_time": "35 minutes",
        "ingredients": [
            {
                "name": "Bow Tie Pasta",
                "amount": {
                    "us_value": 3.0,
                    "us_unit": "cups",
                    "metric_value": 180.0,
                    "metric_unit": "g"
                },
                "image": "https://spoonacular.com/cdn/ingredients_100x100/farfalle.png"
            },
            {
                "name": "Parmigiano Reggiano",
                "amount": {
                    "us_value": 0.5,
                    "us_unit": "cup",
                    "metric_value": 50.0,
                    "metric_unit": "g"
                },
                "image": "https://spoonacular.com/cdn/ingredients_100x100/parmesan.jpg"
            },
            {
                "name": "Kraft Recipe Makers Chicken Bruschetta Pasta",
                "amount": {
                    "value": 5.0,
                    "unit": "servings"
                },
                "image": "https://spoonacular.com/cdn/ingredients_100x100/fusilli.jpg"
            },
            {
                "name": "Pork Chops",
                "amount": {
                    "us_value": 1.5,
                    "us_unit": "lb",
                    "metric_value": 680.389,
                    "metric_unit": "g"
                },
                "image": "https://spoonacular.com/cdn/ingredients_100x100/pork-chops.jpg"
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



    # # Recipe data to submit
    # recipe_data = {
    #     "title": "What to make for dinner tonight?? Bruschetta Style Pork & Pasta",
    #     "photo": "https://img.spoonacular.com/recipes/715538-556x370.jpg",
    #     "description": "What to make for dinner tonight?? Bruschetta Style Pork & Pasta might be a good recipe to expand your main course recipe box. This recipe serves 5 and costs $1.96 per serving. One portion of this dish contains approximately <b>45g of protein</b>, <b>13g of fat</b>, and a total of <b>591 calories</b>. This recipe from Pink When requires bow tie pasta, parmigiano reggiano, recipe makers chicken bruschetta pasta, and pork chops. From preparation to the plate, this recipe takes about <b>35 minutes</b>. 163 people were impressed by this recipe. This recipe is typical of Mediterranean cuisine. Taking all factors into account, this recipe <b>earns a spoonacular score of 95%</b>, which is excellent. Similar recipes are <a href=\"https://spoonacular.com/recipes/how-to-make-a-louisiana-style-gumbo-1055614\">How to Make a Louisiana Style Gumbo</a>, <a href=\"https://spoonacular.com/recipes/bruschetta-stuffed-portobellos-636355\">BRUSCHETTA STUFFED PORTOBELLOS</a>, and <a href=\"https://spoonacular.com/recipes/bruschetta-stuffed-potatoes-636356\">Bruschetta Stuffed Potatoes</a>.",
    #     "servings": 5,
    #     "cook_time": "35 minutes",
    #     "ingredients": [
    #         {
    #             "name": "Bow Tie Pasta",
    #             "amount": {
    #                 "us_value": 3.0,
    #                 "us_unit": "cups",
    #                 "metric_value": 180.0,
    #                 "metric_unit": "g"
    #             }
    #         },
    #         {
    #             "name": "Parmigiano Reggiano",
    #             "amount": {
    #                 "us_value": 0.5,
    #                 "us_unit": "cup",
    #                 "metric_value": 50.0,
    #                 "metric_unit": "g"
    #             }
    #         },
    #         {
    #             "name": "Kraft Recipe Makers Chicken Bruschetta Pasta",
    #             "amount": {
    #                 "value": 5.0,
    #                 "unit": "servings"
    #             }
    #         },
    #         {
    #             "name": "Pork Chops",
    #             "amount": {
    #                 "us_value": 1.5,
    #                 "us_unit": "lb",
    #                 "metric_value": 680.389,
    #                 "metric_unit": "g"
    #             }
    #         }
    #     ],
    #     "instructions": [
    #         {"step_number": 1, "description": "Wash and rinse pork chops and place into the skillet."},
    #         {"step_number": 2, "description": "Cut them into bite-sized pieces and add half of the Basil Garlic simmer sauce."},
    #         {"step_number": 3, "description": "Boil your water and start working on cooking your bow-tie pasta."},
    #         {"step_number": 4, "description": "When you have finished boiling and draining your pasta, add it to the pork along with the rest of the Basil Garlic Simmering Sauce, mixing lightly."},
    #         {"step_number": 5, "description": "Next, you will top with the Chunky Bruschetta Finishing Sauce, cover with Parmesan, and cover."},
    #         {"step_number": 6, "description": "Cook on low heat 2 to 3 minutes or until heated through."}
    #     ]
    # }

    # Headers including the token in cookies
    headers = {
        "Content-Type": "application/json",
    }
    cookies = {
        "auth_token": token,
    }

    # Send a POST request to create a recipe
    create_response = requests.post(
        f"{BASE_URL}{RECIPE_ENDPOINT}",
        json=recipe_data,
        headers=headers,
        cookies=cookies  # Include the token in the cookies
    )

    if create_response.status_code == 201:
        print("Recipe created successfully!")
        print(f"Response: {create_response.json()}")
    else:
        print(f"Failed to create recipe. Status code: {create_response.status_code}")
        print(f"Response: {create_response.text}")
else:
    print(f"Login failed. Status code: {login_response.status_code}")
    print(f"Response: {login_response.text}")