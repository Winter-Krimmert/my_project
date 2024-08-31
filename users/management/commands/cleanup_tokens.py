from django.core.management.base import BaseCommand
from users.models import Token, User
from bson import ObjectId

class Command(BaseCommand):
    help = 'Clean up tokens associated with deleted users.'

    def handle(self, *args, **kwargs):
        tokens = Token.objects.all()
        deleted_tokens = 0

        for token in tokens:
            try:
                # Check if the user associated with the token still exists
                user_exists = User.objects.filter(id=ObjectId(token.user.id)).exists()
                if not user_exists:
                    token.delete()
                    deleted_tokens += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error checking token {token.key}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_tokens} orphaned tokens."))


# crontab -l
# 0 0 * * * /usr/local/bin/python3 /Users/winterkrimmert/Documents/coding_temple/Co.Lab/Week4/mongo+django/manage.py cleanup_tokens

# Create a custom management command to clean up tokens associated with deleted users. 
#  Deletes all abandoned tokens from the database, once a day, at midnight.