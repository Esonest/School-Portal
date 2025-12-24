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
from cbt.models import CBTExam, CBTSubmission # ✅ your actual models

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
@login_required
@student_required
def profile_view(request):
    student = getattr(request.user, 'student_profile', None) or getattr(request.user, 'student', None)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('students:profile')
    else:
        form = StudentProfileForm(instance=student)
    return render(request, 'students/profile.html', {'student': student, 'form': form})


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
