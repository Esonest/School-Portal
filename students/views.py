from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.http import Http404
from django.urls import reverse
from django.utils.timezone import localtime, now  
from django.utils.timesince import timesince
from .models import Student
from .forms import StudentProfileForm
from results.models import Score
from attendance.models import Attendance
from assignments.models import Assignment, AssignmentSubmission 
from cbt.models import CBTExam, CBTSubmission 
from results.utils import portal_required

# ------------------------
# Helper Decorators
# ------------------------
def student_required(view_func):
    return user_passes_test(
        lambda u: hasattr(u, 'student_profile') or hasattr(u, 'student'),
        login_url='accounts:login'
    )(view_func)


# ------------------------
# Student Dashboard
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime, now as timezone_now
from assignments.models import Assignment, AssignmentSubmission
from django.utils import timezone
from django.contrib import messages
from results.utils import portal_required



@login_required
@student_required
def student_dashboard(request):



    student = getattr(request.user, 'student_profile', None) or getattr(request.user, 'student', None)
    if not student:
        return redirect("accounts:portal_selection")

    now = localtime(timezone.now())
    

    # ✅ Assignments
    assignments = list(Assignment.objects.filter(
        published=True,
        classes__in=[student.school_class]
    ).distinct().order_by('-created_on'))

    # ✅ Active CBTs
    active_cbts = list(CBTExam.objects.filter(
        active=True,
        school_class=student.school_class,
        start_time__lte=now,
        end_time__gte=now
    ).order_by('start_time'))

    # ✅ Upcoming CBTs
    upcoming_cbts = list(CBTExam.objects.filter(
        active=True,
        school_class=student.school_class,
        start_time__gt=now
    ).order_by('start_time'))
    
    recent_results = CBTSubmission.objects.filter(
        student=student,
        completed_on__isnull=False
    ).order_by('-completed_on')[:5]
    

    context = {
        'student': student,
        'assignments': assignments,
        'recent_results': recent_results,
        'active_cbts': active_cbts,
        'upcoming_cbts': upcoming_cbts,
        'now': now,
    }
    return render(request, 'students/student_dashboard.html', context)





# students/views.py
from notes.models import LessonNote  # import Note model

@login_required
@student_required
def notes_list(request):
    student = request.user.student_profile
    notes = LessonNote.objects.filter(
        classes=student.school_class,
        publish_date__lte=timezone.now().date()
    ).order_by('-publish_date')

    print(f"DEBUG: {notes.count()} notes found for {student.school_class}")
    for n in notes:
        print(f" - {n.title} ({n.publish_date}) for {[c.name for c in n.classes.all()]}")

    return render(request, 'students/notes.html', {
        'student': student,
        'notes': notes,
    })


@login_required
@student_required
def note_detail(request, pk):
    student = request.user.student_profile
    note = get_object_or_404(LessonNote, pk=pk, classes=student.school_class)
    return render(request, 'students/note_detail.html', {
        'student': student,
        'note': note,
    })





# ------------------------
# CBT List View
# ------------------------
@portal_required("cbt")
@login_required
@student_required
def cbt_list(request):
    student = getattr(request.user, 'student_profile', None) or getattr(request.user, 'student', None)
    exams = CBTExam.objects.all().order_by('-start_time')
    submissions = CBTSubmission.objects.filter(student=student)
    return render(request, 'students/cbt_list.html', {
        'student': student,
        'exams': exams,
        'submissions': submissions,
    })


# ------------------------
# Student Profile
# ------------------------
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
@student_required
def profile_view(request):
    student = getattr(request.user, 'student_profile', None)

    if request.method == "POST":
        form = StudentProfileForm(request.POST, request.FILES, instance=student)
        try:
            if form.is_valid():
                profile = form.save(commit=False)

                # Handle Clear/Remove photo
                if request.POST.get("clear_photo") == "1":
                    if profile.photo:
                        profile.photo.delete(save=False)
                    profile.photo = None

                if not student:
                    profile.user = request.user

                profile.save()

                # AJAX response
                photo_url = profile.photo.url if profile.photo else ""
                data = {
                    "success": True,
                    "dob": profile.dob.strftime('%Y-%m-%d') if profile.dob else "",
                    "gender": profile.get_gender_display() if profile.gender else "",
                    "photo_url": photo_url,
                }

                if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                    return JsonResponse(data)

                return render(request, 'students/profile.html', {"student": profile, "form": form})

            else:
                errors = form.errors.get_json_data()
                if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                    return JsonResponse({"success": False, "errors": errors}, status=400)

        except Exception as e:
            if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}}, status=500)
            else:
                raise

    else:
        form = StudentProfileForm(instance=student)

    return render(request, 'students/profile.html', {"student": student, "form": form})



