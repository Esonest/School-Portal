from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


@login_required
def portal_selection(request):
    """
    Show portal selection page where users choose which dashboard to access.
    """
    user = request.user

    # Determine roles
    roles = []

    if hasattr(user, 'teacherprofile') or user.role == 'teacher':
        roles.append('teacher')
    if hasattr(user, 'studentprofile') or user.role == 'student':
        roles.append('student')
    if user.role == 'schooladmin':
        roles.append('schooladmin')
    if user.role == 'superadmin':
        roles.append('superadmin')
    if user.role == 'accountant':
        roles.append('accountant')

    # Add related objects for roles that need them
    school = getattr(user, 'school', None) if 'schooladmin' in roles else None
    # Assuming accountant also has a school (or organization) relation
    accountant_school = getattr(user, 'school', None) if 'accountant' in roles else None

    context = {
        'roles': roles,
        'school': school,                # for school admin dashboard
        'accountant_school': accountant_school,  # for accountant dashboard links
    }

    return render(request, 'accounts/portal_selection.html', context)

    
     

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required


def login_view(request):
    """Handles user login and redirects to portal selection"""
    if request.user.is_authenticated:
        # Already logged in → go straight to portal selection
        return redirect('accounts:portal_selection')

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('accounts:portal_selection')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")



@login_required
def logout_view(request):
    """Logs the user out and sends them to login page"""
    logout(request)
    return redirect('accounts:login')



def home(request):
    return render(request, 'accounts/home.html')

def about(request):
    return render(request, 'accounts/about.html')

def contact(request):
    return render(request, 'accounts/contact.html')

def help(request):
    return render(request, 'accounts/help.html')    





from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .models import School
from django.urls import reverse, NoReverseMatch

@login_required
def open_portal(request, school_id, portal):
    """
    Open any portal (students, teachers, results, CBT, notes, assignments, attendance)
    for a specific school. Super Admin can access all schools. School Admin only their school.
    """
    school = get_object_or_404(School, id=school_id)
    user = request.user

    # -----------------------------
    # Role-based access
    # -----------------------------
    if getattr(user, 'is_superadmin', False):
        pass  # full access
    elif getattr(user, 'is_schooladmin', False):
        if getattr(user, 'school_id', None) != school.id:
            raise PermissionDenied("You cannot access this school.")
    else:
        raise PermissionDenied("You cannot access this portal.")

    # -----------------------------
    # Portal map
    # -----------------------------
    portal_map = {
        'students': 'students:student_dashboard',          # dashboard/list for admin
        'teachers': 'teachers:teacher_dashboard',
        'results': 'results:dashboard',
        'cbt': 'cbt:dashboard',
        'notes': 'notes:dashboard',
        'assignments': 'assignments:dashboard',
        'attendance': 'attendance:dashboard',
    }

    if portal not in portal_map:
        raise PermissionDenied("Invalid portal requested.")

    url_name = portal_map[portal]

    # -----------------------------
    # Redirect based on role
    # -----------------------------
    try:
        if portal == 'students' and (user.is_superadmin or user.is_schooladmin):
            # Admin view of students with school_id
            return redirect(url_name, school_id=school.id)
        elif portal == 'teachers' and (user.is_superadmin or user.is_schooladmin):
            # Admin view of teachers
            return redirect(url_name, school_id=school.id)
        else:
            # Student or other portals
            return redirect(url_name)
    except NoReverseMatch:
        return redirect(url_name)
