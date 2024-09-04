from decouple import config
from .models import Token, User
from mongoengine import connect



# Step 1: Ensure the `Token` collection exists by creating a token
def create_token_for_user(email):
    # Retrieve the user from the database
    user = User.objects(email=email).first()

    if user:
        # Generate a token for the user
        token = Token.generate_token(user)
        print(f"Token created: {token.key}")
        return token
    else:
        print("User not found.")
        return None

# Step 2: Generate a token for your existing user
create_token_for_user("winterk463@gmail.com")