@student_required
def results_list(request):
    student = getattr(request.user, 'student_profile', None) or getattr(request.user, 'student', None)
    qs = Result.objects.filter(student=student).select_related('exam').order_by('-exam__date')
    return render(request, 'students/results_list.html', {'student': student, 'results': qs})

@student_required
def result_detail(request, pk):
    student = getattr(request.user, 'student_profile', None) or getattr(request.user, 'student', None)
    res = get_object_or_404(Result, pk=pk, student=student)
    res.compute()
    scores = Score.objects.filter(student=res.student, exam=res.exam).select_related('subject')
    affective = res.student and []
    psychomotor = res.student and []
    return render(request, 'students/result_detail.html', {
        'result': res,
        'scores': scores,
        'affective': affective,
        'psychomotor': psychomotor,
    })

@student_required
def download_pdf(request, pk):
    # redirect to results app pdf view (if available)
    try:
        return redirect(reverse('results:detail_pdf', kwargs={'pk': pk}))
    except Exception:
        raise Http404('PDF generation not available')

@student_required
def cumulative_view(request, session):
    student = getattr(request.user, 'student_profile', None) or getattr(request.user, 'student', None)
    data = compute_cumulative(student, session)
    return render(request, 'students/cumulative.html', {'student': student, 'data': data, 'session': session})




# students/views.py
from datetime import timedelta
from django.utils.timezone import now
from assignments.models import Assignment, AssignmentSubmission

@login_required
@student_required
def assignments_list(request):
    student = getattr(request.user, 'student_profile', None) or getattr(request.user, 'student', None)
    assignments = Assignment.objects.filter(
        published=True,
        classes=student.school_class
    ).order_by('-created_on')

    submissions = AssignmentSubmission.objects.filter(student=student)
    subs_map = {sub.assignment_id: sub for sub in submissions}

    # Prepare assignment details
    for a in assignments:
        sub = subs_map.get(a.id)
        a.submitted = bool(sub)
        a.submission = sub
        a.is_overdue = a.due_date and a.due_date < now()
        a.is_due_soon = a.due_date and not a.is_overdue and (a.due_date - now()).days <= 2

    a.time_left = (
        timesince(now(), a.due_date) + " left"
    if a.due_date and not a.is_overdue else ""
    )    

    return render(request, 'students/assignments.html', {
        'student': student,
        'assignments': assignments,
    })

@student_required
def attendance_report(request):
    student = getattr(request.user, 'student_profile', None) or getattr(request.user, 'student', None)
    records = AttendanceRecord.objects.filter(student=student).order_by('-date')[:200]
    total = records.count()
    present = records.filter(present=True).count()
    attendance_pct = (present/total*100) if total else None
    return render(request, 'students/attendance.html', {'records': records, 'attendance_pct': attendance_pct})

@student_required
def cbt_list(request):
    student = getattr(request.user, 'student_profile', None) or getattr(request.user, 'student', None)
    exams = CBTExam.objects.order_by('-start_time')
    results = CBTResult.objects.filter(student=student)
    return render(request, 'students/cbt_list.html', {'exams': exams, 'results': results})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import student_required


    

@login_required
@student_required
def student_result_dashboard(request):
    student = request.user.student_profile
    # Assuming you have a Result model
    results = student.cbtresult_set.all()  
    context = {'student': student, 'results': results}
    return render(request, 'accounts/student_result_dashboard.html', context)




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import Announcement
from .forms import AnnouncementForm


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from django.db.models import Q

@portal_required("announcement")
@login_required
def announcement_list(request):

    school = request.user.school

    now = timezone.now()

    announcements = (
        Announcement.objects
        .filter(school=school)
        .select_related(
            "created_by"
        )
        .prefetch_related(
            "school_classes",
            "students"
        )
        .order_by("-publish_date")
    )

    active_count = announcements.filter(
        is_active=True
    ).filter(
        Q(expiry_date__isnull=True) |
        Q(expiry_date__gte=now)
    ).count()

    expired_count = announcements.filter(
        expiry_date__lt=now
    ).count()

    context = {
        "announcements": announcements,
        "active_count": active_count,
        "expired_count": expired_count,
    }

    return render(
        request,
        "announcements/announcement_list.html",
        context,
    )


from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .forms import AnnouncementForm
from .models import Announcement

from students.services.tasks import process_announcement
from students.services.async_runner import run_async



@login_required
def announcement_create(request):

    school = request.user.school

    if request.method == "POST":

        form = AnnouncementForm(
            request.POST,
            school=school
        )

        if form.is_valid():

            announcement = form.save(commit=False)

            announcement.school = school

            announcement.created_by = request.user

            announcement.save()
            form.save_m2m()

            

            run_async(process_announcement, announcement)

            messages.success(
                request,
                "Announcement created and is being sent..."
            )

            return redirect(
                "students:announcement_list"
            )

    else:

        form = AnnouncementForm(
            school=school
        )

    return render(
        request,
        "announcements/announcement_form.html",
        {
            "form": form
        }
    )


