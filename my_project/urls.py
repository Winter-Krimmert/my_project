from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.authtoken import views as drf_views
from rest_framework import permissions
from users.views import (
    UserRegister, 
    UserLogin,
    LogoutView,
    UserDeleteView, 
    home, 
    RecipeListCreateView, 
    RecipeRetrieveUpdateDestroyView,
    FacebookLogin, 
    GoogleLogin,
    AddSpoonacularRecipeView,
    ServeMediaView,
    CachedRecipeSearchView,
    MyCookbookListCreateView,
    MyCookbookDetailView,
    AddRecipeToCookbookView,
    RemoveRecipeFromCookbookView,
    get_csrf_token,
    # test_cors,
    # ForgotPasswordView,
    # send_test_email,
)

schema_view = get_schema_view(
    openapi.Info(
        title="Recipe-z API",
        default_version='v1',
        description="Recipe-z API documentation",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@yourapi.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Serve the React app at the root URL
    path('', home, name='home'),

    # CORS Test Endpoint
    # path('test-cors/', test_cors),

    # Admin interface
    path('admin/', admin.site.urls),

    # API endpoints for authentication
    path('api/register/', UserRegister.as_view(), name='user-register'),
    path('api/login/', UserLogin.as_view(), name='user-login'),
    path('api/logout/', LogoutView.as_view(), name='user-logout'),
    path('api/get-csrf-token/', get_csrf_token, name='get_csrf_token'),


    # Password reset endpoints
    # path('api/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),

    # Test email sending endpoint
    # path('send-test-email/', send_test_email, name='send_test_email'),


    # Social login endpoints
    path('api/facebook/login/', FacebookLogin.as_view(), name='facebook_login'),
    path('api/google/login/', GoogleLogin.as_view(), name='google_login'),
    path('facebook/callback/', FacebookLogin.as_view(), name='facebook_callback'),
    path('google/callback/', GoogleLogin.as_view(), name='google_callback'),

    # User account management
    path('api/delete/', UserDeleteView.as_view(), name='user-delete-view'),

    # Recipe-related API endpoints
    path('api/recipes/', RecipeListCreateView.as_view(), name='recipe-list-create'),
    path('api/recipes/<pk>/', RecipeRetrieveUpdateDestroyView.as_view(), name='recipe-detail'),
    path('add-spoonacular-recipe/<int:recipe_id>/', AddSpoonacularRecipeView.as_view(), name='add_spoonacular_recipe'),
    path('recipes/search/', CachedRecipeSearchView.as_view(), name='cached_recipe_search'),

    # Media serving endpoint
    path('media/<str:media_id>/', ServeMediaView.as_view(), name='serve_media'),

    # Token authentication
    path('api-token-auth/', drf_views.obtain_auth_token, name='api-token-auth'),

    # Cookbook-related API endpoints
    path('api/cookbooks/', MyCookbookListCreateView.as_view(), name='cookbook-list-create'),
    path('api/cookbooks/<str:cookbook_id>/', MyCookbookDetailView.as_view(), name='cookbook-detail'),
    path('api/cookbooks/<str:cookbook_id>/add_recipe/', AddRecipeToCookbookView.as_view(), name='add-recipe-to-cookbook'),
    path('api/cookbooks/<str:cookbook_id>/remove_recipe/', RemoveRecipeFromCookbookView.as_view(), name='remove-recipe-from-cookbook'),

    # Swagger documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-schema'),
]

# Debug Toolbar (if enabled)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

# Set the custom 404 view
handler404 = 'users.views.custom_404_view'
