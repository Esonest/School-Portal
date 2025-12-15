from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.contrib import messages

from attendance.models import Attendance
from attendance.forms import AttendanceForm, BulkAttendanceForm
from students.models import Student, SchoolClass
from results.utils import portal_required


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

    attendances = Attendance.objects.filter(student=student).order_by("-date")

    return render(request, "attendance/student_attendance.html", {
        "attendances": attendances,
        "student": student,
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

            for student in selected_students:
                record, created = Attendance.objects.get_or_create(
                    student=student,
                    date=date,
                    defaults={
                        "status": status,
                        "marked_by": teacher,  # FIXED HERE ✔
                        "school": student.school,
                    }
                )

                if not created:
                    record.status = status
                    record.marked_by = teacher   # FIXED HERE ✔
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


# -------------------------------------------------------
# TEACHER CLASS REPORT SUMMARY
# -------------------------------------------------------
@portal_required("attendance")
@login_required
def attendance_report(request):
    teacher = get_teacher(request.user)

    classes = teacher.classes.all()
    report_data = []

    for cls in classes:
        total_students = cls.student_set.count()

        present_count = Attendance.objects.filter(
            student__school_class=cls,
            status="present"
        ).count()

        absent_count = Attendance.objects.filter(
            student__school_class=cls,
            status="absent"
        ).count()

        report_data.append({
            "class": cls,
            "total": total_students,
            "present": present_count,
            "absent": absent_count,
        })

    return render(request, "attendance/attendance_report.html", {
        "report_data": report_data
    })


# -------------------------------------------------------
# CLASS ATTENDANCE DETAIL VIEW
# -------------------------------------------------------
@portal_required("attendance")
@login_required
def class_attendance_detail(request, class_id):
    teacher = get_teacher(request.user)

    cls = get_object_or_404(SchoolClass, id=class_id)

    # Ensure teacher has rights
    if cls not in teacher.classes.all():
        raise Http404("You are not assigned to this class")

    students = cls.student_set.all()

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
