from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.contrib import messages

from attendance.models import Attendance
from attendance.forms import AttendanceForm, BulkAttendanceForm
from students.models import Student, SchoolClass
from results.utils import portal_required, SESSION_LIST
from results.models import Score
from django.db.models import Count, Q
import json    



# -------------------------------------------------------
# ROLE CHECK HELPERS
# -------------------------------------------------------

def is_teacher(user):
    return hasattr(user, "teacher_profile")


def get_teacher(user):
    if not is_teacher(user):
        raise Http404("Teacher access required")
    return user.teacher_profile


# -------------------------------------------------------
# DASHBOARD VIEW
# -------------------------------------------------------
@portal_required("attendance")
@login_required
def dashboard(request):
    user = request.user

    # ----------------------
    # TEACHER DASHBOARD
    # ----------------------
    if is_teacher(user):
        teacher = user.teacher_profile
        classes = teacher.classes.all()

        return render(request, "attendance/dashboard.html", {
            "teacher": teacher,
            "classes": classes,
            "is_teacher": True,
        })

    # ----------------------
    # STUDENT DASHBOARD
    # ----------------------
    student = getattr(user, "student_profile", None)
    if not student:
        raise Http404("Student profile required")

 
    selected_session = request.GET.get("session") or ""
    selected_term = request.GET.get("term") or ""

    attendances = Attendance.objects.filter(student=student)

    if selected_session:
        attendances = attendances.filter(session=selected_session)

    if selected_term:
        attendances = attendances.filter(term=selected_term)

    attendances = attendances.order_by("-date")
    present_count = attendances.filter(status="present").count()


    total = attendances.count()
    present = attendances.filter(status="present").count()

    attendance_percent = 0
    if total > 0:
        attendance_percent = round((present / total) * 100, 1)


    term_stats = (
        attendances.values("term")
        .annotate(
            total=Count("id"),
            present=Count("id", filter=Q(status="present"))
        )
    )

# calculate percentage per term
    term_stats_list = []
    for t in term_stats:
        percent = 0
        if t["total"] > 0:
            percent = round((t["present"] / t["total"]) * 100, 1)

        term_stats_list.append({
            "term": t["term"],
            "percent": percent,
            "total": t["total"],
        }) 
    
  
    daily_trend = (
        attendances.values("date")
        .annotate(total=Count("id"))
        .order_by("date")
    )

    daily_trend_json = json.dumps(list(daily_trend), default=str)


    return render(request, "attendance/student_attendance.html", {
        "attendances": attendances,
        "student": student,
        "sessions": SESSION_LIST,
        "terms": [t[0] for t in Score.TERM_CHOICES],
        "selected_session": selected_session,
        "selected_term": selected_term,
        "present_count": present_count,
        "attendance_percent": attendance_percent,
        "term_stats": term_stats_list,
        "daily_trend": daily_trend_json,

    })



# -------------------------------------------------------
# TEACHER MARK ATTENDANCE
# -------------------------------------------------------
@portal_required("attendance")
@login_required
def mark_attendance(request, class_id):
    teacher = get_teacher(request.user)

    cls = get_object_or_404(SchoolClass, id=class_id)

    # Ensure this teacher teaches this class
    if cls not in teacher.classes.all():
        messages.error(request, "You are not assigned to this class.")
        return redirect("attendance:dashboard")

    # Get all students in this class
    students = Student.objects.filter(school_class=cls)
    if not students.exists():
        messages.warning(request, f"No students found in class {cls.name}.")
        return redirect("attendance:dashboard")

    # -------------------
    # POST - Save Attendance
    # -------------------
    if request.method == "POST":
        form = BulkAttendanceForm(request.POST, class_queryset=students)

        if form.is_valid():
            date = form.cleaned_data["date"]
            status = form.cleaned_data["status"]
            selected_students = form.cleaned_data["students"]
            session = form.cleaned_data["session"]
            term = form.cleaned_data["term"]

            for student in selected_students:
                record, created = Attendance.objects.get_or_create(
                    student=student,
                    date=date,
                    defaults={
                        "status": status,
                        "marked_by": request.user,  
                        "school": student.school,
                        "session": session,   
                        "term": term,   
                    }
                )

                if not created:
                    record.status = status
                    record.session = session   
                    record.term = term  
                    record.marked_by = request.user,
                    record.save()

            messages.success(
                request,
                f"Attendance marked for {len(selected_students)} students on {date}."
            )
            return redirect("attendance:dashboard")

    else:
        form = BulkAttendanceForm(class_queryset=students)

    return render(request, "attendance/mark_attendance.html", {
        "form": form,
        "cls": cls,
        "students": students,
    })


@portal_required("attendance")
@login_required
def attendance_report(request):
    teacher = get_teacher(request.user)

    selected_session = request.GET.get("session") or ""
    selected_term = request.GET.get("term") or ""

    classes = teacher.classes.all()
    report_data = []

    for cls in classes:

        records = Attendance.objects.filter(student__school_class=cls)

        # ✅ FILTER BY SESSION
        if selected_session:
            records = records.filter(session=selected_session)

        # ✅ FILTER BY TERM
        if selected_term:
            records = records.filter(term=selected_term)

        total_records = records.count()

        present_count = records.filter(status="present").count()
        absent_count = records.filter(status="absent").count()

        # ✅ CALCULATE PERCENTAGE
        percentage = 0
        if total_records > 0:
            percentage = round((present_count / total_records) * 100, 1)

        latest = records.order_by("-date").first()    

        report_data.append({
            "class": cls,
            "total": cls.students.count(),
            "present": present_count,
            "absent": absent_count,
            "percentage": percentage,
            "session": latest.session if latest else None,
            "term": latest.term if latest else None,
        })

    return render(request, "attendance/attendance_report.html", {
        "report_data": report_data,
        "sessions": SESSION_LIST,
        "terms": [t[0] for t in Score.TERM_CHOICES],
        "selected_session": selected_session,
        "selected_term": selected_term,
    })


@portal_required("attendance")
@login_required
def class_attendance_detail(request, class_id):
    teacher = get_teacher(request.user)

    cls = get_object_or_404(SchoolClass, id=class_id)

    # Ensure teacher has rights
    if cls not in teacher.classes.all():
        raise Http404("You are not assigned to this class")

    students = cls.students.all()

    student_attendance = []
    for student in students:
        record = Attendance.objects.filter(
            student=student
        ).order_by("-date").first()

        student_attendance.append({
            "student": student,
            "status": record.status if record else "N/A",
            "date": record.date if record else None,
        })

    return render(request, "attendance/class_attendance_detail.html", {
        "cls": cls,
        "student_attendance": student_attendance,
    })
