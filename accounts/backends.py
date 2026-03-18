# accounts/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class ActiveUserBackend(ModelBackend):
    """
    Custom backend: only authenticate users who are not deleted and active
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        # ❌ Block deleted or inactive users immediately
        if user.is_deleted or not user.is_active:
            return None

        if user.check_password(password):
            return user
        return None