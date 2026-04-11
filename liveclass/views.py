from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db.models import Count
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

from .models import LiveClass,LiveClassAttendance
from .forms import LiveClassForm
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
import requests

import jwt
import time
from django.conf import settings

import time
import uuid
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def generate_100ms_token(payload):
    return jwt.encode({
        "access_key": settings.HMS_API_KEY,
        "room_id": payload.get("room_id"),
        "user_id": payload.get("user_id"),
        "role": payload.get("role"),
        "type": "app",
        "version": 2,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,
        "jti": str(uuid.uuid4()),
    }, settings.HMS_API_SECRET, algorithm="HS256")


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

import os

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

            # ✅ ASSIGN ROOM ID HERE
            live_class.room_id = os.getenv("ROOM_ID")

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


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from .models import LiveClass, LiveClassAttendance
import uuid
from django.http import JsonResponse

@login_required
def liveclass_join(request, pk):
    user = request.user
    school = getattr(user, "school", None)

    live_class = get_object_or_404(LiveClass, pk=pk, school=school)

    # Permission check
    if not any([
        getattr(user, "is_student_user", False),
        getattr(user, "is_teacher_user", False),
        getattr(user, "is_schooladmin", False),
        getattr(user, "is_superadmin", False),
    ]):
        return HttpResponseForbidden()

    # Ensure class is live
    live_class.update_status()
    if live_class.status != "live":
        messages.error(request, "Class is not currently active.")
        return redirect("liveclass:liveclass_list")

    # Assign role
    if getattr(user, "is_teacher_user", False) or getattr(user, "is_schooladmin", False) or getattr(user, "is_superadmin", False):
        role = "teacher"
    else:
        role = "student"

    # Create room if missing
    if not live_class.room_id:
        import uuid
        live_class.room_id = str(uuid.uuid4())
        live_class.save()

    room_created = create_100ms_room_if_missing(live_class.room_id)
    if not room_created:
        messages.error(request, "Unable to create or access 100ms room. Check API keys.")
        return redirect("liveclass:liveclass_list")

    # Attendance (students only)
    if getattr(user, "is_student_user", False):
        attendance, created = LiveClassAttendance.objects.get_or_create(
            live_class=live_class,
            student=request.user.student_profile
        )
        if not created and attendance.left_at:
            attendance.joined_at = timezone.now()
            attendance.left_at = None
            attendance.save()

    # Generate app token for frontend
    token = generate_100ms_app_token(user.id, role, live_class.room_id)
    return JsonResponse({
        "token": token,
        "role": role,
        "room_id": live_class.room_id,
        "username": user.get_full_name() or user.username,
    })
    

    print(f"🎯 DEBUG: USER: {user.id}, ROLE: {role}, ROOM: {live_class.room_id}")
    print(f"Token length: {len(token)}")

import requests
from django.conf import settings

def start_recording(room_id):
    payload = {
        "access_key": settings.HMS_API_KEY,
        "type": "management",
        "version": 2,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }

    management_token = jwt.encode(
        payload,
        settings.HMS_API_SECRET,
        algorithm="HS256"
    )

    url = f"https://api.100ms.live/v2/recordings/room/{room_id}/start"

    requests.post(
        url,
        headers={
            "Authorization": f"Bearer {management_token}"
        }
    )   


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
        LiveClass.objects.prefetch_related(     "attendances__student", "class_room__students"),
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


from django.http import JsonResponse

@login_required
def heartbeat(request, pk):
    attendance = LiveClassAttendance.objects.filter(
        live_class_id=pk,
        student=request.user.student_profile
    ).first()

    if attendance:
        attendance.last_seen = timezone.now()
        attendance.save()

    return JsonResponse({"status": "ok"})    


@csrf_exempt
def recording_webhook(request):
    data = json.loads(request.body)

    if data.get("type") == "recording.success":
        room_id = data["data"]["room_id"]
        url = data["data"]["url"]

        live_class = LiveClass.objects.filter(room_id=room_id).first()
        if live_class:
            live_class.recording_url = url
            live_class.save()

    return JsonResponse({"status": "ok"})

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


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from django.http import JsonResponse
from .models import LiveClass

# views.py
import uuid
import time
import jwt
import requests
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import LiveClass

# ------------------------------
# Utility functions
# ------------------------------

def generate_management_token():
    """Generate a valid 100ms management token"""
    payload = {
        "access_key": settings.HMS_API_KEY,
        "type": "management",
        "version": 2,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.HMS_API_SECRET, algorithm="HS256")

