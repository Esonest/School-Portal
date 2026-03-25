# accounts/middleware.py
from django.contrib.auth import logout
from django.shortcuts import redirect

class BlockDeletedUserMiddleware:
    """Logs out deleted users or users with inactive schools"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated:
            user.refresh_from_db()
            # ❌ Block deleted users
            if getattr(user, 'is_deleted', False):
                logout(request)
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")

            # ❌ Block inactive schools
            if user.school and not user.school.active:
                logout(request)
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")

            # ❌ Block users without profile for their role
            if user.role == 'teacher' and not hasattr(user, 'teacher_profile'):
                logout(request)
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")
            if user.role == 'student' and not hasattr(user, 'student_profile'):
                logout(request)
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")
            if user.role == 'schooladmin' and not hasattr(user, 'school_admin_profile'):
                logout(request)
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return self.get_response(request)

# accounts/middleware.py
import time
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages

class AutoLogoutMiddleware:
    """
    Logs out user after inactivity timeout
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = 600  # 10 minutes (change as needed)

    def __call__(self, request):
        if request.user.is_authenticated:
            current_time = time.time()
            last_activity = request.session.get('last_activity')

            if last_activity:
                elapsed = current_time - last_activity

                if elapsed > self.timeout:
                    logout(request)
                    messages.warning(request, "Session expired. Please login again.")
                    return redirect(f"{settings.LOGIN_URL}?next={request.path}")

            # Update last activity time
            request.session['last_activity'] = current_time

        return self.get_response(request)        