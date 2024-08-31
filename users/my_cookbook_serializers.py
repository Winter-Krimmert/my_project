# serializers.py
from rest_framework import serializers
from .models import MyCookbook, Recipe
from .fields import ObjectIdField

class MyCookbookSerializer(serializers.ModelSerializer):
    cookbook_id = ObjectIdField()  # Custom ObjectId field for the cookbook_id
    recipes = serializers.SerializerMethodField()  # Serialize recipes references
    recipe_ids = serializers.ListField(
        child=ObjectIdField(),  # Custom ObjectId field for recipe IDs
        write_only=True,
        required=False
    )
    owner = serializers.SerializerMethodField()  # Serialize owner details

    class Meta:
        model = MyCookbook
        fields = [
            'cookbook_id', 'name', 'description', 'recipes', 
            'recipe_ids', 'owner', 'created_at', 'updated_at', 'is_public'
        ]
        read_only_fields = ['cookbook_id', 'created_at', 'updated_at', 'recipes', 'owner']

    def get_recipes(self, obj):
        # Serialize recipe references
        return [{'recipe_id': str(recipe.recipe_id), 'title': recipe.title, 'description': recipe.description, 'cook_time': recipe.cook_time} for recipe in obj.recipes]

    def get_owner(self, obj):
        # Serialize owner details (assuming you want to return user info)
        return {
            'user_id': str(obj.owner.id),
            'email': obj.owner.email,
            'name': obj.owner.name
        }

    def create(self, validated_data):
        recipe_ids = validated_data.pop('recipe_ids', [])
        owner = self.context['request'].user  # Assuming the user is available in the request context
        cookbook = MyCookbook(owner=owner, **validated_data)
        cookbook.save()
        if recipe_ids:
            recipes = Recipe.objects.filter(recipe_id__in=recipe_ids)
            cookbook.recipes.extend(recipes)
            cookbook.save()
        return cookbook

    def update(self, instance, validated_data):
        recipe_ids = validated_data.pop('recipe_ids', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if recipe_ids:
            recipes = Recipe.objects.filter(recipe_id__in=recipe_ids)
            instance.recipes.set(recipes)  # Use `set` to replace the recipes list
        instance.save()
        return instance