def create_100ms_room_if_missing(room_id: str):
    """Return REAL 100ms room_id"""
    mgmt_token = generate_management_token()
    headers = {"Authorization": f"Bearer {mgmt_token}"}
    base_url = "https://api.100ms.live/v2/rooms"

    # 1. Try to fetch room (if it already exists in 100ms)
    resp = requests.get(f"{base_url}/{room_id}", headers=headers)

    if resp.status_code == 200:
        data = resp.json()
        real_room_id = data["id"]
        print(f"✅ Existing Room ID: {real_room_id}")
        return real_room_id  # ✅ RETURN REAL ID

    # 2. Create new room
    data = {
        "name": f"Room-{room_id}",
        "region": "us",
        "template_id": "69c6dc546236da36a7d8f3f4",
    }

    resp = requests.post(base_url, json=data, headers=headers)

    if resp.status_code in [200, 201]:
        room_data = resp.json()

        # 🔥 THIS IS WHERE IT GOES
        real_room_id = room_data["id"]
        print(f"✅ Created Room ID: {real_room_id}")

        return real_room_id  # ✅ IMPORTANT

    # ❌ Failure
    print(f"❌ Failed to create room: {resp.status_code} {resp.text}")
    return None


def generate_100ms_app_token(user_id, role, room_id):
    """Generate a 100ms app token for the frontend"""
    payload = {
        "access_key": settings.HMS_API_KEY,
        "room_id": room_id,
        "user_id": str(user_id),
        "role": role,
        "type": "app",
        "version": 2,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,  # 24h expiry
        "jti": str(uuid.uuid4()),
    }
    print("🎯 TOKEN PAYLOAD:", payload)
    return jwt.encode(payload, settings.HMS_API_SECRET, algorithm="HS256")


# ------------------------------
# API View: get token
# ------------------------------

@login_required
def liveclass_token_api(request, pk):
    user = request.user
    live_class = get_object_or_404(LiveClass, pk=pk, school=getattr(user, "school", None))

    # Determine role
    if getattr(user, "is_teacher_user", False) or getattr(user, "is_schooladmin", False) or getattr(user, "is_superadmin", False):
        role = "teacher"
    else:
        role = "student"

    # Ensure room_id exists
    # Ensure local room_id exists (temporary UUID)
    if not live_class.room_id:
        live_class.room_id = str(uuid.uuid4())
        live_class.save()

# ✅ Create / fetch REAL 100ms room ID
    real_room_id = create_100ms_room_if_missing(live_class.room_id)

    if not real_room_id:
        return JsonResponse({"error": "Room creation failed"}, status=500)

# ✅ VERY IMPORTANT: store REAL 100ms room ID
    if live_class.room_id != real_room_id:
        live_class.room_id = real_room_id
        live_class.save()

# Generate token with REAL room ID
    token = generate_100ms_app_token(user.id, role, live_class.room_id)

    return JsonResponse({
        "token": token,
        "role": role,
        "room_id": live_class.room_id,
        "username": user.get_full_name() or user.username,
    })

@login_required
def start_recording_api(request, pk):
    live_class = get_object_or_404(LiveClass, pk=pk, school=request.user.school)

    if not (request.user.is_teacher_user or request.user.is_schooladmin or request.user.is_superadmin):
        return JsonResponse({"error": "Forbidden"}, status=403)

    start_recording(live_class.room_id)

    return JsonResponse({"success": True})    


from django.contrib.auth import get_user_model
User = get_user_model()

@login_required
def approve_user(request):
    if not (request.user.is_teacher_user or request.user.is_schooladmin or request.user.is_superadmin):
        return JsonResponse({"error": "Forbidden"}, status=403)

    user_id = request.POST.get("user_id")
    user = User.objects.get(id=user_id)

    token = generate_100ms_app_token(user.id, "student", None)

    return JsonResponse({"token": token})


@login_required
def move_to_breakout(request):
    if not (request.user.is_teacher_user or request.user.is_schooladmin or request.user.is_superadmin):
        return JsonResponse({"error": "Forbidden"}, status=403)

    user_id = request.POST.get("user_id")
    room = request.POST.get("room")

    token = generate_100ms_app_token(user_id, room, None)

    return JsonResponse({"token": token})

# views.py
import requests
from django.http import JsonResponse
import json

# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def translate(request):
    if request.method == "POST":
        data = json.loads(request.body)
        text = data.get("text", "")
        target = data.get("target", "en")

        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "auto",
                "tl": target,
                "dt": "t",
                "q": text,
            }

            response = requests.get(url, params=params)
            result = response.json()

            translated = result[0][0][0]

            return JsonResponse({"translated": translated})
        except Exception as e:
            return JsonResponse({"translated": text, "error": str(e)})

    return JsonResponse({"error": "Invalid method"}, status=400)



def liveclass_frontend(request, pk=None):
    return render(request, "frontend/index.html")    