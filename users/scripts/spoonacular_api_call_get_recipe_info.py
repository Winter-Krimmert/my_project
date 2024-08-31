from users.spoonacular import get_recipe_information

# Test Recipe ID
recipe_id = 715538

# Make the API call
recipe_data = get_recipe_information(recipe_id)

# Output the result
if recipe_data:
    print("Recipe Information:")
    print(recipe_data)
else:
    print("Failed to retrieve recipe information.")