@login_required
def announcement_update(request, pk):

    school = request.user.school

    announcement = get_object_or_404(
        Announcement,
        pk=pk,
        school=school
    )

    if request.method == "POST":

        form = AnnouncementForm(
            request.POST,
            instance=announcement,
            school=school
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Announcement updated successfully."
            )

            return redirect(
                "students:announcement_list"
            )

    else:

        form = AnnouncementForm(
            instance=announcement,
            school=school
        )

    return render(
        request,
        "announcements/announcement_form.html",
        {
            "form": form
        }
    )


@login_required
def announcement_delete(request, pk):
    school = request.user.school

    announcement = get_object_or_404(
        Announcement,
        pk=pk,
        school=school
    )

    if request.method == "POST":
        announcement.delete()
        messages.success(
            request,
            "Announcement deleted successfully."
        )
        return redirect("students:announcement_list")

    return render(
        request,
        "announcements/announcement_confirm_delete.html",
        {"announcement": announcement}
    )



import json

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def whatsapp_webhook(request):

    if request.method == "GET":

        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if (
            mode == "subscribe"
            and token == settings.WHATSAPP_VERIFY_TOKEN
        ):
            return HttpResponse(challenge)

        return HttpResponse("Forbidden", status=403)

    elif request.method == "POST":

        body = json.loads(request.body)

        print("=" * 80)
        print("WHATSAPP WEBHOOK")
        print(json.dumps(body, indent=4))
        print("=" * 80)

        try:

            for entry in body.get("entry", []):

                for change in entry.get("changes", []):

                    value = change.get("value", {})

                    # Incoming messages
                    if "messages" in value:
                        print("Incoming Message")
                        print(value["messages"])

                    # Delivery statuses
                    if "statuses" in value:

                        for status in value["statuses"]:

                            print("-" * 50)
                            print("MESSAGE STATUS")
                            print("ID:", status.get("id"))
                            print("STATUS:", status.get("status"))
                            print("RECIPIENT:", status.get("recipient_id"))

                            if status.get("errors"):
                                print("ERRORS:")
                                print(status["errors"])

                            print("-" * 50)

        except Exception as e:

            print("WEBHOOK ERROR:", e)

        return JsonResponse({"status": "ok"})

    return HttpResponse(status=405)

from django.http import JsonResponse


@login_required
def load_students_by_class(
    request
):

    class_ids = request.GET.get(
        "class_ids",
        ""
    ).split(",")

    students = Student.objects.filter(
        school_class_id__in=class_ids
    ).select_related(
        "user"
    )

    data = []

    for s in students:

        data.append({
            "id": s.id,
            "name": s.full_name()
        })

    return JsonResponse({
        "students": data
    })


from django.shortcuts import render, get_object_or_404
from students.models import Student

def student_verify(request, student_uuid):

    student = get_object_or_404(
        Student,
        student_uuid=student_uuid,
        is_active=True
    )

    return render(
        request,
        "students/student_verify.html",
        {
            "student": student,
            "school": student.school,
        }
    )

from results.utils import generate_student_qr
from accounts.decorators import school_admin_or_superadmin_required
from accounts.models import School

@login_required
@school_admin_or_superadmin_required
def student_id_card(
    request,
    school_id,
    student_id
):

    school = get_object_or_404(
        School,
        id=school_id
    )

    student = get_object_or_404(
        Student,
        id=student_id,
        school=school
    )

    qr_data_uri = generate_student_qr(student)

    return render(
        request,
        "students/id_card.html",
        {
            "student": student,
            "school": school,
            "qr_data_uri": qr_data_uri,
        }
    )


from django.shortcuts import get_object_or_404, render
from students.models import Student, SchoolClass
from accounts.models import School

@login_required
@school_admin_or_superadmin_required
def class_id_cards(
    request,
    school_id,
    class_id
):

    school = get_object_or_404(
        School,
        id=school_id
    )

    school_class = get_object_or_404(
        SchoolClass,
        id=class_id,
        school=school
    )

    students = Student.objects.filter(
        school=school,
        school_class=school_class,
        is_active=True
    ).select_related(
        "user",
        "school_class"
    ).order_by(
        "user__first_name",
        "user__last_name"
    )

    cards = []

    for student in students:

        cards.append({
            "student": student,
            "qr": generate_student_qr(student)
        })

    return render(
        request,
        "students/class_id_cards.html",
        {
            "school": school,
            "school_class": school_class,
            "cards": cards,
        }
    )    