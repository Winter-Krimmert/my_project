import os
from django.apps import AppConfig
from django.conf import settings

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # Call the parent ready() method
        super().ready()

        # Define the cache directory path
        cache_dir = os.path.join(settings.BASE_DIR, 'cache')

        # Check if the directory exists; if not, create it
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            print(f"Cache directory created at {cache_dir}")
        else:
            print(f"Cache directory already exists at {cache_dir}")
