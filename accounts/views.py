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


from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import ContactMessage

def contact_us(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message_text = request.POST.get("message")

        # Save to DB
        contact = ContactMessage.objects.create(
            name=name, email=email, subject=subject, message=message_text
        )

        # Send email to techcenter
        full_message = f"""
New Contact Message from TECHCENTER Website

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message_text}
        """
        try:
            send_mail(
                subject=f"[TECHCENTER Contact] {subject}",
                message=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["techcenter652@gmail.com"],
                fail_silently=False,
            )
            # Auto-reply to sender
            send_mail(
                subject="Thank you for contacting TECHCENTER",
                message=f"Hi {name},\n\nWe received your message and will get back to you soon.\n\nRegards,\nTECHCENTER Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )

            messages.success(request, "Your message has been sent successfully.")
        except Exception:
            messages.error(request, "Failed to send message. Please try again later.")

        return redirect("accounts:contact_us")

    return render(request, "accounts/contact.html")



