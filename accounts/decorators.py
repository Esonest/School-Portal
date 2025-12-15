from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps

def student_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_student_user:
            return view_func(request, *args, **kwargs)
        return redirect('portal_selection')
    return _wrapped_view


def teacher_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_teacher_user:
            return view_func(request, *args, **kwargs)
        return redirect('portal_selection')
    return _wrapped_view




# cbt/utils.py
from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from .models import School

def get_user_school(request):
    """Return school for current user if they are school admin; None for superadmins."""
    user = request.user
    # superadmin check (adjust to your project)
    if getattr(user, "is_superadmin", False):
        return None  # superadmin allowed to pass school_id explicitly
    profile = getattr(user, "school_admin_profile", None)
    if profile:
        return profile.school
    return None

def school_admin_or_superadmin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if getattr(request.user, "is_superadmin", False):
            return view_func(request, *args, **kwargs)
        if getattr(request.user, "school_admin_profile", None) is None:
            # not a school admin
            raise PermissionDenied("You are not authorized to access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper


from django.shortcuts import redirect

def school_admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        profile = getattr(request.user, "school_admin_profile", None)
        if not profile:
            return redirect("accounts:portal_selection")
        return view_func(request, *args, **kwargs)
    return wrapper


from django.http import Http404

def superadmin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superadmin:
            raise Http404("Not authorized")
        return view_func(request, *args, **kwargs)
    return wrapper
