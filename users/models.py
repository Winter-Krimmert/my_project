from mongoengine import (
    Document, StringField, DateTimeField, EmbeddedDocumentField, 
    ListField, ReferenceField, EmbeddedDocument, IntField, URLField, 
    ObjectIdField, BooleanField, FloatField, signals, CASCADE
)
from bson import ObjectId
from datetime import datetime, timezone, timedelta
import base64
import os
from gridfs import GridFS
from django.conf import settings
from .GridFS import MediaFile
from my_project.settings import fs




# Social Login Embedded Document
class SocialLogin(EmbeddedDocument):
    googleId = StringField()          
    facebookId = StringField()        

# User Document
class User(Document):
    name = StringField(required=True)  
    email = StringField(
        required=True,
        unique=True,
        regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'  
    )
    password_hash = StringField(required=True)  
    social_logins = EmbeddedDocumentField(SocialLogin)  
    my_cookbooks = ListField(ReferenceField('MyCookbook'))  
    my_plates = ListField(ReferenceField('MyPlate'))
    my_cookbooks = ListField(ReferenceField('MyCookbook'))   
    created_at = DateTimeField(default=datetime.now(timezone.utc))  
    updated_at = DateTimeField(default=datetime.now(timezone.utc))  
    is_active = BooleanField(default=True)  

    @property
    def is_authenticated(self):
        return True  

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now(timezone.utc)  
        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return self.email  

    def delete_account(self):
        for cookbook in self.my_cookbooks:
            cookbook.delete()
        for plate in self.my_plates:
            plate.delete()
        self.delete()  

# Token Document for Authentication

class Token(Document):
    key = StringField(required=True, unique=True)
    user = ReferenceField(User, required=True)
    created = DateTimeField(default=datetime.now(timezone.utc))

    @classmethod
    def generate_token(cls, user):
        existing_token = Token.objects(user=user).first()
        if existing_token and not existing_token.is_expired():
            return existing_token
        new_token = Token(user=user)
        new_token.key = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
        new_token.save()
        return new_token

    def is_expired(self, expiration_hours=2):
        if self.created.tzinfo is None:
            self.created = self.created.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > (self.created + timedelta(hours=expiration_hours))

    def __str__(self):
        return f"Token for {self.user.email}"


# Media Embedded Document
class Media(EmbeddedDocument):
    type = StringField(choices=['image', 'video'], required=True)
    # file_id = StringField()  # GridFS file ID for the media file
    file_id = ObjectIdField(required=True)  # GridFS file ID for the media file
    url = URLField()  # URL to access the media file, if applicable
    file_path = StringField()  # File path for uploaded media (optional)

# IngredientAmount Embedded Document
class IngredientAmount(EmbeddedDocument):
    value = FloatField()  # Generic value field for single unit case
    unit = StringField()  # Generic unit field for single unit case
    us_value = FloatField()  # Optional: Quantity in US units
    us_unit = StringField()  # Optional: Unit for US measurement
    metric_value = FloatField()  # Optional: Quantity in Metric units
    metric_unit = StringField()  # Optional: Unit for Metric measurement

# Ingredient Embedded Document
class Ingredient(EmbeddedDocument):
    name = StringField(required=True)
    spoonacular_id = IntField()
    amount = EmbeddedDocumentField(IngredientAmount)
    media = ListField(EmbeddedDocumentField(Media))  # Replace separate photo and video fields with a list of Media

    def add_media(self, file, filename):
        media_file = MediaFile(file)
        file_id = media_file.save(filename)
        media_type = 'image' if 'image' in filename.lower() else 'video'
        self.media.append(Media(type=media_type, file_id=file_id))
        self.save()  # Save the document to persist changes

# Instruction Embedded Document
class Instruction(EmbeddedDocument):
    step_number = IntField(required=True)
    description = StringField(required=True)
    media = ListField(EmbeddedDocumentField(Media))  # Replace separate photo and video fields with a list of Media

    def add_media(self, file, filename):
        media_file = MediaFile(file)
        file_id = media_file.save(filename)
        media_type = 'image' if 'image' in filename.lower() else 'video'
        self.media.append(Media(type=media_type, file_id=file_id))
        self.save()  # Save the document to persist changes

# Recipe Document
class Recipe(Document):
    recipe_id = ObjectIdField(primary_key=True, default=ObjectId)
    title = StringField(required=True)
    description = StringField()
    keywords = ListField(StringField())
    servings = IntField(required=True)
    cook_time = StringField(required=True)
    ingredients = ListField(EmbeddedDocumentField(Ingredient))
    ingredients_single_block = StringField()  # New field for single block ingredients
    instructions = ListField(EmbeddedDocumentField(Instruction))
    instructions_single_block = StringField()  # New field for single block instructions
    my_plate_id = ObjectIdField()
    media = ListField(EmbeddedDocumentField(Media))  # General media for the recipe

    # New fields
    cuisine = ListField(StringField())  # Storing cuisines as a list
    diet = ListField(StringField())  # Storing diets as a list
    meal_type = ListField(StringField())  # Mapping and storing meal types as a list
    dish_type = ListField(StringField())  # Mapping and storing dish types as a list
    occasion = ListField(StringField())  # Storing occasions as a list

    created_at = DateTimeField(required=True, default=datetime.now(timezone.utc))
    updated_at = DateTimeField(required=True, default=datetime.now(timezone.utc))
    user_id = ReferenceField(User)

    meta = {'collection': 'recipes'}

    def delete(self, *args, **kwargs):
        # Delete associated media from GridFS
        for media in self.media:
            if media.file_id:
                settings.fs.delete(media.file_id)

        # Delete associated ingredients media from GridFS
        for ingredient in self.ingredients:
            for media in ingredient.media:
                if media.file_id:
                    settings.fs.delete(media.file_id)

        # Delete associated instructions media from GridFS
        for instruction in self.instructions:
            for media in instruction.media:
                if media.file_id:
                    settings.fs.delete(media.file_id)

        # Delete associated MyPlate document
        MyPlate.objects(recipe_id=self.recipe_id).delete()

        # Finally, delete the recipe itself
        super(Recipe, self).delete(*args, **kwargs)

