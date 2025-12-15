from django.core.exceptions import PermissionDenied

def accountant_required(func):
    def wrapper(request, *args, **kwargs):
        # Superadmin always allowed
        if getattr(request.user, "is_superadmin", False):
            return func(request, *args, **kwargs)

        # Check accountant role
        roles = getattr(request.user, "roles", [])  # assume roles is a list
        if "accountant" in roles or getattr(request.user, "is_schooladmin", False):
            return func(request, *args, **kwargs)

        # Not allowed
        raise PermissionDenied

    return wrapper
