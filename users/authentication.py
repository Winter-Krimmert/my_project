from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User  # Import your custom User model

class CustomUserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return None

        try:
            user = User.objects(email=email).first()
        except User.DoesNotExist:
            raise AuthenticationFailed('Invalid credentials')

        if user and user.check_password(password):
            return (user, None)

        raise AuthenticationFailed('Invalid credentials')
