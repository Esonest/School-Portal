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
                return redirect('accounts:login')

            # ❌ Block inactive schools
            if user.school and not user.school.active:
                logout(request)
                return redirect('accounts:login')

            # ❌ Block users without profile for their role
            if user.role == 'teacher' and not hasattr(user, 'teacher_profile'):
                logout(request)
                return redirect('accounts:login')
            if user.role == 'student' and not hasattr(user, 'student_profile'):
                logout(request)
                return redirect('accounts:login')
            if user.role == 'schooladmin' and not hasattr(user, 'school_admin_profile'):
                logout(request)
                return redirect('accounts:login')

        return self.get_response(request)