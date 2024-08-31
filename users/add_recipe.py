from decouple import config
from datetime import datetime, timezone
from mongoengine import connect
from my_project.users.models import Recipe, Ingredient, IngredientAmount, Instruction, Media, MyPlate, User

# Load environment variables
MONGODB_URI = config('MONGODB_URI')

# Connect to MongoDB using mongoengine
# connect(
#     db='Recipe-z',
#     host=MONGODB_URI
# )

# Define the sample recipe data
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
            }
        },
        {
            "name": "Parmigiano Reggiano",
            "amount": {
                "us_value": 0.5,
                "us_unit": "cup",
                "metric_value": 50.0,
                "metric_unit": "g"
            }
        },
        {
            "name": "Kraft Recipe Makers Chicken Bruschetta Pasta",
            "amount": {
                "value": 5.0,
                "unit": "servings"
            }
        },
        {
            "name": "Pork Chops",
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

# Create and save the recipe
recipe = Recipe(
    title=recipe_data['title'],
    description=recipe_data['description'],
    keywords=[],  # Keywords are not provided in the sample data
    servings=recipe_data['servings'],
    cook_time=recipe_data['cook_time'],
    ingredients=[
        Ingredient(
            name=ing['name'],
            amount=IngredientAmount(
                value=ing.get('amount', {}).get('value'),
                unit=ing.get('amount', {}).get('unit'),
                us_value=ing.get('amount', {}).get('us_value'),
                us_unit=ing.get('amount', {}).get('us_unit'),
                metric_value=ing.get('amount', {}).get('metric_value'),
                metric_unit=ing.get('amount', {}).get('metric_unit')
            ),
            media=[Media(type="image", url=ing.get('image'))] if 'image' in ing else []
        ) for ing in recipe_data['ingredients']
    ],
    instructions=[
        Instruction(
            step_number=instr['step_number'],
            description=instr['description']
        ) for instr in recipe_data['instructions']
    ],
    media=[Media(type="image", url=recipe_data['photo'])],
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
    user_id="66bdc66aea98f86553ecd2e3"  # Replace with a valid ObjectId if available
)

recipe.save()
print(f"Recipe saved: {recipe.title}")

# Create a MyPlate document to link the recipe with a user
user_id = "66bdc66aea98f86553ecd2e3"  # Replace with the actual ObjectId of the user

my_plate = MyPlate(
    user_id=user_id,
    recipe_id=recipe.recipe_id
)
my_plate.save()
print(f"MyPlate saved: {my_plate.recipe_id}")

# Update the User document to include the new MyPlate
user = User.objects(id=user_id).first()
if user:
    user.my_plates.append(my_plate)
    user.save()
    print(f"User updated with new MyPlate: {user.email}")
else:
    print(f"User with id {user_id} not found")
