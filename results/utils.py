from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None


def grade_from_score(total):
    if total >= 70: return 'A'
    if total >= 60: return 'B'
    if total >= 50: return 'C'
    if total >= 45: return 'D'
    return 'F'


from .models import ClassSubjectTeacher

def sync_class_subject_teacher(teacher):
    """
    Ensures ClassSubjectTeacher entries exist for every class & subject
    assigned to this teacher.
    """
    classes = teacher.classes.all()
    subjects = teacher.subjects.all()

    for school_class in classes:
        for subject in subjects:
            ClassSubjectTeacher.objects.get_or_create(
                school_class=school_class,
                subject=subject,
                defaults={"teacher": teacher}
            )


def get_pronouns(student):
    gender = (student.gender or "").lower()

    if gender.startswith("m"):
        return {
            "pronoun": "he",
            "possessive": "his",
            "objective": "him",
        }

    return {
        "pronoun": "she",
        "possessive": "her",
        "objective": "her",
    }


# utils/sessions.py

SESSION_LIST = [
    "2025/2026",
    "2026/2027",
    "2027/2028",
    "2028/2029",
    "2029/2030",  
]


import secrets
from django.contrib.auth import get_user_model

User = get_user_model()

def generate_unique_username(base: str):
    base = (base or "student").lower()
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1
    return username



# utils.py

def interpret_grade(grade: str) -> str:
    """
    Convert a letter grade to a human-readable interpretation.
    """
    mapping = {
        "A": "Excellent",
        "B": "Very Good",
        "C": "Good",
        "D": "Fair",
        "E": "Poor",
        "F": "Fail",
    }
    return mapping.get(grade.upper(), "")



from django.db.models.signals import post_save
from django.dispatch import receiver
from superadmin.models import SchoolPortalSetting
from accounts.models import School

@receiver(post_save, sender=School)
def create_school_portal_settings(sender, instance, created, **kwargs):
    if created:
        SchoolPortalSetting.objects.get_or_create(school=instance)




# utils.py or decorators.py
from django.shortcuts import render
from functools import wraps
from superadmin.models import SchoolPortalSetting

def portal_required(portal_name):
    """
    Decorator to block access if a specific portal is disabled
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            school = None

            if hasattr(user, "teacher_profile") and user.teacher_profile:
                school = user.teacher_profile.school
            elif hasattr(user, "student_profile") and user.student_profile:
                school = user.student_profile.school

            if not school:
                return render(request, "superadmin/portal_settings/portal_disabled.html", {"school": None, "portal_name": portal_name})

            portal_settings, _ = SchoolPortalSetting.objects.get_or_create(school=school)

            # check the portal_name dynamically
            enabled = getattr(portal_settings, f"{portal_name}_enabled", False)
            if not enabled:
                return render(request, "superadmin/portal_settings/portal_disabled.html", {"school": school, "portal_name": portal_name})

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator




# results/utils.py

import qrcode
from django.urls import reverse
from django.conf import settings
import io
from django.core.files.base import ContentFile
import base64


def generate_verification_qr(student, verification_obj, box_size=6):
    """
    Generate a QR code for a student's verification URL.
    Returns a base64 data URI that can be used directly in HTML templates.
    """
    # Ensure SITE_URL has the full scheme
    base_url = getattr(settings, "SITE_URL", "https://techcenter-p2au.onrender.com")

    # Full verification URL including admission_no and token
    full_url = f"{base_url}/results/verify/{student.admission_no}/?token={verification_obj.verification_token}"

    # Create the QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=4,
    )
    qr.add_data(full_url)  # full URL goes here
    qr.make(fit=True)

    # Convert to image
    img = qr.make_image(fill_color="black", back_color="white")

    # Save image to bytes buffer
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    # Convert to base64 data URI
    qr_data_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    return qr_data_uri


def save_qr_to_student(student, token):
    img = generate_verification_qr(student, token)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    file_name = f"{student.admission_no}_verification_qr.png"
    student.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=True)
