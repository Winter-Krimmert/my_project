import os
from pymongo import MongoClient
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Replace with your MongoDB connection string and database name from environment variables
client = MongoClient(os.getenv("MONGO_DB_HOST"))
db = client[os.getenv("MONGO_DB_NAME")]

# Collection name for recipes
recipes_collection = db["recipes"]

# Recipe data to insert
recipe_data = {
    "title": "What to make for dinner tonight?? Bruschetta Style Pork & Pasta",
    "photo": "https://img.spoonacular.com/recipes/715538-556x370.jpg",
    "description": ("What to make for dinner tonight?? Bruschetta Style Pork & Pasta might be a good recipe to expand your main course recipe box. "
                    "This recipe serves 5 and costs $1.96 per serving. One portion of this dish contains approximately 45g of protein, 13g of fat, "
                    "and a total of 591 calories. This recipe from Pink When requires bow tie pasta, parmigiano reggiano, recipe makers chicken bruschetta pasta, "
                    "and pork chops. From preparation to the plate, this recipe takes about 35 minutes. 163 people were impressed by this recipe. "
                    "This recipe is typical of Mediterranean cuisine. Taking all factors into account, this recipe earns a spoonacular score of 95%, "
                    "which is excellent. Similar recipes are How to Make a Louisiana Style Gumbo, BRUSCHETTA STUFFED PORTOBELLOS, and Bruschetta Stuffed Potatoes."),
    "servings": 5,
    "cookTime": "35 minutes",
    "ingredients": [
        {
            "id": 10120420,
            "name": "Bow Tie Pasta",
            "image": "https://spoonacular.com/cdn/ingredients_100x100/farfalle.png",
            "amount": {
                "us": {"value": 3.0, "unit": "cups"},
                "metric": {"value": 180.0, "unit": "g"}
            }
        },
        {
            "id": 1033,
            "name": "Parmigiano Reggiano",
            "image": "https://spoonacular.com/cdn/ingredients_100x100/parmesan.jpg",
            "amount": {
                "us": {"value": 0.5, "unit": "cup"},
                "metric": {"value": 50.0, "unit": "g"}
            }
        },
        {
            "id": 20420,
            "name": "Kraft Recipe Makers Chicken Bruschetta Pasta",
            "image": "https://spoonacular.com/cdn/ingredients_100x100/fusilli.jpg",
            "amount": {
                "us": {"value": 5.0, "unit": "servings"},
                "metric": {"value": 5.0, "unit": "servings"}
            }
        },
        {
            "id": 10010062,
            "name": "Pork Chops",
            "image": "https://spoonacular.com/cdn/ingredients_100x100/pork-chops.jpg",
            "amount": {
                "us": {"value": 1.5, "unit": "lb"},
                "metric": {"value": 680.389, "unit": "g"}
            }
        }
    ],
    "instructions": [
        {"number": 1, "step": "Wash and rinse pork chops and place into the skillet."},
        {"number": 2, "step": "Cut them into bite-sized pieces and add half of the Basil Garlic simmer sauce."},
        {"number": 3, "step": "Boil your water and start working on cooking your bow-tie pasta."},
        {"number": 4, "step": "When you have finished boiling and draining your pasta, add it to the pork along with the rest of the Basil Garlic Simmering Sauce, mixing lightly."},
        {"number": 5, "step": "Next, you will top with the Chunky Bruschetta Finishing Sauce, cover with Parmesan, and cover."},
        {"number": 6, "step": "Cook on low heat 2 to 3 minutes or until heated through."}
    ],
    "created_at": datetime.now(timezone.utc),
    "updated_at": datetime.now(timezone.utc),
    "user_id": os.getenv("USER_ID")  # Use user ID from environment variables
}

# Insert the recipe into the database
result = recipes_collection.insert_one(recipe_data)
print(f"Recipe inserted with ID: {result.inserted_id}")