# My Plate Document
class MyPlate(Document):
    my_plate_id = ObjectIdField(primary_key=True, default=ObjectId)  # Unique ID for My Plate
    user_id = ReferenceField(User, required=True)  # Reference to the user who created it
    recipe_id = ReferenceField(Recipe, required=True)  # Reference to the associated recipe

    meta = {'collection': 'my_plates'}


# Assuming User and Recipe documents are already defined as per your provided code

class MyCookbook(Document):
    """
    Represents a user's curated collection of recipes.
    """
    cookbook_id = ObjectIdField(primary_key=True, default=ObjectId)
    name = StringField(required=True, max_length=100)
    description = StringField(max_length=500)
    recipes = ListField(ReferenceField('Recipe'))  # List of Recipe references
    owner = ReferenceField('User', required=True, reverse_delete_rule=CASCADE)  # Reference to the owning User
    created_at = DateTimeField(default=datetime.now(timezone.utc))
    updated_at = DateTimeField(default=datetime.now(timezone.utc))
    is_public = BooleanField(default=False)  # Optionally, make cookbooks public

    meta = {'collection': 'my_cookbooks'}

    def save(self, *args, **kwargs):
        """
        Override save to update the `updated_at` timestamp.
        """
        self.updated_at = datetime.now(timezone.utc)
        super(MyCookbook, self).save(*args, **kwargs)

    def add_recipe(self, recipe):
        """
        Adds a recipe to the cookbook.
        """
        if recipe not in self.recipes:
            self.recipes.append(recipe)
            self.save()

    def remove_recipe(self, recipe):
        """
        Removes a recipe from the cookbook.
        """
        if recipe in self.recipes:
            self.recipes.remove(recipe)
            self.save()

    def __str__(self):
        return f"{self.name} by {self.owner.email}"



















# # Adding media to an ingredient
# recipe = Recipe.objects.get(id=recipe_id)
# ingredient = recipe.ingredients[0]
# ingredient.add_media(file, 'image.jpg')

# # Adding media to an instruction
# instruction = recipe.instructions[0]
# instruction.add_media(file, 'video.mp4')

# # Save the recipe document after modifying ingredients or instructions
# recipe.save()











# Old recipe documents



# # Ingredient Embedded Document
# class Ingredient(EmbeddedDocument):
#     name = StringField(required=True)
#     spoonacular_id = IntField()
#     amount = EmbeddedDocumentField(IngredientAmount)  # Flexibly handles single or dual-unit amounts
#     photo = StringField()  # Store file_id instead of URL
#     video = StringField()  # Store file_id instead of URL

#     def add_media(self, file, filename):
#         media_file = MediaFile(file)
#         file_id = media_file.save(filename)
#         # Check if the file is an image or video and update the relevant field
#         if 'image' in filename.lower():
#             self.photo = file_id
#         elif 'video' in filename.lower():
#             self.video = file_id
#         self.save()  # Save the document to persist changes



# # Instruction Embedded Document
# class Instruction(EmbeddedDocument):
#     step_number = IntField(required=True)
#     description = StringField(required=True)
#     photo = StringField()  # Store file_id instead of URL
#     video = StringField()  # Store file_id instead of URL

#     def add_media(self, file, filename):
#         media_file = MediaFile(file)
#         file_id = media_file.save(filename)
#         # Check if the file is an image or video and update the relevant field
#         if 'image' in filename.lower():
#             self.photo = file_id
#         elif 'video' in filename.lower():
#             self.video = file_id
#         self.save()  # Save the document to persist changes

# # Recipe Document
# class Recipe(Document):
#     recipe_id = ObjectIdField(primary_key=True, default=ObjectId)
#     title = StringField(required=True)
#     description = StringField()
#     keywords = ListField(StringField())
#     servings = IntField(required=True)
#     cook_time = StringField(required=True)
#     ingredients = ListField(EmbeddedDocumentField(Ingredient))
#     ingredients_single_block = StringField()  # New field for single block ingredients
#     instructions = ListField(EmbeddedDocumentField(Instruction))
#     instructions_single_block = StringField()  # New field for single block instructions
#     my_plate_id = ObjectIdField()
#     media = ListField(EmbeddedDocumentField(Media))
#     created_at = DateTimeField(required=True)
#     updated_at = DateTimeField(required=True)
#     user_id = ReferenceField(User)

#     meta = {'collection': 'recipes'}

#     def delete(self, *args, **kwargs):
#             # Delete associated media from GridFS
#             for media in self.media:
#                 if media.file_id:
#                     settings.fs.delete(media.file_id)

#             # Delete associated ingredients media from GridFS
#             for ingredient in self.ingredients:
#                 if ingredient.photo:
#                     settings.fs.delete(ingredient.photo)
#                 if ingredient.video:
#                     settings.fs.delete(ingredient.video)

#             # Delete associated instructions media from GridFS
#             for instruction in self.instructions:
#                 if instruction.photo:
#                     settings.fs.delete(instruction.photo)
#                 if instruction.video:
#                     settings.fs.delete(instruction.video)

#             # Delete associated MyPlate document
#             MyPlate.objects(recipe_id=self.recipe_id).delete()

#             # Finally, delete the recipe itself
#             super(Recipe, self).delete(*args, **kwargs)