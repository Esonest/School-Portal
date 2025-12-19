from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import Http404, FileResponse
from django.utils import timezone

from .models import Assignment, AssignmentSubmission, SubmissionFile
from .forms import AssignmentForm, SubmissionForm, GradeForm
from accounts.decorators import teacher_required
from results.utils import portal_required





# Helper to check if user is teacher
def is_teacher(user):
    return hasattr(user, 'teacher_profile') or user.is_staff

# ------------------------
# Teacher / Student dashboard
# ------------------------

@login_required
def dashboard(request):
    user = request.user

    # ------------------------
    # Identify profile & school
    # ------------------------
    teacher_profile = getattr(user, 'teacher_profile', None)
    student_profile = getattr(user, 'student_profile', None)

    if teacher_profile:
        school = teacher_profile.school
    elif student_profile:
        school = student_profile.school
    else:
        raise Http404("No teacher or student profile found.")

    # ------------------------

    # ------------------------
    # TEACHER DASHBOARD
    # ------------------------
    if teacher_profile:
        assignments = Assignment.objects.filter(
            teacher=teacher_profile
        ).order_by('-created_on')

        pending = AssignmentSubmission.objects.filter(
            assignment__teacher=teacher_profile,
            status='submitted'
        ).select_related('assignment', 'student').order_by('submitted_on')[:20]

        return render(request, 'assignments/dashboard.html', {
            'is_teacher': True,
            'assignments': assignments,
            'pending': pending
        })

    # ------------------------
    # STUDENT DASHBOARD
    # ------------------------
    student = student_profile
    student_class = student.school_class

    assignments = Assignment.objects.filter(
        published=True,
        classes=student_class
    ).order_by('-created_on').distinct()

    submissions = AssignmentSubmission.objects.filter(
        student=student
    ).select_related('assignment')

    subs_map = {s.assignment_id: s for s in submissions}

    return render(request, 'students/student_dashboard.html', {
        'is_teacher': False,
        'student': student,
        'assignments': assignments,
        'submissions': submissions,
        'subs_map': subs_map,
        'now': timezone.now(),
    })


# ------------------------
# Create or edit assignment (teacher)
# ------------------------

@login_required
@teacher_required
def create_assignment(request, pk=None):
    user = request.user
    teacher_profile = getattr(user, 'teacher_profile', None)
    if not teacher_profile:
        raise Http404("No teacher profile found.")

    assignment = get_object_or_404(Assignment, pk=pk, teacher=teacher_profile) if pk else None

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.teacher = teacher_profile         # Must be Teacher instance
            obj.school = teacher_profile.school   # Must be School instance
            obj.save()
            form.save_m2m()
            messages.success(request, "Assignment saved successfully.")
            return redirect('assignments:dashboard')
    else:
        form = AssignmentForm(instance=assignment)

    return render(request, 'assignments/create.html', {
        'form': form,
        'assignment': assignment
    })

# ------------------------
# Assignment detail & submissions
# ------------------------

@login_required
@teacher_required
def teacher_assignment_detail(request, pk):
    teacher_profile = getattr(request.user, 'teacher_profile', None)
    assignment = get_object_or_404(Assignment, pk=pk, teacher=teacher_profile)
    submissions = assignment.submissions.select_related('student').all()
    return render(request, 'assignments/teacher_assignment_detail.html', {
        'assignment': assignment,
        'submissions': submissions
    })

# ------------------------
# Delete assignment
# ------------------------

@login_required
@teacher_required
def delete_assignment(request, pk):
    teacher_profile = getattr(request.user, 'teacher_profile', None)
    assignment = get_object_or_404(Assignment, pk=pk, teacher=teacher_profile)

    if request.method == 'POST':
        assignment.delete()
        messages.success(request, "Assignment deleted successfully.")
        return redirect('assignments:dashboard')

    return render(request, 'assignments/confirm_delete.html', {'assignment': assignment})

# ------------------------
# Student: view assignment
# ------------------------

