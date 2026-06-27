from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class ActiveUserBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):

        try:
            user = User.objects.get(username=username)

        except User.DoesNotExist:
            return None

        except User.MultipleObjectsReturned:
            # Prevent server crash
            user = User.objects.filter(
                username=username
            ).order_by("id").first()

            if not user:
                return None

        if user.is_deleted or not user.is_active:
            return None

        if user.check_password(password):
            return user

        return None