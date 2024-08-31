import logging
from rest_framework import status, permissions, pagination
import hashlib
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import BaseAuthentication, TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from .models import User, Recipe, Ingredient, Instruction, MyPlate, Token, Media, IngredientAmount, SocialLogin, MyCookbook
from .serializers import UserSerializer
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound, Http404
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.utils.dateparse import parse_datetime
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from .GridFS import MediaFile
from social_django.utils import load_strategy, load_backend
from social_core.backends.google import GoogleOAuth2
from social_core.backends.facebook import FacebookOAuth2
from social_core.exceptions import AuthException
from django.contrib.auth import login
import requests
from io import BytesIO
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout as django_logout
from django.utils.translation import gettext_lazy as _
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.hashers import check_password
from users import transform_recipe_data
from .spoonacular import get_recipe_information
from django.core.cache import cache
from .spoonacular import search_recipes, search_recipes_by_ingredients
from hashlib import md5
from .my_cookbook_serializers import MyCookbookSerializer




import gridfs
from gridfs import GridFS
from django.urls import reverse


# Middleware for Token Validation
from mongoengine import DoesNotExist

import os
from mongoengine import connect
from dotenv import load_dotenv



# Load environment variables from the .env file
load_dotenv()

# Retrieve the MongoDB URI from the .env file
MONGODB_URI = os.getenv("MONGODB_URI")

# Establish a connection to MongoDB
# mongodb_connection = connect(host=MONGODB_URI)

# Set up logging for the application
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GridFS centralized configuration
fs = settings.GRIDFS_FS

# Custom 404 view
def custom_404_view(request, exception):
    """Render a custom 404 error page."""
    return render(request, '404.html', status=404)

# Middleware for Token Validation
class TokenMiddleware(MiddlewareMixin):
    """Middleware to validate the authentication token on every request."""
    
    def process_request(self, request):
        """Process each request to validate the token and set the user."""
        token_key = request.COOKIES.get('auth_token')
        if token_key:
            try:
                token = Token.objects.get(key=token_key)
                
                # Check if the user associated with the token exists
                if not token.user:
                    raise DoesNotExist("User does not exist.")

                # If the user exists, then check if the token is expired
                if token.is_expired():
                    raise AuthenticationFailed('Token has expired.')
                
                request.user = token.user
            except Token.DoesNotExist:
                request.user = None
                if not request.path.startswith('/api/logout'):  # Skip redirection for logout
                    response = redirect('user-login')
                    response.delete_cookie('auth_token')  # Delete the invalid token
                    return response
            except DoesNotExist:
                request.user = None
                if not request.path.startswith('/api/logout'):  # Skip redirection for logout
                    response = redirect('user-login')
                    response.delete_cookie('auth_token')  # Delete the invalid token
                    return response
        else:
            request.user = None

    def process_exception(self, request, exception):
        """Handle authentication exceptions."""
        if isinstance(exception, AuthenticationFailed):
            response = redirect('user-login')
            response.delete_cookie('auth_token')  # Delete the expired token
            return response

# Custom Token Authentication
class CookieTokenAuthentication(BaseAuthentication):
    """Custom authentication class to handle token-based authentication via cookies."""
    def authenticate(self, request):
        """Authenticate the user based on the token in the cookie."""
        token_key = request.COOKIES.get('auth_token')
        if not token_key:
            return None  # No token, no authentication

        try:
            token = Token.objects.get(key=token_key)
            if token.is_expired():
                token.delete()
                raise AuthenticationFailed('Token has expired.')
            return (token.user, token)
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token.')

# Home view
def home(request):
    """Render the home page."""
    return HttpResponse("Welcome to the Recipe-z Project!")

