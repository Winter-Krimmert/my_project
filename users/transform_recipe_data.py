def transform_recipe_data(aggregate_data):
    # Extracting title, photo, description, servings, and cook time
    recipe_details = {
        "title": aggregate_data.get("title"),
        "photo": aggregate_data.get("image"),
        "description": aggregate_data.get("summary"),
        "servings": aggregate_data.get("servings"),
        "cookTime": f"{aggregate_data.get('preparationMinutes') + aggregate_data.get('cookingMinutes')} minutes",
        "ingredients": [],
        "instructions": [],
        "cuisine": aggregate_data.get("cuisines", []),  # Storing cuisines as a list
        "diet": aggregate_data.get("diets", []),  # Storing diets as a list
        "meal_type": map_meal_type(aggregate_data.get("dishTypes", [])),  # Mapping and storing meal types as a list
        "dish_type": map_dish_type(aggregate_data.get("dishTypes", [])),  # Mapping and storing dish types as a list
        "occasion": aggregate_data.get("occasions", [])  # Storing occasions as a list
    }

    # Transforming ingredients
    for ingredient in aggregate_data.get("extendedIngredients", []):
        ingredient_data = {
            "id": ingredient.get("id"),
            "name": ingredient.get("originalName"),
            "image": f"https://spoonacular.com/cdn/ingredients_100x100/{ingredient.get('image')}",
            "amount": {
                "us": {
                    "value": ingredient.get("measures", {}).get("us", {}).get("amount"),
                    "unit": ingredient.get("measures", {}).get("us", {}).get("unitShort")
                },
                "metric": {
                    "value": ingredient.get("measures", {}).get("metric", {}).get("amount"),
                    "unit": ingredient.get("measures", {}).get("metric", {}).get("unitShort")
                }
            }
        }
        recipe_details["ingredients"].append(ingredient_data)

    # Transforming instructions
    instructions_raw = aggregate_data.get("instructions", "")
    instructions_steps = [step.strip() + "." for step in instructions_raw.split('.') if step.strip()]
    recipe_details["instructions"] = [
        {"number": i + 1, "step": step} for i, step in enumerate(instructions_steps)
    ]

    return {"recipeDetails": recipe_details}

def map_meal_type(dish_types):
    """Maps the dish types to meal types if applicable."""
    meal_types = ['breakfast', 'lunch', 'dinner']
    return [dish_type for dish_type in dish_types if dish_type.lower() in meal_types]

def map_dish_type(dish_types):
    """Maps the dish types, excluding meal types."""
    meal_types = ['breakfast', 'lunch', 'dinner']
    return [dish_type for dish_type in dish_types if dish_type.lower() not in meal_types]

# Example usage
aggregate_data = {
    "id": 715538,
    "title": "What to make for dinner tonight?? Bruschetta Style Pork & Pasta",
    "readyInMinutes": 35,
    "servings": 5,
    "sourceUrl": "http://www.pinkwhen.com/make-dinner-tonight/",
    "image": "https://img.spoonacular.com/recipes/715538-556x370.jpg",
    "imageType": "jpg",
    "summary": "What to make for dinner tonight?? Bruschetta Style Pork & Pasta takes roughly <b>35 minutes</b> from beginning to end. This recipe...",
    "preparationMinutes": 5,
    "cookingMinutes": 30,
    "extendedIngredients": [
        {
            "id": 10120420,
            "aisle": "Pasta and Rice",
            "image": "farfalle.png",
            "consistency": "SOLID",
            "name": "bow tie pasta",
            "nameClean": "farfalle",
            "original": "3 cups bow tie pasta",
            "originalName": "bow tie pasta",
            "amount": 3.0,
            "unit": "cups",
            "meta": [],
            "measures": {
                "us": {
                    "amount": 3.0,
                    "unitShort": "cups",
                    "unitLong": "cups"
                },
                "metric": {
                    "amount": 180.0,
                    "unitShort": "g",
                    "unitLong": "grams"
                }
            }
        },
        {
            "id": 1033,
            "aisle": "Cheese",
            "image": "parmesan.jpg",
            "consistency": "SOLID",
            "name": "parmigiano reggiano",
            "nameClean": "parmesan",
            "original": "½ cup Parmigiano Reggiano",
            "originalName": "Parmigiano Reggiano",
            "amount": 0.5,
            "unit": "cup",
            "meta": [],
            "measures": {
                "us": {
                    "amount": 0.5,
                    "unitShort": "cups",
                    "unitLong": "cups"
                },
                "metric": {
                    "amount": 50.0,
                    "unitShort": "g",
                    "unitLong": "grams"
                }
            }
        },
        {
            "id": 20420,
            "aisle": "Pasta and Rice",
            "image": "fusilli.jpg",
            "consistency": "SOLID",
            "name": "recipe makers chicken bruschetta pasta",
            "nameClean": "pasta",
            "original": "Kraft Recipe Makers Chicken Bruschetta Pasta",
            "originalName": "Kraft Recipe Makers Chicken Bruschetta Pasta",
            "amount": 5.0,
            "unit": "servings",
            "meta": ["kraft"],
            "measures": {
                "us": {
                    "amount": 5.0,
                    "unitShort": "servings",
                    "unitLong": "servings"
                },
                "metric": {
                    "amount": 5.0,
                    "unitShort": "servings",
                    "unitLong": "servings"
                }
            }
        },
        {
            "id": 10010062,
            "aisle": "Meat",
            "image": "pork-chops.jpg",
            "consistency": "SOLID",
            "name": "pork chops",
            "nameClean": "pork chops",
            "original": "1-1/2 lb. pork chops",
            "originalName": "pork chops",
            "amount": 1.5,
            "unit": "lb",
            "meta": [],
            "measures": {
                "us": {
                    "amount": 1.5,
                    "unitShort": "lb",
                    "unitLong": "pounds"
                },
                "metric": {
                    "amount": 680.389,
                    "unitShort": "g",
                    "unitLong": "grams"
                }
            }
        }
    ],
    "instructions": "wash and rinse pork chops and place into the skillet.cut them into bite sized pieces and add half of the Basil Garlic simmer sauce.boil your water and start working on cooking your bow-tie pasta.when you have finished with boiling and draining your pasta, add it to the pork along with the rest of the Basil Garlic Simmering Sauce, mixing lightly.Next you will top with the Chunky Bruschetta Finishing Sauce, cover with Parmesan, and cover. Cooking on low heat 2 to 3 minutes or until heated through.",
    "analyzedInstructions": [
        {
            "name": "",
            "steps": [
                {
                    "number": 1,
                    "step": "wash and rinse pork chops and place into the skillet.cut them into bite sized pieces and add half of the Basil Garlic simmer sauce.boil your water and start working on cooking your bow-tie pasta.when you have finished with boiling and draining your pasta, add it to the pork along with the rest of the Basil Garlic Simmering Sauce, mixing lightly.Next you will top with the Chunky Bruschetta Finishing Sauce, cover with Parmesan, and cover. Cooking on low heat 2 to 3 minutes or until heated through.",
                    "ingredients": [
                        # ingredient data here
                    ]
                }
            ]
        }
    ],
    "cuisines": [
        "Mediterranean",
        "Italian",
        "European"
    ],
    "dishTypes": [
        "lunch",
        "main course",
        "main dish",
        "dinner"
    ],
    "diets": [],
    "occasions": []
}

final_data = transform_recipe_data(aggregate_data)
print(final_data)
