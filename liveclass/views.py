from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db.models import Count
from django.contrib import messages

from .models import LiveClass,LiveClassAttendance
from .forms import LiveClassForm
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
import requests



def is_school_admin(user):
    return hasattr(user, "school_admin_profile")


def is_teacher(user):
    return hasattr(user, "teacher_profile")


# ========================
# LIST VIEW
# ========================

from django.utils import timezone
from django.db.models import Q
from django.db.models import Count

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q


@login_required
def liveclass_list(request):
    user = request.user
    school = getattr(user, "school", None)
    now = timezone.now()

    # ===============================
    # AUTO STATUS UPDATE
    # ===============================
    LiveClass.objects.filter(
        start_time__lte=now,
        end_time__gte=now,
        status="scheduled"
    ).update(status="live")

    LiveClass.objects.filter(
        end_time__lt=now,
        status__in=["scheduled", "live"]
    ).update(status="ended")

    # ===============================
    # BASE QUERYSET (ROLE-BASED)
    # ===============================
    if getattr(user, "is_superadmin", False):
        classes = LiveClass.objects.all()
    else:
        classes = LiveClass.objects.filter(school=school)

        # Teacher sees only their own classes
        if getattr(user, "is_teacher_user", False):
            classes = classes.filter(teacher=user.teacher_profile)

        # Student sees only their own class
        elif getattr(user, "is_student_user", False):
            student_class = getattr(user.student_profile, "school_class", None)
            if student_class:
                classes = classes.filter(class_room=student_class)
            else:
                classes = classes.none()

    # Annotate attendance and student counts
    classes = classes.annotate(
        attendance_count=Count('attendances__student', distinct=True),
        student_count=Count("class_room__students", distinct=True)
    ).select_related(
        "teacher",
        "subject",
        "class_room"
    ).order_by("-start_time")

    # Calculate attendance percent safely
    for cls in classes:
        cls.attendance_percent = (
            (cls.attendance_count / cls.student_count) * 100
            if cls.student_count > 0 else 0
        )

    # ===============================
    # PASS ROLES TO TEMPLATE
    # ===============================
    roles = []
    if getattr(user, "is_teacher_user", False):
        roles.append("teacher")
    if getattr(user, "is_student_user", False):
        roles.append("student")
    if getattr(user, "is_schooladmin", False):
        roles.append("schooladmin")
    if getattr(user, "is_superadmin", False):
        roles.append("superadmin")

    return render(request, "liveclass/list.html", {
        "classes": classes,
        "roles": roles,
        "now": now
    })


# ========================
# CREATE
# ========================

@login_required
def liveclass_create(request):

    if not (request.user.is_teacher_user or request.user.is_schooladmin):
        return HttpResponseForbidden()

    school = request.user.school

    if request.method == "POST":
        form = LiveClassForm(request.POST, school=school, user=request.user)

        if form.is_valid():
            live_class = form.save(commit=False)
            live_class.school = school

            if request.user.is_teacher_user:
                live_class.teacher = request.user.teacher_profile

            live_class.save()
            return redirect("liveclass:liveclass_list")
    else:
        form = LiveClassForm(school=school, user=request.user)

    return render(request, "liveclass/form.html", {"form": form})



@login_required
def liveclass_update(request, pk):
    school = request.user.school

    live_class = get_object_or_404(
        LiveClass.objects.select_related("teacher"),
        pk=pk,
        school=school
    )

    # Only teacher-owner OR school admin OR superadmin can edit
    if request.user.is_teacher_user:
        if live_class.teacher.user != request.user:
            return HttpResponseForbidden()

    elif not (request.user.is_schooladmin or request.user.is_superadmin):
        return HttpResponseForbidden()

    if request.method == "POST":
        form = LiveClassForm(
            request.POST,
            instance=live_class,
            school=school,
            user=request.user
        )
        if form.is_valid():
            form.save()
            return redirect("liveclass:liveclass_list")
    else:
        form = LiveClassForm(
            instance=live_class,
            school=school,
            user=request.user
        )

    return render(request, "liveclass/form.html", {"form": form})