@login_required
def student_assignment_detail(request, pk):
    student = getattr(request.user, 'student_profile', None)
    if not student:
        raise Http404("Student required")
    assignment = get_object_or_404(Assignment, pk=pk, published=True, classes=student.school_class)
    submission = AssignmentSubmission.objects.filter(assignment=assignment, student=student).first()
    return render(request, 'assignments/student_assignment_detail.html', {
        'assignment': assignment,
        'submission': submission
    })

# ------------------------
# Student: submit assignment
# ------------------------

@login_required
@transaction.atomic
def submit_assignment(request, pk):
    student = getattr(request.user, 'student_profile', None)
    if not student:
        raise Http404("Student required")
    assignment = get_object_or_404(Assignment, pk=pk, published=True, classes=student.school_class)
    submission, _ = AssignmentSubmission.objects.get_or_create(
        assignment=assignment,
        student=student,
        defaults={'status': 'submitted'}
    )

    if request.method == 'POST':
        form = SubmissionForm(request.POST, instance=submission)
        files = request.FILES.getlist('file')
        if form.is_valid():
            obj = form.save(commit=False)
            obj.status = 'late' if assignment.due_date and timezone.now() > assignment.due_date else 'submitted'
            obj.save()
            for f in files:
                SubmissionFile.objects.create(submission=obj, file=f)
            messages.success(request, "Your assignment has been submitted.")
            return redirect('assignments:dashboard')
    else:
        form = SubmissionForm(instance=submission)

    return render(request, 'assignments/submit_assignment.html', {
        'form': form,
        'assignment': assignment,
        'submission': submission
    })

# Teacher: grade a submission

@login_required
def grade_submission(request, submission_id):
    """
    Allow only teachers (owners of the assignment) to grade a submission.
    """
    user = request.user

    # --- Access control ---
    teacher = getattr(user, 'teacher_profile', None)
    if not teacher and not user.is_staff:
        messages.error(request, "Only teachers can access grading.")
        return redirect('assignments:dashboard')

    # --- Retrieve the submission ---
    submission = get_object_or_404(
        AssignmentSubmission.objects.select_related('assignment', 'student'),
        pk=submission_id
    )

    # --- Verify ownership (only the teacher who created the assignment can grade it) ---
    if submission.assignment.teacher != user and not user.is_staff:
        raise Http404("You are not authorized to grade this submission.")

    # --- Process form submission ---
    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            score = form.cleaned_data['score']
            feedback = form.cleaned_data['feedback']

            # Call model method for grading
            submission.mark_graded(score, feedback, user)

            messages.success(request, "Submission graded successfully.")
            return redirect('assignments:teacher_assignment_detail', pk=submission.assignment.pk)
    else:
        # Pre-fill form with existing grading info
        form = GradeForm(initial={
            'score': submission.score or submission.assignment.max_score,
            'feedback': submission.feedback
        })

    context = {
        'form': form,
        'submission': submission,
    }
    return render(request, 'assignments/grade_submission.html', context)

# Download submission file

@login_required
def download_submission_file(request, file_id):
    sf = get_object_or_404(SubmissionFile, pk=file_id)
    # permission: teacher of the assignment or the student who uploaded
    user = request.user
    student = getattr(user, 'student_profile', None) or getattr(user, 'student', None)
    if sf.submission.student.user == user or sf.submission.assignment.teacher == user or user.is_staff:
        return FileResponse(sf.file.open('rb'), as_attachment=True, filename=sf.filename())
    raise Http404("Not authorized to download this file")

# List submissions for admin/teacher or student

@login_required
def submission_list(request, assignment_id=None):
    user = request.user
    if is_teacher(user):
        qs = AssignmentSubmission.objects.filter(assignment__teacher=user).order_by('-submitted_on')
    else:
        student = getattr(user, 'student_profile', None) or getattr(user, 'student', None)
        qs = AssignmentSubmission.objects.filter(student=student).order_by('-submitted_on')
    if assignment_id:
        qs = qs.filter(assignment_id=assignment_id)
    return render(request, 'assignments/submission_list.html', {'submissions': qs})
