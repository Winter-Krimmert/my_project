# # serializers.pyfrom rest_framework import serializers
# from rest_framework import serializers
# from .models import User, Recipe, Ingredient, Instruction, Media, IngredientAmount

# class IngredientAmountSerializer(serializers.Serializer):
#     value = serializers.FloatField(required=False)
#     unit = serializers.CharField(required=False, allow_blank=True)
#     us_value = serializers.FloatField(required=False)
#     us_unit = serializers.CharField(required=False, allow_blank=True)
#     metric_value = serializers.FloatField(required=False)
#     metric_unit = serializers.CharField(required=False, allow_blank=True)

# class MediaSerializer(serializers.Serializer):
#     type = serializers.ChoiceField(choices=['image', 'video'])
#     url = serializers.URLField(required=False)
#     file_path = serializers.CharField(required=False, allow_blank=True)

# class IngredientSerializer(serializers.Serializer):
#     name = serializers.CharField()
#     spoonacular_id = serializers.IntegerField(required=False)
#     amount = IngredientAmountSerializer()
#     media = MediaSerializer(many=True, required=False)

# class InstructionSerializer(serializers.Serializer):
#     step_number = serializers.IntegerField()
#     description = serializers.CharField()
#     photo = serializers.URLField(required=False)
#     video = serializers.URLField(required=False)

# class RecipeSerializer(serializers.Serializer):
#     title = serializers.CharField()
#     description = serializers.CharField(required=False)
#     keywords = serializers.ListField(child=serializers.CharField(), required=False)
#     servings = serializers.IntegerField()
#     cook_time = serializers.CharField()
#     ingredients = IngredientSerializer(many=True)
#     instructions = InstructionSerializer(many=True)
#     media = MediaSerializer(many=True, required=False)
#     user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
#     created_at = serializers.DateTimeField(required=False)
#     updated_at = serializers.DateTimeField(required=False)