# User Registration
class UserRegister(APIView):
    """View to handle user registration."""
    permission_classes = [permissions.AllowAny]  # Allow any user to register

    def get(self, request):
        """Render the registration page."""
        return render(request, 'registration/register.html')

    def post(self, request):
        """Handle user registration form submission."""
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()

            # Send confirmation email
            send_mail(
                'Confirm your account',
                'Click the link to confirm your account: <link>',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return Response({"message": "User registered successfully! Check your email to confirm your account."}, 
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# User Deletion
class UserDeleteView(APIView):
    """View to handle user deletion."""
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Render the user deletion confirmation page."""
        return render(request, 'delete/delete_user.html', {'error_message': None})

    def post(self, request):
        """Handle user deletion form submission."""
        user_id = request.data.get('user_id')

        if not self.is_valid_object_id(user_id):
            return render(request, 'delete/delete_user.html', {
                'error_message': "Please enter a valid user ID."
            })

        try:
            user = User.objects.get(id=ObjectId(user_id))
            # Delete associated tokens
            Token.objects.filter(user=user).delete()
            user.delete()
            logger.info(f"User and associated tokens deleted: {user_id}")
            return render(request, 'delete/delete_user.html', {
                'success_message': "User deleted successfully."
            })
        except User.DoesNotExist:
            logger.error(f"User with ID {user_id} does not exist.")
            return render(request, 'delete/delete_user.html', {
                'error_message': "User with the given ID does not exist. Please try again."
            })
        except Exception as e:
            logger.error(f"An error occurred while deleting user {user_id}: {str(e)}")
            return render(request, 'delete/delete_user.html', {
                'error_message': f"An error occurred: {str(e)}"
            })

    def is_valid_object_id(self, user_id):
        """Check if the provided user ID is a valid ObjectId."""
        return ObjectId.is_valid(user_id)

# Facebook Login
class FacebookLogin(APIView):
    """View to handle Facebook OAuth login."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Handle the Facebook OAuth callback."""
        code = request.GET.get('code')
        if not code:
            return Response({'error': 'No code provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Exchange code for access token
        token_url = "https://graph.facebook.com/v10.0/oauth/access_token"
        token_params = {
            'client_id': settings.SOCIAL_AUTH_FACEBOOK_KEY,
            'client_secret': settings.SOCIAL_AUTH_FACEBOOK_SECRET,
            'redirect_uri': settings.FACEBOOK_REDIRECT_URI,
            'code': code
        }

        token_response = requests.get(token_url, params=token_params)
        token_json = token_response.json()

        if 'access_token' not in token_json:
            return Response({'error': 'Failed to retrieve access token'}, status=status.HTTP_400_BAD_REQUEST)
        
        access_token = token_json['access_token']

        # Step 2: Fetch user info using the access token
        user_info_url = "https://graph.facebook.com/me"
        user_info_params = {
            'fields': 'id,name,email',
            'access_token': access_token
        }
        
        user_info_response = requests.get(user_info_url, params=user_info_params)
        user_info = user_info_response.json()

        if 'email' not in user_info:
            return Response({'error': 'Failed to retrieve user information'}, status=status.HTTP_400_BAD_REQUEST)

        email = user_info.get('email')
        name = user_info.get('name')
        facebook_id = user_info.get('id')

        # Check if user exists or create a new one
        user, created = User.objects.get_or_create(email=email, defaults={'name': name})

        if created:
            user.social_logins = SocialLogin(facebookId=facebook_id)
            user.save()
        else:
            user.social_logins.facebookId = facebook_id
            user.save()

        # Log in the user
        login(request, user)

        return redirect('home')

# Google Login
class GoogleLogin(APIView):
    """View to handle Google OAuth login."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Handle the Google OAuth callback."""
        code = request.GET.get('code')
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
            'code': code,
        }

        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()

        if 'access_token' not in token_json:
            return Response({'error': 'Failed to retrieve access token'}, status=status.HTTP_400_BAD_REQUEST)

        access_token = token_json['access_token']
        user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        user_info_response = requests.get(user_info_url, headers={'Authorization': f'Bearer {access_token}'})
        user_info = user_info_response.json()

        email = user_info.get('email')
        name = user_info.get('name')
        uid = user_info.get('id')

        # Check if user exists or create a new one
        user, created = User.objects.get_or_create(email=email, defaults={'name': name})

        if created:
            user.social_logins = SocialLogin(googleId=uid)
            user.save()
        else:
            user.social_logins.googleId = uid
            user.save()

        # Log in the user
        login(request, user)

        return redirect('home')

# User Login

class UserLogin(APIView):
    """View to handle user login."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Render the login page or delete the token if the user doesn't exist."""
        token_key = request.COOKIES.get('auth_token')
        if token_key:
            try:
                token = Token.objects.get(key=token_key)
                if token.user:
                    return render(request, 'login/login_user.html', {
                        'message': f"Welcome back, {token.user.name}! You are already logged in."
                    })
                else:
                    response = render(request, 'login/login_user.html')
                    response.delete_cookie('auth_token')
                    return response
            except Token.DoesNotExist:
                pass

        return render(request, 'login/login_user.html')

    def post(self, request):
        """Handle user login form submission."""
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects(email=email).first()
        if not user:
            logger.error(f"Login failed for email: {email} (user not found)")
            return Response({'error': "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the password is correct
        if not self.check_password(password, user.password_hash):
            logger.error(f"Login failed for email: {email} (incorrect password)")
            return Response({'error': "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate or get the existing token
        token = Token.generate_token(user)
        token_key = token.key

        # Set the authentication token in the cookie
        response = render(request, 'login/login_user.html', {
            'message': f"Login successful! Welcome, {user.name}."
        })
        response.set_cookie(
            key='auth_token',
            value=token_key,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='Strict'
        )

        logger.info(f"Login successful for user: {user.email}")
        return response

    def check_password(self, plain_password, hashed_password):
        """Check if the plain password matches the hashed password."""
        return check_password(plain_password, hashed_password)



# Logout
class LogoutView(APIView):
    """View to handle user logout."""
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        """Handle logout by invalidating the token and clearing the cookie."""
        token_key = request.COOKIES.get('auth_token')
        if token_key:
            try:
                token = Token.objects.get(key=token_key)
                if not token.is_expired():
                    token.delete()
                    response = Response({"detail": _("Successfully logged out.")}, status=status.HTTP_200_OK)
                else:
                    response = Response({"detail": _("Token is expired or invalid.")}, status=status.HTTP_400_BAD_REQUEST)
            except Token.DoesNotExist:
                response = Response({"detail": _("Invalid token.")}, status=status.HTTP_400_BAD_REQUEST)
        else:
            response = Response({"detail": _("Token not provided.")}, status=status.HTTP_400_BAD_REQUEST)
        
        response.delete_cookie('auth_token')
        return response


# Recipe Views

class RecipeListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    authentication_classes = [CookieTokenAuthentication]

    def get(self, request):
        return render(request, 'recipes/recipe_form.html')

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        logger.info(f"Received POST data: {request.data}")

        title = request.data.get('title')
        description = request.data.get('description')
        keywords = request.data.get('keywords', '')
        servings = request.data.get('servings')
        cook_time = request.data.get('cook_time')
        ingredients_data = request.data.get('ingredients', [])
        ingredients_single_block = request.data.get('ingredients_single_block', '')
        instructions_data = request.data.get('instructions', [])
        instructions_single_block = request.data.get('instructions_single_block', '')
        media_data = request.data.get('media', [])

        recipe = Recipe(
            title=title,
            description=description,
            keywords=[keyword.strip() for keyword in keywords.split(',') if keyword.strip()],
            servings=servings,
            cook_time=cook_time,
            ingredients=ingredients_data if not ingredients_single_block else [],
            ingredients_single_block=ingredients_single_block,
            instructions=instructions_data if not instructions_single_block else [],
            instructions_single_block=instructions_single_block,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        recipe.save()

        if ingredients_data and not ingredients_single_block:
            self.add_ingredients(recipe, ingredients_data)
        if instructions_data and not instructions_single_block:
            self.add_instructions(recipe, instructions_data)
        
        recipe.media = [self.handle_media(media) for media in media_data]
        recipe.save()

        # Create MyPlate instance and update user's my_plates field
        my_plate = MyPlate(user_id=request.user.id, recipe_id=recipe.id)
        my_plate.save()
        user = User.objects.get(id=request.user.id)
        user.my_plates.append(my_plate)
        user.save()
        recipe.my_plate_id = my_plate.my_plate_id
        recipe.save()

        logger.info(f"Recipe created: {recipe}")
        return JsonResponse({'message': 'Recipe created successfully!'}, status=status.HTTP_201_CREATED)

    def add_ingredients(self, recipe, ingredients_data):
        for ingredient_data in ingredients_data:
            amount_data = ingredient_data.get('amount', None)
            amount = IngredientAmount(
                value=amount_data.get('value') if amount_data else None,
                unit=amount_data.get('unit') if amount_data else None,
                us_value=amount_data.get('us_value') if amount_data else None,
                us_unit=amount_data.get('us_unit') if amount_data else None,
                metric_value=amount_data.get('metric_value') if amount_data else None,
                metric_unit=amount_data.get('metric_unit') if amount_data else None
            ) if amount_data else None
            ingredient = Ingredient(
                name=ingredient_data['name'],
                spoonacular_id=ingredient_data.get('spoonacular_id', None),
                amount=amount,
                photo=self.handle_media(ingredient_data.get('photo')),
                video=self.handle_media(ingredient_data.get('video'))
            )
            recipe.ingredients.append(ingredient)

    def add_instructions(self, recipe, instructions_data):
        for instruction_data in instructions_data:
            instruction = Instruction(
                step_number=instruction_data['step_number'],
                description=instruction_data['description'],
                photo=self.handle_media(instruction_data.get('photo')),
                video=self.handle_media(instruction_data.get('video'))
            )
            recipe.instructions.append(instruction)

    def handle_media(self, media_data):
        if isinstance(media_data, dict):
            file_id = media_data.get('file_id')
            url = media_data.get('url')
            if file_id:
                return Media(type=media_data.get('type'), url=url, file_id=file_id)
            elif url:
                # First, check if this media is already in the cache
                cache_key = f"media_{hashlib.md5(url.encode()).hexdigest()}"
                cached_media = cache.get(cache_key)
                if cached_media:
                    return Media(type=media_data.get('type'), url=url, file_id=cached_media.gridfs.grid_id)
                else:
                    # Use the MediaFile class to handle the download and storage
                    media_file = MediaFile.from_url(url, "recipe_image")
                    cache.set(cache_key, media_file, timeout=60*60)  # Cache for 1 hour
                    return Media(type=media_data.get('type'), url=url, file_id=media_file.gridfs.grid_id)
        return None

class RecipeRetrieveUpdateDestroyView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_media_url(self, file_id):
        """Generate a URL to access the media file."""
        return self.request.build_absolute_uri(reverse('serve_media', args=[file_id]))

    def generate_cache_key(self, pk):
        """Generate a cache key using hashlib.md5"""
        return f"recipe_{hashlib.md5(str(pk).encode()).hexdigest()}"

    def get(self, request, pk):
        logger.info(f"Fetching recipe with ID: {pk}")
        cache_key = self.generate_cache_key(pk)
        cached_recipe = cache.get(cache_key)

        if cached_recipe:
            logger.info(f"Returning cached recipe for ID: {pk}")
            return JsonResponse(cached_recipe)

        try:
            recipe_id = ObjectId(pk)
            recipe = Recipe.objects.get(id=recipe_id)
        except (InvalidId, Recipe.DoesNotExist):
            logger.error(f"Recipe not found for ID: {pk}")
            return JsonResponse({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)

        # Construct the response data
        data = {
            'title': recipe.title,
            'description': recipe.description,
            'keywords': recipe.keywords,
            'servings': recipe.servings,
            'cook_time': recipe.cook_time,
            'ingredients': [
                {
                    'name': ingredient.name,
                    'amount': {
                        'value': ingredient.amount.value if ingredient.amount else None,
                        'unit': ingredient.amount.unit if ingredient.amount else None,
                        'us_value': ingredient.amount.us_value if ingredient.amount else None,
                        'us_unit': ingredient.amount.us_unit if ingredient.amount else None,
                        'metric_value': ingredient.amount.metric_value if ingredient.amount else None,
                        'metric_unit': ingredient.amount.metric_unit if ingredient.amount else None,
                    },
                    'spoonacular_id': ingredient.spoonacular_id,
                    'photo': self.get_media_url(ingredient.photo.file_id) if ingredient.photo else None,
                    'video': self.get_media_url(ingredient.video.file_id) if ingredient.video else None
                } for ingredient in recipe.ingredients
            ] if not recipe.ingredients_single_block else recipe.ingredients_single_block,
            'instructions': [
                {
                    'step_number': instruction.step_number,
                    'description': instruction.description,
                    'photo': self.get_media_url(instruction.photo.file_id) if instruction.photo else None,
                    'video': self.get_media_url(instruction.video.file_id) if instruction.video else None
                } for instruction in recipe.instructions
            ] if not recipe.instructions_single_block else recipe.instructions_single_block,
            'media': [
                {
                    'type': media.type,
                    'url': self.get_media_url(media.file_id) if media.file_id else media.url,
                    'file_id': media.file_id
                } for media in recipe.media
            ],
            'spoonacular_id': recipe.spoonacular_id
        }

        cache.set(cache_key, data, timeout=60*60)  # Cache the recipe for 1 hour
        return JsonResponse(data)

    def put(self, request, pk):
        logger.info(f"Updating recipe with ID: {pk}")
        try:
            recipe_id = ObjectId(pk)
            recipe = Recipe.objects.get(id=recipe_id)
        except (InvalidId, Recipe.DoesNotExist):
            logger.error(f"Recipe not found for ID: {pk}")
            return JsonResponse({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)

        # Ensure user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        # Update recipe fields
        recipe.title = request.data.get('title', recipe.title)
        recipe.description = request.data.get('description', recipe.description)
        recipe.servings = request.data.get('servings', recipe.servings)
        recipe.cook_time = request.data.get('cook_time', recipe.cook_time)
        recipe.updated_at = datetime.now(timezone.utc)

        # Handle ingredients and instructions
        ingredients_data = request.data.get('ingredients', [])
        ingredients_single_block = request.data.get('ingredients_single_block', '')
        recipe.ingredients = []
        if ingredients_data and not ingredients_single_block:
            self.add_ingredients(recipe, ingredients_data)
        elif ingredients_single_block:
            recipe.ingredients_single_block = ingredients_single_block

        instructions_data = request.data.get('instructions', [])
        instructions_single_block = request.data.get('instructions_single_block', '')
        recipe.instructions = []
        if instructions_data and not instructions_single_block:
            self.add_instructions(recipe, instructions_data)
        elif instructions_single_block:
            recipe.instructions_single_block = instructions_single_block

        # Handle media updates
        media_data = request.data.get('media', [])
        updated_media = []
        for media in media_data:
            if 'url' in media:
                file_id = self.save_media_to_gridfs(media['url'])
                updated_media.append(Media(type=media['type'], file_id=file_id))
            else:
                updated_media.append(Media(type=media['type'], file_id=media.get('file_id')))

        recipe.media = updated_media
        recipe.save()

        # Invalidate the cache
        cache_key = self.generate_cache_key(pk)
        cache.delete(cache_key)

        logger.info(f"Recipe updated: {recipe}")
        return JsonResponse({'message': 'Recipe updated successfully!'})

    def delete(self, request, pk):
        logger.info(f"Deleting recipe with ID: {pk}")
        try:
            recipe_id = ObjectId(pk)
            recipe = Recipe.objects.get(id=recipe_id)

            # Collect media file IDs for deletion
            media_file_ids = [media.file_id for media in recipe.media]
            
            # Delete media from GridFS
            for file_id in media_file_ids:
                settings.fs.delete(file_id)
            
            # Delete associated ingredients and instructions media from GridFS
            for ingredient in recipe.ingredients:
                if ingredient.photo:
                    settings.fs.delete(ingredient.photo.file_id)
                if ingredient.video:
                    settings.fs.delete(ingredient.video.file_id)

            for instruction in recipe.instructions:
                if instruction.photo:
                    settings.fs.delete(instruction.photo.file_id)
                if instruction.video:
                    settings.fs.delete(instruction.video.file_id)

            # Delete the recipe
            recipe.delete()

            # Invalidate the cache
            cache_key = self.generate_cache_key(pk)
            cache.delete(cache_key)
            
            logger.info(f"Recipe deleted: {pk}")
            return JsonResponse({'message': 'Recipe deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)
        
        except (InvalidId, Recipe.DoesNotExist):
            logger.error(f"Recipe not found for ID: {pk}")
            return JsonResponse({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting recipe: {e}")
            return JsonResponse({'error': 'An error occurred while deleting the recipe.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def save_media_to_gridfs(self, url):
        response = requests.get(url)
        response.raise_for_status()
        file_data = BytesIO(response.content)
        file_id = settings.fs.put(file_data, filename=url.split('/')[-1])
        return file_id

    def add_ingredients(self, recipe, ingredients_data):
        for ingredient_data in ingredients_data:
            amount_data = ingredient_data.get('amount', None)
            amount = IngredientAmount(
                value=amount_data.get('value') if amount_data else None,
                unit=amount_data.get('unit') if amount_data else None,
                us_value=amount_data.get('us_value') if amount_data else None,
                us_unit=amount_data.get('us_unit') if amount_data else None,
                metric_value=amount_data.get('metric_value') if amount_data else None,
                metric_unit=amount_data.get('metric_unit') if amount_data else None
            ) if amount_data else None
            ingredient = Ingredient(
                name=ingredient_data['name'],
                spoonacular_id=ingredient_data.get('spoonacular_id', None),
                amount=amount,
                photo=self.handle_media(ingredient_data.get('photo')),
                video=self.handle_media(ingredient_data.get('video'))
            )
            recipe.ingredients.append(ingredient)

    def add_instructions(self, recipe, instructions_data):
        for instruction_data in instructions_data:
            instruction = Instruction(
                step_number=instruction_data['step_number'],
                description=instruction_data['description'],
                photo=self.handle_media(instruction_data.get('photo')),
                video=self.handle_media(instruction_data.get('video'))
            )
            recipe.instructions.append(instruction)

    def handle_media(self, media_data):
        if isinstance(media_data, dict):
            file_id = media_data.get('file_id')
            url = media_data.get('url')
            if file_id:
                return Media(type=media_data.get('type'), url=url, file_id=file_id)
            elif url:
                # Use the MediaFile class to handle the download and storage
                media_file = MediaFile.from_url(url, "recipe_image")
                return Media(type=media_data.get('type'), url=media_file.url, file_id=media_file.file_id)
        return None

    # Spoonacular Recipe Views

class CachedRecipeSearchView(APIView):
    def get(self, request, *args, **kwargs):
        # Extract search parameters from the request
        include_ingredients = request.query_params.getlist('include_ingredients')
        exclude_ingredients = request.query_params.getlist('exclude_ingredients')
        cuisine = request.query_params.get('cuisine')
        diet = request.query_params.get('diet')
        meal_type = request.query_params.get('meal_type')
        max_time = request.query_params.get('max_time')
        dish_type = request.query_params.get('dish_type')
        occasion = request.query_params.get('occasion')

        # Build query parameters for Spoonacular API complexSearch endpoint
        query_params = {
            'cuisine': cuisine,
            'diet': diet,
            'type': meal_type,
            'maxReadyTime': max_time,
            'dishType': dish_type,
            'query': occasion,  # Using 'query' for occasions
        }
        query_params = {k: v for k, v in query_params.items() if v}

        # Generate a cache key based on query parameters and included/excluded ingredients
        cache_key = md5(
            str(query_params).encode() +
            str(include_ingredients).encode() +
            str(exclude_ingredients).encode()
        ).hexdigest()

        # Check if the results are cached
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        # Perform ingredient-based search
        ingredient_based_recipes = []
        if include_ingredients or exclude_ingredients:
            ingredient_based_recipes = search_recipes_by_ingredients(
                ingredients=include_ingredients,
                exclude_ingredients=exclude_ingredients
            ) or {}

        # Collect Spoonacular IDs from the ingredient-based search results
        ingredient_based_spoonacular_ids = set(
            recipe['id'] for recipe in ingredient_based_recipes.get('results', []) if recipe.get('id')
        )

        # Perform the database search
        db_query_params = {
            'cuisine': cuisine,
            'diet': diet,
            'meal_type': meal_type,
            'max_time': max_time,
            'dish_type': dish_type,
            'occasion': occasion
        }
        db_recipes = Recipe.objects.filter(
            **{k: v for k, v in db_query_params.items() if v}
        )

        # Collect Spoonacular IDs from the database recipes
        db_spoonacular_ids = set(recipe.spoonacular_id for recipe in db_recipes if recipe.spoonacular_id)

        # Combine Spoonacular IDs from both ingredient-based search and database search
        all_spoonacular_ids = ingredient_based_spoonacular_ids.union(db_spoonacular_ids)

        # Perform advanced filter search
        advanced_filter_recipes = []
        if not include_ingredients and not exclude_ingredients:
            advanced_filter_recipes = search_recipes(query_params) or {}

        # Fetch additional recipes from Spoonacular API, excluding those with IDs already in the database
        additional_spoonacular_recipes = []
        if not include_ingredients and not exclude_ingredients:
            api_results = search_recipes(query_params)
            if api_results:
                additional_spoonacular_recipes = [
                    recipe for recipe in api_results.get('results', []) 
                    if recipe['id'] not in all_spoonacular_ids
                ]

        # Combine results from all sources
        combined_results = {
            'results': (
                list(db_recipes.values('id', 'title', 'description', 'image')) +  # Adjust fields as necessary
                ingredient_based_recipes.get('results', []) +
                additional_spoonacular_recipes
            )
        }

        # Remove duplicates if necessary
        seen = set()
        unique_results = []
        for recipe in combined_results['results']:
            if recipe['id'] not in seen:
                seen.add(recipe['id'])
                unique_results.append(recipe)
        combined_results['results'] = unique_results

        # Cache the response for future requests
        cache.set(cache_key, combined_results, timeout=60*60)  # Cache for 1 hour

        return Response(combined_results, status=status.HTTP_200_OK)
    
class AddSpoonacularRecipeView(APIView):
    def get(self, request, recipe_id, *args, **kwargs):
        # Fetch recipe data from Spoonacular using the provided recipe_id
        response_data = get_recipe_information(recipe_id)

        if not response_data:
            return Response({'error': 'Failed to fetch recipe data from Spoonacular'}, status=status.HTTP_404_NOT_FOUND)

        # Transform the fetched data
        recipe_data = transform_recipe_data(response_data).get('recipeDetails')

        if not recipe_data:
            return Response({'error': 'Invalid recipe data from Spoonacular'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the recipe already exists
        if Recipe.objects(recipe_id=recipe_id).first():
            # Recipe already exists, skip adding
            return Response({'message': 'Recipe already exists, skipping.'}, status=status.HTTP_200_OK)

        # Create and save new recipe with additional fields
        recipe = Recipe(
            recipe_id=recipe_id,
            title=recipe_data.get('title', ''),
            description=recipe_data.get('description', ''),
            servings=recipe_data.get('servings', 1),
            cook_time=recipe_data.get('cookTime', ''),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            user_id=None,  # Assuming no user association for automated recipes
            cuisine=recipe_data.get('cuisine', []),  # New field
            diet=recipe_data.get('diet', []),  # New field
            meal_type=recipe_data.get('meal_type', []),  # New field
            dish_type=recipe_data.get('dish_type', []),  # New field
            occasion=recipe_data.get('occasion', [])  # New field
        )

        # Download and save recipe media (thumbnail)
        recipe_thumbnail_url = recipe_data.get('photo')
        if recipe_thumbnail_url:
            recipe_media_id = self.save_media_to_gridfs(recipe_thumbnail_url)
            recipe.media = [Media(type='image', file_id=recipe_media_id)]

        # Add ingredients
        ingredients = []
        for ingredient_data in recipe_data.get('ingredients', []):
            ingredient = Ingredient(
                name=ingredient_data.get('name', ''),
                spoonacular_id=ingredient_data.get('id'),
                amount=self.create_ingredient_amount(ingredient_data.get('amount', {}))
            )
            if ingredient_data.get('image'):
                ingredient_media_id = self.save_media_to_gridfs(ingredient_data['image'])
                ingredient.add_media(file=None, filename=ingredient_data['image'])  # Assume image URL is used to fetch
            ingredients.append(ingredient)

        recipe.ingredients = ingredients

        # Add instructions
        instructions = []
        for instruction_data in recipe_data.get('instructions', []):
            instruction = Instruction(
                step_number=instruction_data.get('number'),
                description=instruction_data.get('step')
            )
            instructions.append(instruction)

        recipe.instructions = instructions

        # Save the recipe
        recipe.save()
        return Response({'message': 'Recipe added successfully'}, status=status.HTTP_201_CREATED)

# For retrieving metadata about a Media file. Not Serving the file itself.
class MediaRetrieveView(APIView):

    def get(self, request, media_id):
        try:
            # Attempt to retrieve media from the Recipe document
            recipe = Recipe.objects(media__file_id=media_id).first()
            if recipe:
                media = next(m for m in recipe.media if m.file_id == media_id)
            else:
                # Attempt to retrieve media from Ingredient or Instruction
                recipe = Recipe.objects(ingredients__photo=media_id).first()
                if recipe:
                    media = next(i for i in recipe.ingredients if i.photo == media_id)
                else:
                    recipe = Recipe.objects(instructions__photo=media_id).first()
                    if recipe:
                        media = next(inst for inst in recipe.instructions if inst.photo == media_id)
                    else:
                        raise DoesNotExist

            data = {
                "file_id": media.file_id,
                "type": media.type,
                "url": media.url,
                "file_path": media.file_path,
            }
            return Response(data, status=status.HTTP_200_OK)
        except DoesNotExist:
            return Response({"error": "Media not found"}, status=status.HTTP_404_NOT_FOUND)

# Get media from cache or GridFS
def get_media_from_cache(file_id):
    cache_key = f"media_{file_id}"
    media = cache.get(cache_key)
    if not media:
        try:
            media = settings.fs.get(file_id)
            cache.set(cache_key, media, timeout=60*60)  # Cache for 1 hour
        except DoesNotExist:
            media = None
    return media

# Serving the media file itself
class ServeMediaView(APIView):
    def get(self, request, media_id, *args, **kwargs):
        try:
            # Attempt to retrieve media from cache
            media = get_media_from_cache(media_id)
            if not media:
                raise Http404("Media file does not exist")

            # Return the media file as an HTTP response
            response = HttpResponse(media.read(), content_type=media.content_type)
            response['Content-Disposition'] = f'inline; filename="{media.filename}"'
            
            return response

        except Http404:
            return Http404("Media file does not exist")
        except Exception as e:
            return Response({"detail": str(e)}, status=500)

# My Cookbook Views

class MyCookbookListCreateView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cookbooks = MyCookbook.objects(owner=request.user)
        serializer = MyCookbookSerializer(cookbooks, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = MyCookbookSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class MyCookbookDetailView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, cookbook_id):
        cookbook = MyCookbook.objects.get(cookbook_id=cookbook_id, owner=request.user)
        serializer = MyCookbookSerializer(cookbook)
        return Response(serializer.data)

    def put(self, request, cookbook_id):
        cookbook = MyCookbook.objects.get(cookbook_id=cookbook_id, owner=request.user)
        serializer = MyCookbookSerializer(cookbook, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, cookbook_id):
        cookbook = MyCookbook.objects.get(cookbook_id=cookbook_id, owner=request.user)
        cookbook.delete()
        return Response(status=204)

class AddRecipeToCookbookView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, cookbook_id):
        cookbook = MyCookbook.objects.get(cookbook_id=cookbook_id, owner=request.user)
        recipe_id = request.data.get('recipe_id')
        try:
            recipe = Recipe.objects.get(recipe_id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({'error': 'Recipe not found'}, status=404)
        cookbook.add_recipe(recipe)
        serializer = MyCookbookSerializer(cookbook)
        return Response(serializer.data, status=200)

class RemoveRecipeFromCookbookView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, cookbook_id):
        cookbook = MyCookbook.objects.get(cookbook_id=cookbook_id, owner=request.user)
        recipe_id = request.data.get('recipe_id')
        try:
            recipe = Recipe.objects.get(recipe_id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({'error': 'Recipe not found'}, status=404)
        cookbook.remove_recipe(recipe)
        serializer = MyCookbookSerializer(cookbook)
        return Response(serializer.data, status=200)









































# # Recipe views
# class RecipePagination(pagination.PageNumberPagination):
#     page_size = 10
#     page_size_query_param = 'page_size'
#     max_page_size = 100


# class RecipeListCreateView(APIView):
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]

#     def get(self, request):
#         recipes = Recipe.objects.all()
#         serializer = RecipeSerializer(recipes, many=True)
#         return Response(serializer.data)

#     def post(self, request):
#         logger.info(f"Received POST data: {request.data}")

#         # Handle recipe creation as before
#         serializer = RecipeSerializer(data=request.data)
#         if serializer.is_valid():
#             recipe = serializer.save()
#             logger.info(f"Recipe created: {recipe}")
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
        
#         logger.error(f"Recipe creation failed: {serializer.errors}")
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def create_recipe(self, request):
#         serializer = RecipeSerializer(data=request.data)
#         if serializer.is_valid():
#             recipe = serializer.save()

#             # Handle keywords: Parse comma-separated keywords
#             keywords = request.data.get('keywords', '')
#             recipe.keywords = [keyword.strip() for keyword in keywords.split(',') if keyword.strip()]

#             # Create MyPlate instance
#             my_plate = MyPlate(user_id=request.user.id, recipe_id=recipe.id)
#             my_plate.save()  # Automatically generates my_plate_id

#             # Update the User's my_plates field
#             user = User.objects.get(id=request.user.id)
#             user.my_plates.append(my_plate)
#             user.save()

#             # Update recipe with my_plate_id
#             recipe.my_plate_id = my_plate.my_plate_id
#             recipe.save()

#             # Process ingredients
#             self.add_ingredients(recipe, request.data.get('ingredients', []))

#             # Process instructions
#             self.add_instructions(recipe, request.data.get('instructions', []))

#             recipe.save()
#             logger.info(f"Recipe created: {serializer.data}")
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
        
#         logger.error(f"Recipe creation failed: {serializer.errors}")
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def add_ingredients(self, recipe, ingredients_data):
#         # Handle both step-by-step and single block ingredients input
#         if isinstance(ingredients_data, str):  # Single block
#             single_block_ingredients = ingredients_data.split(',')
#             for ingredient in single_block_ingredients:
#                 ingredient = ingredient.strip()
#                 if ingredient:  # Avoid empty strings
#                     recipe.ingredients.append(Ingredient(name=ingredient))
#         else:  # Step-by-step
#             for ingredient_data in ingredients_data:
#                 # Handling dual-unit and single-unit measurements
#                 if 'amount' in ingredient_data:
#                     amount_data = ingredient_data['amount']
#                     amount = IngredientAmount(
#                         value=amount_data.get('value'),
#                         unit=amount_data.get('unit'),
#                         us_value=amount_data.get('us', {}).get('value'),
#                         us_unit=amount_data.get('us', {}).get('unit'),
#                         metric_value=amount_data.get('metric', {}).get('value'),
#                         metric_unit=amount_data.get('metric', {}).get('unit')
#                     )
#                 else:
#                     amount = None

#                 ingredient = Ingredient(
#                     name=ingredient_data['name'],
#                     spoonacular_id=ingredient_data.get('spoonacular_id', None),
#                     amount=amount
#                 )
#                 recipe.ingredients.append(ingredient)

#     def add_instructions(self, recipe, instructions_data):
#         # Handle both step-by-step and single block instructions input
#         if isinstance(instructions_data, str):  # Single block
#             recipe.instructions.append(Instruction(description=instructions_data))
#         else:  # Step-by-step
#             for instruction_data in instructions_data:
#                 instruction = Instruction(
#                     step_number=instruction_data['step_number'],
#                     description=instruction_data['description'],
#                     photo=instruction_data.get('photo', None),
#                     video=instruction_data.get('video', None)
#                 )
#                 recipe.instructions.append(instruction)


# class RecipeRetrieveUpdateDestroyView(APIView):
#     authentication_classes = [CookieTokenAuthentication]
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request, pk):
#         logger.info(f"Fetching recipe with ID: {pk}")
#         try:
#             recipe_id = ObjectId(pk)
#             recipe = Recipe.objects.get(id=recipe_id)  # Use ObjectId with MongoEngine
#         except (InvalidId, Recipe.DoesNotExist):
#             logger.error(f"Recipe not found for ID: {pk}")
#             return Response(status=status.HTTP_404_NOT_FOUND)

#         serializer = RecipeSerializer(recipe)
#         return Response(serializer.data)

#     def put(self, request, pk):
#         logger.info(f"Updating recipe with ID: {pk}")
#         try:
#             recipe_id = ObjectId(pk)
#             recipe = Recipe.objects.get(id=recipe_id)  # Use ObjectId with MongoEngine
#         except (InvalidId, Recipe.DoesNotExist):
#             logger.error(f"Recipe not found for ID: {pk}")
#             return Response(status=status.HTTP_404_NOT_FOUND)

#         serializer = RecipeSerializer(recipe, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             logger.info(f"Recipe updated: {serializer.data}")
#             return Response(serializer.data)
#         logger.error(f"Update failed: {serializer.errors}")
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk):
#         logger.info(f"Deleting recipe with ID: {pk}")
#         try:
#             recipe_id = ObjectId(pk)
#             recipe = Recipe.objects.get(id=recipe_id)  # Use ObjectId with MongoEngine
#             recipe.delete()
#             logger.info(f"Recipe deleted: {pk}")
#             return Response(status=status.HTTP_204_NO_CONTENT)
#         except (ObjectId.InvalidId, Recipe.DoesNotExist):
#             logger.error(f"Recipe not found for ID: {pk}")
#             return Response(status=status.HTTP_404_NOT_FOUND)


# def recipe_form_view(request):
#     # Render the HTML template without needing to process JSON
#     return render(request, 'recipes/recipe_form.html')



# Newer Views than what is above...._______________________________________________________________________________________________________________________


# class RecipeRetrieveUpdateDestroyView(APIView):
#     authentication_classes = [CookieTokenAuthentication]
#     permission_classes = [permissions.IsAuthenticated]

#     def get_media_url(self, file_id):
#         """Generate a URL to access the media file."""
#         return self.request.build_absolute_uri(reverse('serve_media', args=[file_id]))

#     def get(self, request, pk):
#         logger.info(f"Fetching recipe with ID: {pk}")
#         try:
#             recipe_id = ObjectId(pk)
#             recipe = Recipe.objects.get(id=recipe_id)
#         except (InvalidId, Recipe.DoesNotExist):
#             logger.error(f"Recipe not found for ID: {pk}")
#             return JsonResponse({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)

#         # Construct the response data
#         data = {
#             'title': recipe.title,
#             'description': recipe.description,
#             'keywords': recipe.keywords,
#             'servings': recipe.servings,
#             'cook_time': recipe.cook_time,
#             'ingredients': [
#                 {
#                     'name': ingredient.name,
#                     'amount': {
#                         'value': ingredient.amount.value if ingredient.amount else None,
#                         'unit': ingredient.amount.unit if ingredient.amount else None,
#                         'us_value': ingredient.amount.us_value if ingredient.amount else None,
#                         'us_unit': ingredient.amount.us_unit if ingredient.amount else None,
#                         'metric_value': ingredient.amount.metric_value if ingredient.amount else None,
#                         'metric_unit': ingredient.amount.metric_unit if ingredient.amount else None,
#                     },
#                     'spoonacular_id': ingredient.spoonacular_id,
#                     'photo': self.get_media_url(ingredient.photo.file_id) if ingredient.photo else None,
#                     'video': self.get_media_url(ingredient.video.file_id) if ingredient.video else None
#                 } for ingredient in recipe.ingredients
#             ] if not recipe.ingredients_single_block else recipe.ingredients_single_block,
#             'instructions': [
#                 {
#                     'step_number': instruction.step_number,
#                     'description': instruction.description,
#                     'photo': self.get_media_url(instruction.photo.file_id) if instruction.photo else None,
#                     'video': self.get_media_url(instruction.video.file_id) if instruction.video else None
#                 } for instruction in recipe.instructions
#             ] if not recipe.instructions_single_block else recipe.instructions_single_block,
#             'media': [
#                 {
#                     'type': media.type,
#                     'url': self.get_media_url(media.file_id) if media.file_id else media.url,
#                     'file_id': media.file_id
#                 } for media in recipe.media
#             ],
#             'spoonacular_id': recipe.spoonacular_id
#         }
#         return JsonResponse(data)

#     def put(self, request, pk):
#         logger.info(f"Updating recipe with ID: {pk}")
#         try:
#             recipe_id = ObjectId(pk)
#             recipe = Recipe.objects.get(id=recipe_id)
#         except (InvalidId, Recipe.DoesNotExist):
#             logger.error(f"Recipe not found for ID: {pk}")
#             return JsonResponse({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)

#         # Ensure user is authenticated
#         if not request.user.is_authenticated:
#             return JsonResponse({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

#         # Update recipe fields
#         recipe.title = request.data.get('title', recipe.title)
#         recipe.description = request.data.get('description', recipe.description)
#         recipe.servings = request.data.get('servings', recipe.servings)
#         recipe.cook_time = request.data.get('cook_time', recipe.cook_time)
#         recipe.updated_at = datetime.now(timezone.utc)

#         # Handle ingredients and instructions
#         ingredients_data = request.data.get('ingredients', [])
#         ingredients_single_block = request.data.get('ingredients_single_block', '')
#         recipe.ingredients = []
#         if ingredients_data and not ingredients_single_block:
#             self.add_ingredients(recipe, ingredients_data)
#         elif ingredients_single_block:
#             recipe.ingredients_single_block = ingredients_single_block

#         instructions_data = request.data.get('instructions', [])
#         instructions_single_block = request.data.get('instructions_single_block', '')
#         recipe.instructions = []
#         if instructions_data and not instructions_single_block:
#             self.add_instructions(recipe, instructions_data)
#         elif instructions_single_block:
#             recipe.instructions_single_block = instructions_single_block

#         # Handle media updates
#         media_data = request.data.get('media', [])
#         updated_media = []
#         for media in media_data:
#             if 'url' in media:
#                 file_id = self.save_media_to_gridfs(media['url'])
#                 updated_media.append(Media(type=media['type'], file_id=file_id))
#             else:
#                 updated_media.append(Media(type=media['type'], file_id=media.get('file_id')))

#         recipe.media = updated_media
#         recipe.save()
#         logger.info(f"Recipe updated: {recipe}")
#         return JsonResponse({'message': 'Recipe updated successfully!'})

#     def save_media_to_gridfs(self, url):
#         response = requests.get(url)
#         response.raise_for_status()
#         file_data = BytesIO(response.content)
#         file_id = settings.fs.put(file_data, filename=url.split('/')[-1])
#         return file_id

#     def delete(self, request, pk):
#         logger.info(f"Deleting recipe with ID: {pk}")
#         try:
#             recipe_id = ObjectId(pk)
#             recipe = Recipe.objects.get(id=recipe_id)

#             # Collect media file IDs for deletion
#             media_file_ids = [media.file_id for media in recipe.media]
            
#             # Delete media from GridFS
#             for file_id in media_file_ids:
#                 settings.fs.delete(file_id)
            
#             # Delete associated ingredients and instructions media from GridFS
#             for ingredient in recipe.ingredients:
#                 if ingredient.photo:
#                     settings.fs.delete(ingredient.photo.file_id)
#                 if ingredient.video:
#                     settings.fs.delete(ingredient.video.file_id)

#             for instruction in recipe.instructions:
#                 if instruction.photo:
#                     settings.fs.delete(instruction.photo.file_id)
#                 if instruction.video:
#                     settings.fs.delete(instruction.video.file_id)

#             # Delete the recipe
#             recipe.delete()
            
#             logger.info(f"Recipe deleted: {pk}")
#             return JsonResponse({'message': 'Recipe deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)
        
#         except (InvalidId, Recipe.DoesNotExist):
#             logger.error(f"Recipe not found for ID: {pk}")
#             return JsonResponse({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             logger.error(f"Error deleting recipe: {e}")
#             return JsonResponse({'error': 'An error occurred while deleting the recipe.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def add_ingredients(self, recipe, ingredients_data):
#         for ingredient_data in ingredients_data:
#             amount_data = ingredient_data.get('amount', None)
#             amount = IngredientAmount(
#                 value=amount_data.get('value') if amount_data else None,
#                 unit=amount_data.get('unit') if amount_data else None,
#                 us_value=amount_data.get('us_value') if amount_data else None,
#                 us_unit=amount_data.get('us_unit') if amount_data else None,
#                 metric_value=amount_data.get('metric_value') if amount_data else None,
#                 metric_unit=amount_data.get('metric_unit') if amount_data else None
#             ) if amount_data else None
#             ingredient = Ingredient(
#                 name=ingredient_data['name'],
#                 spoonacular_id=ingredient_data.get('spoonacular_id', None),
#                 amount=amount,
#                 photo=self.handle_media(ingredient_data.get('photo')),
#                 video=self.handle_media(ingredient_data.get('video'))
#             )
#             recipe.ingredients.append(ingredient)

#     def add_instructions(self, recipe, instructions_data):
#         for instruction_data in instructions_data:
#             instruction = Instruction(
#                 step_number=instruction_data['step_number'],
#                 description=instruction_data['description'],
#                 photo=self.handle_media(instruction_data.get('photo')),
#                 video=self.handle_media(instruction_data.get('video'))
#             )
#             recipe.instructions.append(instruction)

#     def handle_media(self, media_data):
#         if isinstance(media_data, dict):
#             file_id = media_data.get('file_id')
#             url = media_data.get('url')
#             if file_id:
#                 return Media(type=media_data.get('type'), url=url, file_id=file_id)
#             elif url:
#                 # Use the MediaFile class to handle the download and storage
#                 media_file = MediaFile.from_url(url, "recipe_image")
#                 return Media(type=media_data.get('type'), url=url, file_id=media_file.gridfs.grid_id)
#         return None


# class RecipeRetrieveUpdateDestroyView(APIView):
#     authentication_classes = [CookieTokenAuthentication]
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request, pk):
#         logger.info(f"Fetching recipe with ID: {pk}")
#         try:
#             recipe_id = ObjectId(pk)
#             recipe = Recipe.objects.get(id=recipe_id)
#         except (InvalidId, Recipe.DoesNotExist):
#             logger.error(f"Recipe not found for ID: {pk}")
#             return Response(status=status.HTTP_404_NOT_FOUND)

#         data = {
#             'title': recipe.title,
#             'description': recipe.description,
#             'keywords': recipe.keywords,
#             'servings': recipe.servings,
#             'cook_time': recipe.cook_time,
#             'ingredients': [
#                 {
#                     'name': ingredient.name,
#                     'amount': {
#                         'value': ingredient.amount.value if ingredient.amount else None,
#                         'unit': ingredient.amount.unit if ingredient.amount else None,
#                         'us_value': ingredient.amount.us_value if ingredient.amount else None,
#                         'us_unit': ingredient.amount.us_unit if ingredient.amount else None,
#                         'metric_value': ingredient.amount.metric_value if ingredient.amount else None,
#                         'metric_unit': ingredient.amount.metric_unit if ingredient.amount else None,
#                     },
#                     'spoonacular_id': ingredient.spoonacular_id,
#                     'photo': ingredient.photo,
#                     'video': ingredient.video
#                 } for ingredient in recipe.ingredients
#             ] if not recipe.ingredients_single_block else recipe.ingredients_single_block,
#             'instructions': [
#                 {
#                     'step_number': instruction.step_number,
#                     'description': instruction.description,
#                     'photo': instruction.photo,
#                     'video': instruction.video
#                 } for instruction in recipe.instructions
#             ] if not recipe.instructions_single_block else recipe.instructions_single_block,
#             'media': [{'type': media.type, 'url': media.url, 'file_id': media.file_id} for media in recipe.media],
#             'spoonacular_id': recipe.spoonacular_id
#         }
#         return JsonResponse(data)

#     def put(self, request, pk):
#         logger.info(f"Updating recipe with ID: {pk}")
#         try:
#             recipe_id = ObjectId(pk)
#             recipe = Recipe.objects.get(id=recipe_id)
#         except (InvalidId, Recipe.DoesNotExist):
#             logger.error(f"Recipe not found for ID: {pk}")
#             return Response(status=status.HTTP_404_NOT_FOUND)

#         # Ensure user is authenticated
#         if not request.user.is_authenticated:
#             return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

#         recipe.title = request.data.get('title', recipe.title)
#         recipe.description = request.data.get('description', recipe.description)
#         recipe.servings = request.data.get('servings', recipe.servings)
#         recipe.cook_time = request.data.get('cook_time', recipe.cook_time)
#         recipe.updated_at = datetime.now(timezone.utc)

#         ingredients_data = request.data.get('ingredients', [])
#         ingredients_single_block = request.data.get('ingredients_single_block', '')
#         recipe.ingredients = []
#         if ingredients_data and not ingredients_single_block:
#             self.add_ingredients(recipe, ingredients_data)
#         elif ingredients_single_block:
#             recipe.ingredients_single_block = ingredients_single_block

#         instructions_data = request.data.get('instructions', [])
#         instructions_single_block = request.data.get('instructions_single_block', '')
#         recipe.instructions = []
#         if instructions_data and not instructions_single_block:
#             self.add_instructions(recipe, instructions_data)
#         elif instructions_single_block:
#             recipe.instructions_single_block = instructions_single_block

#         # Handle media updates
#         media_data = request.data.get('media', [])
#         updated_media = []
#         for media in media_data:
#             if 'url' in media:
#                 file_id = self.save_media_to_gridfs(media['url'])
#                 updated_media.append(Media(type=media['type'], file_id=file_id))
#             else:
#                 updated_media.append(Media(type=media['type'], file_id=media.get('file_id')))

#         recipe.media = updated_media

#         recipe.save()
#         logger.info(f"Recipe updated: {recipe}")
#         return JsonResponse({'message': 'Recipe updated successfully!'})

#     def save_media_to_gridfs(self, url):
#         response = requests.get(url)
#         response.raise_for_status()
#         file_data = BytesIO(response.content)
#         file_id = settings.fs.put(file_data, filename=url.split('/')[-1])
#         return file_id

#     def delete(self, request, pk):
#         logger.info(f"Deleting recipe with ID: {pk}")
#         try:
#             recipe_id = ObjectId(pk)
#             recipe = Recipe.objects.get(id=recipe_id)

#             # Collect media file IDs for deletion
#             media_file_ids = [media.file_id for media in recipe.media]
            
#             # Delete media from GridFS
#             for file_id in media_file_ids:
#                 settings.fs.delete(file_id)
            
#             # Delete the recipe
#             recipe.delete()
            
#             logger.info(f"Recipe deleted: {pk}")
#             return Response({'message': 'Recipe deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)
        
#         except (InvalidId, Recipe.DoesNotExist):
#             logger.error(f"Recipe not found for ID: {pk}")
#             return Response(status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             logger.error(f"Error deleting recipe: {e}")
#             return Response({'error': 'An error occurred while deleting the recipe.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# class AddSpoonacularRecipeView(APIView):
#     def post(self, request, *args, **kwargs):
#         recipe_data = request.data.get('recipeDetails')

#         if not recipe_data:
#             return Response({'error': 'Invalid recipe data'}, status=status.HTTP_400_BAD_REQUEST)

#         recipe_id = recipe_data.get('id')
        
#         # Check if the recipe already exists
#         if Recipe.objects(recipe_id=recipe_id).first():
#             # Recipe already exists, skip adding
#             return Response({'message': 'Recipe already exists, skipping.'}, status=status.HTTP_200_OK)

#         # Create and save new recipe
#         recipe = Recipe(
#             recipe_id=recipe_id,
#             title=recipe_data.get('title', ''),
#             description=recipe_data.get('description', ''),
#             servings=recipe_data.get('servings', 1),
#             cook_time=recipe_data.get('cookTime', ''),
#             created_at=datetime.now(),
#             updated_at=datetime.now(),
#             user_id=None  # Assuming no user association for automated recipes
#         )

#         # Download and save recipe media (thumbnail)
#         recipe_thumbnail_url = recipe_data.get('photo')
#         if recipe_thumbnail_url:
#             recipe_media_id = self.save_media_to_gridfs(recipe_thumbnail_url)
#             recipe.media = [Media(type='image', file_id=recipe_media_id)]

#         # Add ingredients
#         ingredients = []
#         for ingredient_data in recipe_data.get('ingredients', []):
#             ingredient = Ingredient(
#                 name=ingredient_data.get('name', ''),
#                 spoonacular_id=ingredient_data.get('id'),
#                 amount=self.create_ingredient_amount(ingredient_data.get('amount', {}))
#             )
#             if ingredient_data.get('image'):
#                 ingredient_media_id = self.save_media_to_gridfs(ingredient_data['image'])
#                 ingredient.add_media(file=None, filename=ingredient_data['image'])  # Assume image URL is used to fetch
#             ingredients.append(ingredient)

#         recipe.ingredients = ingredients

#         # Add instructions
#         instructions = []
#         for instruction_data in recipe_data.get('instructions', []):
#             instruction = Instruction(
#                 step_number=instruction_data.get('number'),
#                 description=instruction_data.get('step')
#             )
#             instructions.append(instruction)

#         recipe.instructions = instructions

#         # Save the recipe
#         recipe.save()
#         return Response({'message': 'Recipe added successfully'}, status=status.HTTP_201_CREATED)

#     def save_media_to_gridfs(self, url):
#         response = requests.get(url)
#         response.raise_for_status()
#         file_data = BytesIO(response.content)
#         file_id = settings.fs.put(file_data, filename=url.split('/')[-1])
#         return file_id

#     def create_ingredient_amount(self, amount_data):
#         if not amount_data:
#             return None
#         return IngredientAmount(
#             value=amount_data.get('value'),
#             unit=amount_data.get('unit'),
#             us_value=amount_data.get('us', {}).get('value'),
#             us_unit=amount_data.get('us', {}).get('unit'),
#             metric_value=amount_data.get('metric', {}).get('value'),
#             metric_unit=amount_data.get('metric', {}).get('unit')
#         )



# class CachedRecipeSearchView(APIView):
#     def get(self, request, *args, **kwargs):
#         # Extract search parameters from the request
#         include_ingredients = request.query_params.getlist('include_ingredients')
#         exclude_ingredients = request.query_params.getlist('exclude_ingredients')
#         cuisine = request.query_params.get('cuisine')
#         diet = request.query_params.get('diet')
#         meal_type = request.query_params.get('meal_type')
#         max_time = request.query_params.get('max_time')
#         dish_type = request.query_params.get('dish_type')
#         occasion = request.query_params.get('occasion')

#         # Build query parameters for Spoonacular API complexSearch endpoint
#         query_params = {
#             'cuisine': cuisine,
#             'diet': diet,
#             'type': meal_type,
#             'maxReadyTime': max_time,
#             'dishType': dish_type,
#             'query': occasion,  # Using 'query' for occasions
#         }
#         query_params = {k: v for k, v in query_params.items() if v}

#         # Generate a cache key based on query parameters and included/excluded ingredients
#         cache_key = md5(str(query_params).encode() + str(include_ingredients).encode() + str(exclude_ingredients).encode()).hexdigest()

#         # Check if the results are cached
#         cached_data = cache.get(cache_key)
#         if cached_data:
#             return Response(cached_data, status=status.HTTP_200_OK)

#         # Perform ingredient-based search
#         ingredient_based_recipes = []
#         if include_ingredients or exclude_ingredients:
#             ingredient_based_recipes = search_recipes_by_ingredients(
#                 include_ingredients=include_ingredients,
#                 exclude_ingredients=exclude_ingredients
#             )

#         # Perform advanced filter search
#         advanced_filter_recipes = search_recipes(query_params) if not include_ingredients and not exclude_ingredients else []

#         # Combine results from both searches
#         combined_results = {
#             'results': ingredient_based_recipes.get('results', []) + advanced_filter_recipes.get('results', [])
#         }

#         # Remove duplicates if necessary
#         seen = set()
#         unique_results = []
#         for recipe in combined_results['results']:
#             if recipe['id'] not in seen:
#                 seen.add(recipe['id'])
#                 unique_results.append(recipe)
#         combined_results['results'] = unique_results

#         # Cache the response for future requests
#         cache.set(cache_key, combined_results, timeout=60*60)  # Cache for 1 hour

#         return Response(combined_results, status=status.HTTP_200_OK)



# class AddSpoonacularRecipeView(APIView):
#     def get(self, request, recipe_id, *args, **kwargs):
#         # Fetch recipe data from Spoonacular using the provided recipe_id
#         response_data = get_recipe_information(recipe_id)

#         if not response_data:
#             return Response({'error': 'Failed to fetch recipe data from Spoonacular'}, status=status.HTTP_404_NOT_FOUND)

#         # Transform the fetched data
#         recipe_data = transform_recipe_data(response_data).get('recipeDetails')

#         if not recipe_data:
#             return Response({'error': 'Invalid recipe data from Spoonacular'}, status=status.HTTP_400_BAD_REQUEST)

#         # Check if the recipe already exists
#         if Recipe.objects(recipe_id=recipe_id).first():
#             # Recipe already exists, skip adding
#             return Response({'message': 'Recipe already exists, skipping.'}, status=status.HTTP_200_OK)

#         # Create and save new recipe
#         recipe = Recipe(
#             recipe_id=recipe_id,
#             title=recipe_data.get('title', ''),
#             description=recipe_data.get('description', ''),
#             servings=recipe_data.get('servings', 1),
#             cook_time=recipe_data.get('cookTime', ''),
#             created_at=datetime.now(),
#             updated_at=datetime.now(),
#             user_id=None  # Assuming no user association for automated recipes
#         )

#         # Download and save recipe media (thumbnail)
#         recipe_thumbnail_url = recipe_data.get('photo')
#         if recipe_thumbnail_url:
#             recipe_media_id = self.save_media_to_gridfs(recipe_thumbnail_url)
#             recipe.media = [Media(type='image', file_id=recipe_media_id)]

#         # Add ingredients
#         ingredients = []
#         for ingredient_data in recipe_data.get('ingredients', []):
#             ingredient = Ingredient(
#                 name=ingredient_data.get('name', ''),
#                 spoonacular_id=ingredient_data.get('id'),
#                 amount=self.create_ingredient_amount(ingredient_data.get('amount', {}))
#             )
#             if ingredient_data.get('image'):
#                 ingredient_media_id = self.save_media_to_gridfs(ingredient_data['image'])
#                 ingredient.add_media(file=None, filename=ingredient_data['image'])  # Assume image URL is used to fetch
#             ingredients.append(ingredient)

#         recipe.ingredients = ingredients

#         # Add instructions
#         instructions = []
#         for instruction_data in recipe_data.get('instructions', []):
#             instruction = Instruction(
#                 step_number=instruction_data.get('number'),
#                 description=instruction_data.get('step')
#             )
#             instructions.append(instruction)

#         recipe.instructions = instructions

#         # Save the recipe
#         recipe.save()
#         return Response({'message': 'Recipe added successfully'}, status=status.HTTP_201_CREATED)

#     def save_media_to_gridfs(self, url):
#         response = requests.get(url)
#         response.raise_for_status()
#         file_data = BytesIO(response.content)
#         file_id = settings.fs.put(file_data, filename=url.split('/')[-1])
#         return file_id

#     def create_ingredient_amount(self, amount_data):
#         if not amount_data:
#             return None
#         return IngredientAmount(
#             value=amount_data.get('value'),
#             unit=amount_data.get('unit'),
#             us_value=amount_data.get('us', {}).get('value'),
#             us_unit=amount_data.get('us', {}).get('unit'),
#             metric_value=amount_data.get('metric', {}).get('value'),
#             metric_unit=amount_data.get('metric', {}).get('unit')
#         )