@login_required
def liveclass_delete(request, pk):
    school = request.user.school

    live_class = get_object_or_404(
        LiveClass.objects.select_related("teacher"),
        pk=pk,
        school=school
    )

    if request.user.is_teacher_user:
        if live_class.teacher.user != request.user:
            return HttpResponseForbidden()

    elif not (request.user.is_schooladmin or request.user.is_superadmin):
        return HttpResponseForbidden()

    if request.method == "POST":
        live_class.delete()
        return redirect("liveclass:liveclass_list")

    return render(request, "liveclass/delete.html", {"live_class": live_class})


def generate_100ms_token(room_id, user_id, role):
    """
    Generate 100ms auth token for a user.
    """
    response = requests.post(
        "https://api.100ms.live/v2/tokens",
        auth=(settings.HMS_API_KEY, settings.HMS_API_SECRET),
        json={
            "room_id": room_id,
            "user_id": str(user_id),
            "role": role,
        }
    )

    if response.status_code != 200:
        return None

    return response.json().get("token")


@login_required
def liveclass_join(request, pk):
    user = request.user
    school = getattr(user, "school", None)

    live_class = get_object_or_404(
        LiveClass.objects.select_related("teacher"),
        pk=pk,
        school=school
    )

    # ===============================
    # PERMISSION CHECK
    # ===============================
    is_student = getattr(user, "is_student_user", False)
    is_teacher = getattr(user, "is_teacher_user", False)
    is_schooladmin = getattr(user, "is_schooladmin", False)
    is_superadmin = getattr(user, "is_superadmin", False)

    if not any([is_student, is_teacher, is_schooladmin, is_superadmin]):
        return HttpResponseForbidden("Not allowed to join this class.")

    # ===============================
    # STATUS CHECK
    # ===============================
    live_class.update_status()

    if live_class.status != "live":
        messages.error(request, "Class is not currently active.")
        return redirect("liveclass:liveclass_list")

    # ===============================
    # ATTENDANCE (STUDENTS ONLY)
    # ===============================
    if is_student:
        attendance, created = LiveClassAttendance.objects.get_or_create(
            live_class=live_class,
            student=user.student_profile
        )

        if not created and attendance.left_at:
            attendance.joined_at = timezone.now()
            attendance.left_at = None
            attendance.save(update_fields=["joined_at", "left_at"])

    # ===============================
    # DETERMINE ROLE
    # ===============================
    is_moderator = any([is_teacher, is_schooladmin, is_superadmin])
    role = "teacher" if is_moderator else "student"

    # ===============================
    # ENSURE ROOM EXISTS
    # ===============================
    if not live_class.hms_room_id:
        messages.error(request, "Live room not configured.")
        return redirect("liveclass:liveclass_list")

    # ===============================
    # GENERATE 100ms TOKEN
    # ===============================
    token = generate_100ms_token(
        room_id=live_class.hms_room_id,
        user_id=user.id,
        role=role
    )

    if not token:
        messages.error(request, "Unable to join live room. Try again.")
        return redirect("liveclass:liveclass_list")

    # ===============================
    # RENDER JOIN PAGE
    # ===============================
    return render(request, "liveclass/join.html", {
        "live_class": live_class,
        "hms_token": token,
        "is_moderator": is_moderator,
    })


from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import LiveClass, LiveClassAttendance

