import re
from rest_framework import serializers
from .models import User, Recipe, Ingredient, Instruction, Media, IngredientAmount
from django.contrib.auth.hashers import make_password
from datetime import timezone, datetime

class UserSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)  # User's name
    email = serializers.EmailField()  # User's email
    password = serializers.CharField(write_only=True)  # Password (write-only)

    def validate_email(self, value):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Enter a valid email address.")
        if User.objects(email=value).first():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_password(self, value):
        if len(value) < 8 or not re.search(r"[A-Z]", value) or not re.search(r"[0-9]", value):
            raise serializers.ValidationError("Password must be at least 8 characters long and include an uppercase letter and a number.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.password_hash = make_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        new_email = validated_data.get('email', instance.email)

        if new_email != instance.email and User.objects(email=new_email).first():
            raise serializers.ValidationError("This email is already registered.")

        instance.email = new_email

        if 'password' in validated_data:
            instance.password_hash = make_password(validated_data['password'])
        
        instance.save()
        return instance

# # Ingredient Amount Serializer
# class IngredientAmountSerializer(serializers.ModelSerializer):
#     value = serializers.FloatField(required=False)  # Amount value
#     unit = serializers.CharField(max_length=50, required=False)  # Measurement unit
#     us_value = serializers.FloatField(required=False)  # US measurement value
#     us_unit = serializers.CharField(max_length=50, required=False)  # US measurement unit
#     metric_value = serializers.FloatField(required=False)  # Metric measurement value
#     metric_unit = serializers.CharField(max_length=50, required=False)  # Metric measurement unit

#     class Meta:
#         model = IngredientAmount
#         fields = '__all__'

# # Media Serializer
# class MediaSerializer(serializers.ModelSerializer):
#     type = serializers.ChoiceField(choices=['image', 'video'])  # Type of media
#     url = serializers.URLField()  # Media URL
#     file_path = serializers.CharField(required=False)  # File path

#     class Meta:
#         model = Media
#         fields = '__all__'

# # Ingredient Serializer
# class IngredientSerializer(serializers.ModelSerializer):
#     name = serializers.CharField(max_length=100)  # Ingredient name
#     amount = IngredientAmountSerializer(required=False)  # Amount of ingredient
#     spoonacular_id = serializers.IntegerField(required=False)  # Spoonacular ID
#     media = MediaSerializer(many=True, required=False)  # Media associated with ingredient

#     class Meta:
#         model = Ingredient
#         fields = '__all__'

# # Instruction Serializer
# class InstructionSerializer(serializers.ModelSerializer):
#     step_number = serializers.IntegerField()  # Step number
#     description = serializers.CharField()  # Description of the step
#     photo = serializers.URLField(required=False)  # Photo URL
#     video = serializers.URLField(required=False)  # Video URL

#     class Meta:
#         model = Instruction
#         fields = '__all__'

# # Media Serializer
# class MediaSerializer(serializers.ModelSerializer):
#     type = serializers.ChoiceField(choices=['image', 'video'])  # Type of media
#     url = serializers.URLField()  # Media URL
#     file_path = serializers.CharField(required=False)  # File path

#     class Meta:
#         model = Media
#         fields = '__all__'

# # Recipe Serializer
# class RecipeSerializer(serializers.ModelSerializer):
#     title = serializers.CharField(max_length=200)  # Recipe title
#     description = serializers.CharField(required=False)  # Recipe description
#     keywords = serializers.ListField(child=serializers.CharField(max_length=50), required=False)  # Recipe keywords
#     servings = serializers.IntegerField()  # Number of servings
#     cook_time = serializers.CharField(max_length=50)  # Cook time
#     ingredients = IngredientSerializer(many=True)  # List of ingredients
#     instructions = InstructionSerializer(many=True)  # List of instructions
#     media = MediaSerializer(many=True, required=False)  # List of media items
#     spoonacular_id = serializers.IntegerField(required=False, allow_null=True)  # Spoonacular ID

#     class Meta:
#         model = Recipe
#         fields = '__all__'

# def create(self, validated_data):
#         ingredients_data = validated_data.pop('ingredients')
#         instructions_data = validated_data.pop('instructions')
#         media_data = validated_data.pop('media', [])

#         recipe = Recipe(**validated_data)
#         recipe.created_at = datetime.now(timezone.utc)  # Set created_at
#         recipe.updated_at = datetime.now(timezone.utc)  # Set updated_at
#         recipe.save()

#         # Save nested ingredients, instructions, and media
#         self._save_ingredients(recipe, ingredients_data)
#         self._save_instructions(recipe, instructions_data)
#         self._save_media(recipe, media_data)

#         return recipe

# def update(self, instance, validated_data):
#         instance.title = validated_data.get('title', instance.title)
#         instance.description = validated_data.get('description', instance.description)
#         instance.servings = validated_data.get('servings', instance.servings)
#         instance.cook_time = validated_data.get('cook_time', instance.cook_time)

#         instance.updated_at = datetime.now(timezone.utc)  # Update timestamp
#         instance.save()

#         if 'ingredients' in validated_data:
#             instance.ingredients.clear()
#             self._save_ingredients(instance, validated_data['ingredients'])

#         if 'instructions' in validated_data:
#             instance.instructions.clear()
#             self._save_instructions(instance, validated_data['instructions'])

#         if 'media' in validated_data:
#             instance.media.clear()
#             self._save_media(instance, validated_data['media'])

#         return instance

# def _save_ingredients(self, recipe, ingredients_data):
#     for ingredient_data in ingredients_data:
#         amount_data = ingredient_data.pop('amount', None)
#         ingredient = Ingredient(**ingredient_data)

#         if amount_data:
#             ingredient.amount = IngredientAmount(**amount_data)

#         ingredient.recipe_id = recipe.id  # Associate ingredient with the recipe
#         ingredient.save()

# def __save_instructions(self, recipe, instructions_data):
#     for instruction_data in instructions_data:
#         instruction = Instruction(**instruction_data)
#         instruction.recipe_id = recipe.id  # Associate instruction with the recipe
#         instruction.save()

# def _save_media(self, recipe, media_data):
#     for media_entry in media_data:
#         media = Media(**media_entry)
#         media.recipe_id = recipe.id  # Associate media with the recipe
#         media.save()