@login_required
def attendance_dashboard(request, pk):
    """
    Show attendance details for a single live class.
    """
    school = request.user.school
    live_class = get_object_or_404(
        LiveClass.objects.prefetch_related("attendances__student", "class_room__students"),
        pk=pk, school=school
    )

    # Permission: only teacher-owner or school admin or superadmin
    if request.user.is_teacher_user and live_class.teacher.user != request.user:
        return HttpResponseForbidden()
    elif not (request.user.is_teacher_user or request.user.is_schooladmin or request.user.is_superadmin):
        return HttpResponseForbidden()

    # All students in the class
    total_students_in_class = live_class.class_room.students.count()

    # Students who actually attended
    attendance_list = live_class.attendances.select_related("student")
    total_attendance_for_class = attendance_list.count()

    # Calculate attendance percent safely
    if total_students_in_class > 0:
        attendance_percent = (total_attendance_for_class / total_students_in_class) * 100
    else:
        attendance_percent = 0

    # Optional: For all live classes in the same school (summary)
    live_classes_in_school = LiveClass.objects.filter(school=school).annotate(
        attendance_count=Count("attendances")
    )

    # Optional: Total attendance in school
    total_attendance_in_school = LiveClassAttendance.objects.filter(live_class__school=school).count()

    return render(request, "liveclass/attendance_dashboard.html", {
        "live_class": live_class,
        "attendance_list": attendance_list,
        "total_attendance_for_class": total_attendance_for_class,
        "total_students_in_class": total_students_in_class,
        "attendance_percent": attendance_percent,
        "live_classes_in_school": live_classes_in_school,
        "total_attendance_in_school": total_attendance_in_school,
    })




from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import LiveClass

@login_required
def liveclass_start(request, pk):
    user = request.user
    live_class = get_object_or_404(
        LiveClass,
        pk=pk,
        school=user.school
    )

    # Permission check FIRST
    if user.is_teacher_user:
        if live_class.teacher.user != user:
            if not (user.is_schooladmin or user.is_superadmin):
                return HttpResponseForbidden("Not allowed to start this class.")
    elif not (user.is_schooladmin or user.is_superadmin):
        return HttpResponseForbidden("Permission denied.")

    # Only scheduled/upcoming classes can be started
    if live_class.status not in ["scheduled", "upcoming"]:
        return redirect("liveclass:liveclass_join", pk=pk)

    live_class.status = "live"
    live_class.actual_start_time = timezone.now()
    live_class.save()

    return redirect("liveclass:liveclass_join", pk=pk)


@login_required
def liveclass_leave(request, pk):
    """
    Marks a student as leaving a live class.
    Called via JS sendBeacon on window unload.
    """
    live_class = get_object_or_404(
        LiveClass,
        pk=pk,
        school=getattr(request.user, "school", None)
    )

    if not request.user.is_student_user:
        return HttpResponseForbidden("Only students can leave a class.")

    try:
        attendance = LiveClassAttendance.objects.get(
            live_class=live_class,
            student=request.user.student_profile,
            left_at__isnull=True  # only update if currently "in class"
        )
        attendance.left_at = timezone.now()
        attendance.total_duration += int(
            (attendance.left_at - attendance.joined_at).total_seconds()
        )
        attendance.save()
    except LiveClassAttendance.DoesNotExist:
        # student never joined or already left
        pass

    # sendBeacon doesn’t expect a redirect, just return 200 OK
    from django.http import HttpResponse
    return HttpResponse(status=200)


# views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@login_required
@csrf_exempt
def liveclass_enable_camera(request, pk):
    """
    Called via AJAX when a student enables their camera.
    Marks camera_enabled=True in attendance.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    live_class = get_object_or_404(LiveClass, pk=pk, school=request.user.school)
    
    if not request.user.is_student_user:
        return JsonResponse({"error": "Only students"}, status=403)

    attendance, _ = LiveClassAttendance.objects.get_or_create(
        live_class=live_class,
        student=request.user.student_profile
    )
    attendance.camera_enabled = True
    attendance.save()
    return JsonResponse({"success": True})


# views.py
from django.http import JsonResponse

@login_required
def liveclass_peers(request, pk):
    live_class = get_object_or_404(LiveClass, pk=pk, school=request.user.school)
    if not request.user.is_student_user:
        return JsonResponse({"error": "Only students"}, status=403)
    
    # return list of student IDs currently in attendance
    student_ids = list(live_class.attendances.filter(left_at__isnull=True).values_list('student__user_id', flat=True))
    return JsonResponse(student_ids, safe=False)
