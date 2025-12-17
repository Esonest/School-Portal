
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.models import School, User
from attendance.models import Attendance
from results.models import ClassScoreSetting, ClassSubjectTeacher
# Permission checks
def is_superadmin(user):
    return user.role == 'superadmin'

def is_schooladmin(user):
    return user.role == 'schooladmin'

@login_required
@user_passes_test(is_superadmin)
def super_admin_dashboard(request):
    schools = School.objects.all()

    # Define portal links here
    portal_links = [
        ('Students', 'students'),
        ('Teachers', 'teachers'),
        ('Results', 'results'),
        ('CBT', 'cbt'),
        ('Notes', 'notes'),
        ('Assignments', 'assignments'),
        ('Attendance', 'attendance'),
    ]

    context = {
        'schools': schools,
        'user_role': 'Super Admin',
        'portal_links': portal_links,
    }
    return render(request, 'school_admin/super_admin_dashboard.html', context)


@login_required
@user_passes_test(is_schooladmin)
def school_admin_dashboard(request, school_id):
    # Get the school using the ID from the URL
    try:
        school = School.objects.get(id=school_id)
    except School.DoesNotExist:
        return HttpResponse("School not found", status=404)

    # Optional: Ensure this admin belongs to this school
    if request.user.school.id != school.id:
        return HttpResponse("Unauthorized", status=403)

    # Aggregate counts for dashboard
    student_count = Student.objects.filter(school=school).count()
    classes = SchoolClass.objects.filter(school=school)
    class_count = classes.count()
    teacher_count = Teacher.objects.filter(school=school).count()
    result_count = Score.objects.filter(school=school).count()
    cbt_count = CBTExam.objects.filter(school=school).count()
    lesson_count = LessonNote.objects.filter(school=school).count()
    assignment_count = Assignment.objects.filter(school=school).count()
    attendance_count = Attendance.objects.filter(school=school).count()
    classes = SchoolClass.objects.filter(school=school).prefetch_related('students')
    class_subject_teacher_count = ClassSubjectTeacher.objects.filter(school_class__school=school).count()
    class_score_settings = ClassScoreSetting.objects.filter(school_class__school=school).select_related('school_class')


    context = {
        'school': school,
        'user_role': 'School Admin',
        'student_count': student_count,
        'teacher_count': teacher_count,
        'result_count': result_count,
        'cbt_count': cbt_count,
        'lesson_count': lesson_count,
        'assignment_count': assignment_count,
        'attendance_count': attendance_count,
        "classes": classes,
        'class_score_settings': class_score_settings,
        "class_count": class_count,
        "class_subject_teacher_count": class_subject_teacher_count
    }

    return render(request, 'school_admin/school_admin_dashboard.html', context)







from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction

from  students.models import Student
from .forms import StudentCreateForm, StudentUpdateForm



# LIST STUDENTS
@login_required
@user_passes_test(is_schooladmin or is_superadmin)
def student_list(request, school_id):

    # Base queryset
    students = Student.objects.filter(
        school_id=school_id
    ).select_related("user", "school_class")

    # --- FILTER BY CLASS ---
    class_id = request.GET.get("class_id")
    if class_id:
        students = students.filter(school_class_id=class_id)

    # Get school
    school = request.user.school_admin_profile.school

    # Get all classes in this school for dropdown
    classes = SchoolClass.objects.filter(school_id=school_id)

    return render(request, "school_admin/super_admin_student_list.html", {
        "students": students,
        "school": school,
        "classes": classes,
        "selected_class": class_id,
    })

from results.utils import generate_unique_username
from django.contrib.auth import get_user_model

User = get_user_model()  # ✅ Use the active user model

#from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import User
from .forms import StudentCreateForm  # 👈 separate forms like you did for accountant


@login_required
@user_passes_test(lambda u: is_schooladmin(u) or is_superadmin(u))
@transaction.atomic
def student_create(request, school_id):
    school = get_object_or_404(School, id=school_id)

    if request.method == "POST":
        form = StudentCreateForm(request.POST, request.FILES, school=school)
        if form.is_valid():
            student = form.save()  # ✅ User is created automatically
            messages.success(request, f"Student '{student.user.get_full_name()}' created successfully")
            return redirect("school_admin:admin_student_list", school_id=school.id)
        else:
            messages.error(request, f"Error creating student: {form.errors}")
    else:
        form = StudentCreateForm(school=school)

    return render(request, "school_admin/admin_student_form.html", {
        "form": form,
        "school": school,       
    })



# ------------------- EDIT STUDENT -------------------
@login_required
@user_passes_test(lambda u: is_schooladmin(u) or is_superadmin(u))
def student_edit(request, school_id, student_id):
    # Get the school from the logged-in admin profile
    school = request.user.school_admin_profile.school
    student = get_object_or_404(Student, id=student_id, school=school)

    if request.method == "POST":
        form = StudentUpdateForm(request.POST, request.FILES, instance=student, school=school)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student '{student.user.get_full_name()}' updated successfully.")
            return redirect("school_admin:admin_student_list", school_id=school.id)
    else:
        form = StudentUpdateForm(instance=student, school=school)

    return render(request, "school_admin/admin_student_form.html", {
        "form": form,
        "student": student,
        "school": school
    })

# DELETE STUDENT
@login_required
@user_passes_test(is_schooladmin or is_superadmin)
def student_delete(request, school_id, student_id):
    school = request.user.school_admin_profile.school
    student = get_object_or_404(Student, id=student_id, school=school)

    if request.method == "POST":
        # Delete user also
        student.user.delete()
        student.delete()
        return redirect("school_admin:admin_student_list", school_id=school.id)

    return render(request, "students/admin/student_confirm_delete.html", {
        "student": student,
        "school": school
    })


#CBT


from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from cbt.models import CBTExam, CBTQuestion, CBTSubmission, Subject
from .forms import CBTExamForm, CBTQuestionForm
from accounts.decorators import school_admin_or_superadmin_required, get_user_school

# Dashboard: list exams for a school (school_id passed)
@school_admin_or_superadmin_required
def admin_dashboard(request, school_id=None):
    user_school = get_user_school(request)
    if getattr(request.user, "is_superadmin", False):
        # superadmin can pass school_id or see all exams
        if school_id:
            exams = CBTExam.objects.filter(school_id=school_id).order_by('-start_time')
            school = get_object_or_404(School, id=school_id)
        else:
            exams = CBTExam.objects.all().order_by('-start_time')
            school = None
    else:
        # school admin
        school = user_school
        exams = CBTExam.objects.filter(school=school).order_by('-start_time')

    context = {'exams': exams, 'school': school}
    return render(request, 'school_admin/admin_question_dashboard.html', context)


# Create exam
@school_admin_or_superadmin_required
def exam_create(request, school_id):
    school = get_object_or_404(School, id=school_id)
    if not getattr(request.user, "is_superadmin", False) and request.user.school_admin_profile.school_id != school.id:
        raise PermissionDenied

    if request.method == 'POST':
        form = CBTExamForm(request.POST, user=request.user)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.school = school
            # optionally assign created_by if teacher
            exam.created_by = getattr(request.user, 'teacher_profile', None)
            exam.save()
            messages.success(request, "Exam created.")
            return redirect('school_admin:admin_dashboard', school_id=school.id)
    else:
        form = CBTExamForm(user=request.user)
    return render (request, 'school_admin/exam_create.html', {'form': form, 'school': school})


# Edit exam
@school_admin_or_superadmin_required
def exam_edit(request, school_id, exam_id):
    school = get_object_or_404(School, id=school_id)
    exam = get_object_or_404(CBTExam, id=exam_id, school=school)
    if request.method == 'POST':
        form = CBTExamForm(request.POST, instance=exam, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam updated.")
            return redirect('cbt:admin_dashboard', school_id=school.id)
    else:
        form = CBTExamForm(instance=exam, user=request.user)
    return render(request, 'cbt/admin/exam_form.html', {'form': form, 'exam': exam, 'school': school})



# Delete exam
@school_admin_or_superadmin_required
def exam_delete(request, school_id, exam_id):
    school = get_object_or_404(School, id=school_id)
    exam = get_object_or_404(CBTExam, id=exam_id, school=school)
    if request.method == 'POST':
        exam.delete()
        messages.success(request, "Exam deleted.")
        return redirect('cbt:admin_dashboard', school_id=school.id)
    return render(request, 'cbt/admin/exam_confirm_delete.html', {'exam': exam, 'school': school})


# Manage Questions list + add question
@school_admin_or_superadmin_required
def manage_questions(request, school_id, exam_id):
    school = get_object_or_404(School, id=school_id)
    exam = get_object_or_404(CBTExam, id=exam_id, school=school)
    questions = exam.questions.all().order_by('id')
    return render(request, 'cbt/admin/questions_list.html', {'exam': exam, 'questions': questions, 'school': school})


@school_admin_or_superadmin_required
def question_create(request, school_id, exam_id):
    school = get_object_or_404(School, id=school_id)
    exam = get_object_or_404(CBTExam, id=exam_id, school=school)
    if request.method == 'POST':
        form = CBTQuestionForm(request.POST)
        if form.is_valid():
            q = form.save(commit=False)
            q.exam = exam
            q.save()
            messages.success(request, "Question added.")
            return redirect('cbt:manage_questions', school_id=school.id, exam_id=exam.id)
    else:
        form = CBTQuestionForm()
    return render(request, 'cbt/admin/question_form.html', {'form': form, 'exam': exam, 'school': school})


@school_admin_or_superadmin_required
def question_edit(request, school_id, exam_id, question_id):
    school = get_object_or_404(School, id=school_id)
    exam = get_object_or_404(CBTExam, id=exam_id, school=school)
    q = get_object_or_404(CBTQuestion, id=question_id, exam=exam)
    if request.method == 'POST':
        form = CBTQuestionForm(request.POST, instance=q)
        if form.is_valid():
            form.save()
            messages.success(request, "Question updated.")
            return redirect('cbt:manage_questions', school_id=school.id, exam_id=exam.id)
    else:
        form = CBTQuestionForm(instance=q)
    return render(request, 'school_admin/exam_create.html', {'form': form, 'exam': exam, 'question': q, 'school': school})


@school_admin_or_superadmin_required
def question_delete(request, school_id, exam_id, question_id):
    school = get_object_or_404(School, id=school_id)
    exam = get_object_or_404(CBTExam, id=exam_id, school=school)
    q = get_object_or_404(CBTQuestion, id=question_id, exam=exam)
    if request.method == 'POST':
        q.delete()
        messages.success(request, "Question deleted.")
        return redirect('school_admin:manage_questions', school_id=school.id, exam_id=exam.id)
    return render(request, 'school_admin/exam_delete.html', {'question': q, 'exam': exam, 'school': school})


# Toggle publish
@school_admin_or_superadmin_required
def exam_toggle_active(request, school_id, exam_id):
    school = get_object_or_404(School, id=school_id)
    exam = get_object_or_404(CBTExam, id=exam_id, school=school)
    exam.active = not exam.active
    exam.save()
    messages.success(request, f"Exam {'published' if exam.active else 'unpublished'}.")
    return redirect('cbt:admin_dashboard', school_id=school.id)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.urls import reverse
from cbt.models import CBTExam, CBTQuestion, CBTSubmission
from django.contrib import messages
import math

@login_required
def start_exam(request, exam_id):
    exam = get_object_or_404(CBTExam, id=exam_id)
    # check eligible (student's class, active)
    student = getattr(request.user, 'student_profile', None)
    if not student:
        messages.error(request, "Only students can take exams.")
        return redirect('accounts:portal_selection')

    if exam.school_id != student.school_id:
        messages.error(request, "You are not allowed to take this exam.")
        return redirect('accounts:portal_selection')

    if not exam.is_active():
        messages.error(request, "This exam is not active.")
        return redirect('students:student_dashboard')

    # create or resume submission
    submission, created = CBTSubmission.objects.get_or_create(student=student, exam=exam, defaults={
        'started_on': timezone.now(),
        'total_questions': exam.questions.count()
    })

    # calculate page = 1
    return redirect('cbt:exam_page', exam_id=exam.id, page=1)


@login_required
def exam_question_page(request, exam_id, page):
    exam = get_object_or_404(CBTExam, id=exam_id)
    student = getattr(request.user, 'student_profile', None)
    if not student or exam.school_id != student.school_id:
        messages.error(request, "You can't take this exam.")
        return redirect('accounts:portal_selection')

    # get questions and pagination
    questions = list(exam.questions.all())
    total = len(questions)
    if total == 0:
        messages.error(request, "No questions for this exam.")
        return redirect('students:student_dashboard')

    page = int(page)
    if page < 1 or page > total:
        return redirect('cbt:exam_page', exam_id=exam.id, page=1)

    q = questions[page-1]
    shuffled_options = q.get_shuffled_options()



    # handle saving answer if POST
    if request.method == 'POST':
        selected = request.POST.get('answer')  # e.g., 'A'
        submission = CBTSubmission.objects.get(student=student, exam=exam)
        raw = submission.raw_answers or {}
        raw[str(q.id)] = selected or ''
        submission.raw_answers = raw
        submission.save()
        # navigate to next or submit
        if request.POST.get('action') == 'next':
            if page < total:
                return redirect('cbt:exam_page', exam_id=exam.id, page=page+1)
        elif request.POST.get('action') == 'prev':
            if page > 1:
                return redirect('cbt:exam_page', exam_id=exam.id, page=page-1)
        elif request.POST.get('action') == 'submit':
            return redirect('cbt:submit_exam', exam_id=exam.id)

    # Remaining time calculation: use started_on + duration
    submission = CBTSubmission.objects.get(student=student, exam=exam)
    elapsed = (timezone.now() - submission.started_on).total_seconds()
    remaining = max(0, exam.duration_minutes*60 - elapsed)

    context = {
        'exam': exam,
        'question': q,
        'page': page,
        'total': total,
        'shuffled_options': shuffled_options,  # dict new_label -> text
        'remaining_seconds': int(remaining),
        'submission': submission,
    }
    return render(request, 'cbt/student/question_page.html', context)


@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(CBTExam, id=exam_id)
    student = getattr(request.user, 'student_profile', None)
    if not student:
        messages.error(request, "Only students may submit exams.")
        return redirect('accounts:portal_selection')

    submission = get_object_or_404(CBTSubmission, exam=exam, student=student)

    # compute results
    questions = list(exam.questions.all())
    raw = submission.raw_answers or {}
    total_q = len(questions)
    correct = 0
    wrong = 0
    for q in questions:
        ans = raw.get(str(q.id), '')
        if ans == q.correct_option:
            correct += 1
        elif ans == '':
            # attempted? treat empty as wrong or not attempted per your policy
            pass
        else:
            wrong += 1

    submission.completed_on = timezone.now()
    submission.total_questions = total_q
    submission.correct_answers = correct
    submission.wrong_answers = wrong
    submission.score = sum([q.marks for q in questions if raw.get(str(q.id), '') == q.correct_option])
    submission.percentage = (submission.score / (sum(q.marks for q in questions) or 1)) * 100
    submission.status = 'Passed' if submission.percentage >= 50 else 'Failed'
    submission.save()

    messages.success(request, "Exam submitted. See result.")
    return redirect('cbt:view_result', exam_id=exam.id)


@login_required
def view_result(request, exam_id):
    exam = get_object_or_404(CBTExam, id=exam_id)
    student = getattr(request.user, 'student_profile', None)
    if not student:
        messages.error(request, "Only students may view results here.")
        return redirect('accounts:portal_selection')

    submission = get_object_or_404(CBTSubmission, exam=exam, student=student)
    questions = exam.questions.all()
    # build detailed view
    details = []
    for q in questions:
        ans = submission.raw_answers.get(str(q.id), '') if submission.raw_answers else ''
        details.append({
            'question': q,
            'selected': ans,
            'correct': q.correct_option,
            'is_correct': ans == q.correct_option
        })

    return render(request, 'cbt/student/result.html', {
        'exam': exam,
        'submission': submission,
        'details': details
    })



from django.db.models import Avg  # Add this at the top of your views.py

@school_admin_or_superadmin_required
def submissions_list(request, school_id, exam_id):
    school = get_object_or_404(School, id=school_id)
    exam = get_object_or_404(CBTExam, id=exam_id, school=school)
    subs = CBTSubmission.objects.filter(exam=exam).select_related('student__user')
    # summary
    total_attempts = subs.count()
    avg_percentage = subs.aggregate(Avg('percentage'))['percentage__avg'] or 0
    pass_count = subs.filter(status='Passed').count()
    fail_count = total_attempts - pass_count
    context = {
        'exam': exam,
        'submissions': subs,
        'total_attempts': total_attempts,
        'avg_percentage': avg_percentage,
        'pass_count': pass_count,
        'fail_count': fail_count,
    }
    return render(request, 'school_admin/admin_exam_submission_list.html', context)




# cbt/views.py
from django.forms import modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from cbt.models import CBTExam, CBTQuestion
from .forms import CBTQuestionForm
from django.contrib.auth.decorators import login_required, user_passes_test

def is_admin(user):
    return user.is_superadmin or hasattr(user, 'school')

@login_required
@user_passes_test(is_admin)
def bulk_question_admin(request, school_id, exam_id):
    school = get_object_or_404(School, id=school_id)
    exam = get_object_or_404(CBTExam, id=exam_id, school=school)

    if not (request.user.is_superadmin or request.user.school == school):
        raise PermissionDenied("You are not allowed to manage this school's exams.")

    CBTQuestionFormSet = modelformset_factory(
        CBTQuestion,
        form=CBTQuestionForm,
        extra=50,
        max_num=50,
        can_delete=True
    )

    if request.method == "POST":
        formset = CBTQuestionFormSet(
            request.POST,
            queryset=CBTQuestion.objects.none()
        )

        if formset.is_valid():

            # Handle deleted forms (IMPORTANT: modelformset uses deleted_forms)
            for form in formset.deleted_forms:
                if form.instance.pk:  # Only delete existing DB records
                    form.instance.delete()

            # Save all new valid (non-empty) questions
            questions = formset.save(commit=False)

            for q in questions:
                # Skip fully empty forms
                if not q.text:
                    continue

                q.exam = exam
                q.save()

            messages.success(request, "Questions added successfully!")
            return redirect(
                "school_admin:preview_questions",
                school_id=school.id,
                exam_id=exam.id
            )

    else:
        formset = CBTQuestionFormSet(queryset=CBTQuestion.objects.none())

    return render(
        request,
        "school_admin/admin_bulk_questions.html",
        {"school": school, "exam": exam, "formset": formset}
    )





def preview_questions(request, school_id, exam_id):
    school = get_object_or_404(School, id=school_id)
    exam = get_object_or_404(CBTExam, id=exam_id, school=school)

    questions = CBTQuestion.objects.filter(exam=exam)

    return render(request, "school_admin/admin_preview_questions.html", {
        "school": school,
        "exam": exam,
        "questions": questions,
    })




from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from cbt.models import CBTExam, CBTQuestion

@login_required
def exam_preview(request, school_id, exam_id):
    """
    Allows the school admin to preview an exam exactly as students will see it,
    but without shuffling and without answer submission.
    """
    # Confirm exam belongs to this school
    exam = get_object_or_404(CBTExam, id=exam_id, school_id=school_id)

    # Load questions in defined order
    questions = CBTQuestion.objects.filter(exam=exam).order_by("id")

    context = {
        "school_id": school_id,
        "exam": exam,
        "questions": questions,
    }
    return render(request, "school_admin/exam_preview.html", context)


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from cbt.models import CBTExam, CBTQuestion

@login_required
def question_list(request, school_id, exam_id):
    """
    List all questions for an exam for school admins.
    """
    exam = get_object_or_404(CBTExam, id=exam_id, school_id=school_id)
    questions = CBTQuestion.objects.filter(exam=exam).order_by("id")

    context = {
        "school_id": school_id,
        "exam": exam,
        "questions": questions,
    }
    return render(request, "school_admin/question_list.html", context)


@login_required
def activate_exam(request, school_id, exam_id):
    school = get_object_or_404(School, id=school_id)

    # permission: super admin OR school admin owning this school
    if not (request.user.is_superadmin or request.user.school_id == school_id):
        raise PermissionDenied()

    exam = get_object_or_404(CBTExam, id=exam_id, school=school)

    exam.active = True
    exam.save()

    messages.success(request, f"{exam.title} has been activated.")
    return redirect("school_admin:admin_dashboard", school_id=school.id)

@login_required
def deactivate_exam(request, school_id, exam_id):
    school = get_object_or_404(School, id=school_id)

    if not (request.user.is_superadmin or request.user.school_id == school_id):
        raise PermissionDenied()

    exam = get_object_or_404(CBTExam, id=exam_id, school=school)

    exam.active = False
    exam.save()

    messages.info(request, f"{exam.title} has been deactivated.")
    return redirect("school_admin:admin_dashboard", school_id=school.id)

@login_required
def delete_exam(request, school_id, exam_id):
    school = get_object_or_404(School, id=school_id)

    if not (request.user.is_superadmin or request.user.school_id == school_id):
        raise PermissionDenied()

    exam = get_object_or_404(CBTExam, id=exam_id, school=school)

    if request.method == "POST":
        exam.delete()
        messages.success(request, "Exam deleted successfully.")
        return redirect("school_admin:admin_dashboard", school_id=school.id)

    return render(request, "cbt/admin/exam_confirm_delete.html", {"school": school, "exam": exam})



@login_required
def submission_detail(request, school_id, exam_id, submission_id):
    """
    Display a detailed view of a student's CBT submission.
    Supports shuffled option reconstruction.
    """

    school = get_object_or_404(School, id=school_id)

    exam = get_object_or_404(
        CBTExam.objects.select_related("school"),
        id=exam_id,
        school=school
    )

    submission = get_object_or_404(
        CBTSubmission.objects.select_related("student__school", "exam"),
        id=submission_id,
        exam=exam
    )

    # ------------ PERMISSION CHECK -------------
    if not (
        request.user.is_superadmin or
        getattr(request.user, "school", None) == school
    ):
        raise PermissionDenied("You do not have permission to view this submission.")
    # -------------------------------------------

    answers = submission.raw_answers or {}   # stored answers
    questions = exam.questions.all().order_by("id")

    # =====================================================================
    # 🔥 RECONSTRUCT REAL CORRECT ANSWER BASED ON SHUFFLED OPTION ORDER
    # =====================================================================
    correct_map = {}   # {question.id: "A"|"B"|"C"|"D"}

    for q in questions:

        # ——— Original correct answer (letter and text) ———
        original_options = {
            "A": q.option_a,
            "B": q.option_b,
            "C": q.option_c,
            "D": q.option_d,
        }

        orig_letter = q.correct_option
        orig_text = original_options.get(orig_letter, "").strip().lower()

        # ——— Get the shuffled list stored during submission ———
        shuffled_list = answers.get(f"_shuffle_text_{q.id}", [])

        # If not shuffled, use default
        if not shuffled_list:
            correct_map[q.id] = orig_letter
            continue

        # Normalize shuffled for matching
        normalized_shuffled = [opt.strip().lower() for opt in shuffled_list]

        # ——— Find correct option inside shuffled list ———
        try:
            idx = normalized_shuffled.index(orig_text)   # position in shuffled
            new_letter = chr(65 + idx)  # convert 0 → A, 1 → B, …
        except ValueError:
            # Correct text not found after shuffle (rare, but safe fallback)
            new_letter = orig_letter

        correct_map[q.id] = new_letter

    # ——— CONTEXT ———
    context = {
        "school": school,
        "exam": exam,
        "submission": submission,
        "answers": answers,
        "questions": questions,
        "correct_map": correct_map,
    }

    return render(request, "school_admin/submission_detail.html", context)



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from students.models import Student
from results.models import Score, Subject, Psychomotor, Affective, ResultComment
from accounts.models import School



@login_required
@user_passes_test(lambda u: u.is_superadmin or hasattr(u, 'school'))
def result_dashboard(request, school_id):
    """
    School admin dashboard to view all student results:
    Scores, Psychomotor, Affective, and Result Comments.
    """
    school = get_object_or_404(School, id=school_id)

    # Permission check
    if not (request.user.is_superadmin or getattr(request.user, 'school', None) == school):
        return redirect('accounts:portal_selection')

    # Fetch students in the school
    students = Student.objects.filter(school=school)

    # Aggregate all related data in one dictionary for clarity
    data = {
        'school': school,
        'students': students,
        'scores': Score.objects.filter(student__in=students).select_related('subject', 'student'),
        'psychomotors': Psychomotor.objects.filter(student__in=students),
        'affectives': Affective.objects.filter(student__in=students),
        'result_comments': ResultComment.objects.filter(student__in=students),
    }

    return render(request, 'school_admin/results/result_dashboard.html', data)



# -----------------------------
# Helper
# -----------------------------
def is_school_admin(user):
    return getattr(user, 'is_admin', False) or getattr(user, 'is_superadmin', False)

# -----------------------------
# SCORE LIST
# -----------------------------
@login_required
def score_list(request, school_id):
    school = get_object_or_404(School, id=school_id)
    scores = Score.objects.filter(school=school).select_related('student', 'subject')
    return render(request, 'school_admin/results/score_list.html', {'scores': scores, 'school': school})

# -----------------------------
# CREATE/EDIT SCORE
# -----------------------------
@login_required
def score_create_edit(request, school_id, score_id=None):
    school = get_object_or_404(School, id=school_id)
    score = get_object_or_404(Score, id=score_id) if score_id else None
    students = Student.objects.filter(school=school)
    subjects = Subject.objects.filter(school=school)
    current_session = "2025/2026"  # Or fetch from system settings

    if request.method == "POST":
        student_id = request.POST.get("student_id")
        subject_id = request.POST.get("subject_id")
        ca = float(request.POST.get("ca") or 0)
        exam = float(request.POST.get("exam") or 0)
        session = request.POST.get("session")
        term = request.POST.get("term")
        student = get_object_or_404(Student, id=student_id)
        subject = get_object_or_404(Subject, id=subject_id)

        if score:
            score.student = student
            score.subject = subject
            score.ca = ca
            score.exam = exam
            score.session = session
            score.term = term
            score.save()
        else:
            Score.objects.create(
                student=student,
                subject=subject,
                ca=ca,
                exam=exam,
                session=session,
                term=term,
                school=school
            )
        return redirect('school_admin:score_list', school_id=school.id)

    return render(request, 'school_admin/results/score_edit.html', {
        'score': score,
        'students': students,
        'subjects': subjects,
        'school': school,
        'current_session': current_session
    })

# -----------------------------
# DELETE SCORE
# -----------------------------
@login_required
def score_delete(request, score_id):
    score = get_object_or_404(Score, id=score_id)
    school_id = score.school.id
    score.delete()
    return redirect('school_admin:score_list', school_id=school_id)


@login_required
def psychomotor_list(request, school_id):
    school = get_object_or_404(School, id=school_id)
    records = Psychomotor.objects.filter(school=school).select_related('student')
    return render(request, 'school_admin/results/psychomotor_list.html', {'records': records, 'school': school})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from students.models import Student
from accounts.models import School
from results.models import Psychomotor, Affective

# ---------------------------
# Generic create/edit helper
# ---------------------------
def create_edit_domain(request, school_id, model_class, template_name, fields, record_id=None):
    school = get_object_or_404(School, id=school_id)
    record = get_object_or_404(model_class, id=record_id) if record_id else None
    students = Student.objects.filter(school=school)
    current_session = "2025/2026"  # Or fetch dynamically from system settings

    if request.method == "POST":
        student = get_object_or_404(Student, id=request.POST.get("student_id"))
        term = request.POST.get("term")
        session = request.POST.get("session")
        data = {k: int(request.POST.get(k) or 0) for k in fields}

        if record:
            for k, v in data.items():
                setattr(record, k, v)
            record.student = student
            record.term = term
            record.session = session
            record.save()
        else:
            model_class.objects.create(student=student, school=school, term=term, session=session, **data)

        # Redirect based on model type
        if model_class == Psychomotor:
            return redirect('school_admin:psychomotor_list', school_id=school.id)
        elif model_class == Affective:
            return redirect('school_admin:affective_list', school_id=school.id)

    return render(request, template_name, {
        'record': record,
        'students': students,
        'school': school,
        'current_session': current_session,
        'fields': fields
    })


# ---------------------------
# Specific views using helper
# ---------------------------
@login_required
def psychomotor_create_edit(request, school_id, record_id=None):
    fields = ['neatness','agility','creativity','sports','handwriting']
    return create_edit_domain(
        request, school_id,
        model_class=Psychomotor,
        template_name='school_admin/results/edit_psychomotor.html',
        fields=fields,
        record_id=record_id
    )

@login_required
def affective_create_edit(request, school_id, record_id=None):
    fields = ['punctuality','cooperation','behavior','attentiveness','perseverance']
    return create_edit_domain(
        request, school_id,
        model_class=Affective,
        template_name='school_admin/results/edit_affective.html',
        fields=fields,
        record_id=record_id
    )

@login_required
def psychomotor_delete(request, record_id):
    record = get_object_or_404(Psychomotor, id=record_id)
    school_id = record.school.id
    record.delete()
    return redirect('school_admin:psychomotor_list', school_id=school_id)



@login_required
def affective_list(request, school_id):
    school = get_object_or_404(School, id=school_id)
    records = Affective.objects.filter(school=school).select_related('student')
    return render(request, 'school_admin/results/affective_list.html', {'records': records, 'school': school})


@login_required
def affective_delete(request, record_id):
    record = get_object_or_404(Affective, id=record_id)
    school_id = record.school.id
    record.delete()
    return redirect('school_admin:affective_list', school_id=school_id)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.models import School
from students.models import Student
from results.models import ResultComment

# ---------------------------
# Helper: check school admin
# ---------------------------
def is_school_admin(user):
    return getattr(user, 'is_admin', False) or getattr(user, 'is_superadmin', False)

# ---------------------------
# List Result Comments
# ---------------------------
@login_required
@user_passes_test(is_school_admin)
def result_comment_list(request, school_id):
    school = get_object_or_404(School, id=school_id)
    students = Student.objects.filter(school=school)
    comments = ResultComment.objects.filter(student__in=students)
    return render(request, 'school_admin/results/result_comment_list.html', {
        'school': school,
        'result_comments': comments,
    })

# ---------------------------
# Create / Edit Result Comment
# ---------------------------
@login_required
def result_comment_create_edit(request, school_id, comment_id=None):
    school = get_object_or_404(School, id=school_id)
    comment = get_object_or_404(ResultComment, id=comment_id) if comment_id else None
    students = Student.objects.filter(school=school)

    if request.method == "POST":
        student = get_object_or_404(Student, id=request.POST.get("student_id"))
        text = request.POST.get("comment", "").strip()

        if comment:
            comment.student = student
            comment.comment = text
            comment.save()
        else:
            ResultComment.objects.create(student=student, school=school, comment=text)

        return redirect('school_admin:result_comment_list', school_id=school.id)

    return render(request, 'school_admin/results/edit_result_comment.html', {
        'comment': comment,
        'students': students,
        'school': school
    })

# ---------------------------
# Delete Result Comment
# ---------------------------
@login_required
def result_comment_delete(request, comment_id):
    comment = get_object_or_404(ResultComment, id=comment_id)
    school_id = comment.school.id
    comment.delete()
    return redirect('school_admin:result_comment_list', school_id=school_id)



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from notes.models import LessonNote, NoteCategory, SchoolClass, LessonNoteSubmission
from .forms import LessonNoteForm
from accounts.models import School

# ---------------------------
# School admin: List notes
# ---------------------------
@login_required
@user_passes_test(lambda u: u.is_superadmin or hasattr(u, 'school'))
def lessonnote_list(request):
    school = getattr(request.user, 'school', None) if not request.user.is_superadmin else None
    notes = LessonNote.objects.all() if request.user.is_superadmin else LessonNote.objects.filter(school=school)
    return render(request, 'school_admin/notes/lessonnote_list.html', {'notes': notes})

# ---------------------------
# Create/Edit note
# ---------------------------
@login_required
@user_passes_test(lambda u: u.is_superadmin or hasattr(u, 'school'))
def lessonnote_create_edit(request, pk=None):
    if pk:
        note = get_object_or_404(LessonNote, pk=pk)
    else:
        note = None

    if request.method == 'POST':
        form = LessonNoteForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            obj = form.save(commit=False)
            if not obj.school_id:
                obj.school = getattr(request.user, 'school', None)
            obj.save()
            form.save_m2m()
            return redirect('school_admin:lessonnote_list')
    else:
        form = LessonNoteForm(instance=note)

    return render(request, 'school_admin/notes/lessonnote_form.html', {'form': form, 'note': note})

# ---------------------------
# Delete note
# ---------------------------
@login_required
@user_passes_test(lambda u: u.is_superadmin or hasattr(u, 'school'))
def lessonnote_delete(request, pk):
    note = get_object_or_404(LessonNote, pk=pk)
    if request.method == 'POST':
        note.delete()
        return redirect('school_admin:lessonnote_list')
    return render(request, 'school_admin/notes/lessonnote_delete_confirm.html', {'note': note})




@login_required
def lesson_dashboard(request, school_id):
    """
    School admin dashboard for lesson notes:
    - Shows all notes for the given school
    - Maps submissions per note for template display
    """

    user = request.user
    school = get_object_or_404(School, id=school_id)

    # Permission check: only superadmin or school admin
    if not (user.is_superadmin or getattr(user, 'school', None) == school):
        raise Http404("Not allowed")

    # Fetch all lesson notes for this school
    notes = LessonNote.objects.filter(school=school).order_by('-publish_date')

    # Fetch all submissions related to these notes
    submissions = LessonNoteSubmission.objects.filter(
        note__in=notes
    ).select_related('note', 'student', 'graded_by')

    # Map submissions by note ID for easy template lookup
    subs_map = {}
    for sub in submissions:
        subs_map.setdefault(sub.note_id, []).append(sub)

    context = {
        'school': school,
        'notes': notes,
        'subs_map': subs_map,
    }

    return render(request, 'school_admin/notes/lessonnote_dashboard.html', context)



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404
from assignments.models import Assignment, AssignmentSubmission
from assignments.forms import AssignmentForm
from accounts.models import School

# ------------------------
# List assignments for a school
# ------------------------
@login_required
def assignment_list(request, school_id):
    school = get_object_or_404(School, id=school_id)
    user = request.user

    # Only superadmin or school admin
    if not (user.is_superadmin or getattr(user, 'school', None) == school):
        raise Http404("Not allowed")

    assignments = Assignment.objects.filter(school=school).order_by('-created_on')
    return render(request, 'school_admin/assignments/assignment_list.html', {
        'school': school,
        'assignments': assignments
    })

# ------------------------
# Create or edit assignment
# ------------------------
@login_required
def assignment_create_edit(request, school_id, pk=None):
    school = get_object_or_404(School, id=school_id)
    user = request.user
    if not (user.is_superadmin or getattr(user, 'school', None) == school):
        raise Http404("Not allowed")

    assignment = get_object_or_404(Assignment, pk=pk, school=school) if pk else None

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.school = school
            obj.save()
            form.save_m2m()
            return redirect('school_admin:assignment_list', school_id=school.id)
    else:
        form = AssignmentForm(instance=assignment)

    return render(request, 'school_admin/assignments/assignment_form.html', {
        'form': form,
        'school': school,
        'assignment': assignment
    })

# ------------------------
# Delete assignment
# ------------------------
@login_required
def assignment_delete(request, school_id, pk):
    school = get_object_or_404(School, id=school_id)
    assignment = get_object_or_404(Assignment, pk=pk, school=school)

    if request.method == 'POST':
        assignment.delete()
        return redirect('school_admin:assignment_list', school_id=school.id)

    return render(request, 'school_admin/assignments/assignment_delete_confirm.html', {
        'assignment': assignment,
        'school': school
    })

# ------------------------
# View submissions for a given assignment
# ------------------------
@login_required
def assignment_submissions(request, school_id, pk):
    school = get_object_or_404(School, id=school_id)
    assignment = get_object_or_404(Assignment, pk=pk, school=school)
    submissions = AssignmentSubmission.objects.filter(assignment=assignment).select_related('student', 'graded_by')

    return render(request, 'school_admin/assignments/assignment_submissions.html', {
        'school': school,
        'assignment': assignment,
        'submissions': submissions
    })


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from accounts.models import School
from assignments.models import Assignment, AssignmentSubmission

@login_required
def assignment_dashboard(request, school_id):
    user = request.user
    school = get_object_or_404(School, id=school_id)

    # Permission check: superadmin or school admin
    if not (user.is_superadmin or getattr(user, 'school', None) == school):
        raise Http404("Not allowed")

    # Fetch all assignments for this school
    assignments = Assignment.objects.filter(school=school).order_by('-created_on')

    # Fetch all submissions
    submissions = AssignmentSubmission.objects.filter(assignment__in=assignments).select_related('student', 'graded_by', 'assignment')

    # Map submissions by assignment ID for easy lookup
    sub_map = {}
    for sub in submissions:
        sub_map.setdefault(sub.assignment_id, []).append(sub)

    context = {
        'school': school,
        'assignments': assignments,
        'sub_map': sub_map,
    }

    return render(request, 'school_admin/assignments/assignment_dashboard.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Count
from django.utils.dateparse import parse_date

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Count
from django.utils.dateparse import parse_date

from accounts.models import School
from students.models import Student, SchoolClass
from attendance.models import Attendance
from django.db.models import Count
from django.http import JsonResponse

# -------------------------
# Correct permission check
# -------------------------
def school_admin_required(user):
    return hasattr(user, "is_schooladmin") and user.is_schooladmin


@login_required
def attendance_list(request, school_id):
    # --------------------------------
    # Permission Check (FIXED)
    # --------------------------------
    if not school_admin_required(request.user):
        raise PermissionDenied

    school = get_object_or_404(School, id=school_id)

    # --------------------------------
    # Filters
    # --------------------------------
    selected_class = request.GET.get("class") or ""
    selected_student = request.GET.get("student") or ""
    selected_status = request.GET.get("status") or ""
    start_date = request.GET.get("start_date") or ""
    end_date = request.GET.get("end_date") or ""

    records = Attendance.objects.filter(school=school).select_related("student")

    # Filter: class
    if selected_class:
        records = records.filter(student__school_class_id=selected_class)

    # Filter: student
    if selected_student:
        records = records.filter(student_id=selected_student)

    # Filter: status
    if selected_status:
        records = records.filter(status=selected_status)

    # Filter: date range
    if start_date:
        records = records.filter(date__gte=parse_date(start_date))

    if end_date:
        records = records.filter(date__lte=parse_date(end_date))

    # --------------------------------
    # Dropdown data
    # --------------------------------
    classes = SchoolClass.objects.filter(school=school)
    students = Student.objects.filter(school=school)

    # --------------------------------
    # Chart Data
    # --------------------------------

    # Daily count
    daily_chart = (
        records.values("date")
        .annotate(total=Count("id"))
        .order_by("date")
    )

    # Status distribution
    status_chart = (
        records.values("status")
        .annotate(total=Count("id"))
    )

    # Class distribution
    class_chart = (
        records.values("student__school_class__name")
        .annotate(total=Count("id"))
    )

    context = {
        "school": school,
        "records": records,
        "classes": classes,
        "students": students,

        # Filter memory
        "selected_class": selected_class,
        "selected_student": selected_student,
        "selected_status": selected_status,
        "start_date": start_date,
        "end_date": end_date,

        # Chart datasets
        "daily_chart": list(daily_chart),
        "status_chart": list(status_chart),
        "class_chart": list(class_chart),
    }

    return render(request, "school_admin/attendance/admin_list.html", context)



# ----------------------------------------
# ADMIN: CREATE ATTENDANCE
# ----------------------------------------

from accounts.models import School
from students.models import Student
from attendance.models import Attendance
from attendance.forms import AttendanceForm


# ---------------------------------------------------------
# Correct Admin Permission Checker
# ---------------------------------------------------------



# ---------------------------------------------------------
# CREATE ATTENDANCE
# ---------------------------------------------------------
@login_required
def attendance_create(request, school_id):
    if not school_admin_required(request.user):
        raise PermissionDenied

    school = get_object_or_404(School, id=school_id)

    if request.method == "POST":
        form = AttendanceForm(request.POST)

        if form.is_valid():
            attendance = form.save(commit=False)

            # ensure record belongs to admin's school
            if attendance.student.school_id != school.id:
                messages.error(request, "This student does not belong to this school.")
                return redirect("school_admin:admin_attendance_list", school_id=school.id)

            attendance.school = school
            attendance.marked_by = None  # admin created, not teacher
            attendance.save()

            messages.success(request, "Attendance created successfully.")
            return redirect("school_admin:admin_attendance_list", school_id=school.id)
    else:
        # limit students to school
        form = AttendanceForm()
        form.fields["student"].queryset = Student.objects.filter(school=school)

    context = {
        "form": form,
        "school": school,
        "is_create": True,
    }

    return render(request, "school_admin/attendance/admin_form.html", context)


# ---------------------------------------------------------
# EDIT ATTENDANCE
# ---------------------------------------------------------
@login_required
def attendance_edit(request, school_id, record_id):
    if not school_admin_required(request.user):
        raise PermissionDenied

    school = get_object_or_404(School, id=school_id)
    record = get_object_or_404(Attendance, id=record_id, school=school)

    if request.method == "POST":
        form = AttendanceForm(request.POST, instance=record)

        if form.is_valid():
            updated_record = form.save(commit=False)

            # again: protect school boundary
            if updated_record.student.school_id != school.id:
                messages.error(request, "Invalid student for this school.")
                return redirect("school_admin:admin_attendance_list", school_id=school.id)

            updated_record.marked_by = record.marked_by  # keep original teacher if any
            updated_record.save()

            messages.success(request, "Attendance updated successfully.")
            return redirect("school_admin:admin_attendance_list", school_id=school.id)
    else:
        form = AttendanceForm(instance=record)
        form.fields["student"].queryset = Student.objects.filter(school=school)

    context = {
        "form": form,
        "school": school,
        "record": record,
        "is_edit": True,
    }

    return render(request, "school_admin/attendance/admin_form.html", context)


# ---------------------------------------------------------
# DELETE ATTENDANCE
# ---------------------------------------------------------
@login_required
def attendance_delete(request, school_id, record_id):
    if not school_admin_required(request.user):
        raise PermissionDenied

    school = get_object_or_404(School, id=school_id)
    record = get_object_or_404(Attendance, id=record_id, school=school)

    if request.method == "POST":
        record.delete()
        messages.success(request, "Attendance deleted successfully.")
        return redirect("school_admin:admin_attendance_list", school_id=school.id)

    return render(request, "school_admin/attendance/admin_confirm_delete.html", {
        "record": record,
        "school": school,
    })



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages

from accounts.models import School, Teacher

from .forms import TeacherForm



def school_admin_required(user):
    return hasattr(user, 'role') and user.role == 'schooladmin'

from django.db.models import Count
from django.http import JsonResponse

@login_required
def teacher_list(request, school_id):
    if not school_admin_required(request.user):
        raise PermissionDenied

    school = get_object_or_404(School, id=school_id)

    # Filters
    selected_class = request.GET.get('class', None)
    selected_subject = request.GET.get('subject', None)

    teachers = Teacher.objects.filter(school=school).prefetch_related('classes', 'subjects')

    if selected_class:
        teachers = teachers.filter(classes__id=selected_class)
    if selected_subject:
        teachers = teachers.filter(subjects__id=selected_subject)

    # Classes for filter dropdown
    classes = SchoolClass.objects.filter(school=school).order_by("name")

    # Subjects for filter dropdown
    subjects = []
    for t in teachers:
        for s in t.subjects.all():
            if s not in subjects:
                subjects.append(s)

    # Chart: Teachers per Class
    class_chart = teachers.values('classes__name').annotate(total=Count('id'))

    # Chart: Teachers per Subject
    subject_chart = teachers.values('subjects__name').annotate(total=Count('id'))

    context = {
        "school": school,
        "teachers": teachers,
        "classes": classes,
        "subjects": subjects,
        "selected_class": selected_class,
        "selected_subject": selected_subject,
        "class_chart": list(class_chart),
        "subject_chart": list(subject_chart),
    }
    return render(request, "school_admin/teachers/admin_list.html", context)


# ------------------- CREATE TEACHER -------------------
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from .forms import TeacherForm



# ------------------- CREATE TEACHER -------------------
@login_required
@user_passes_test(lambda u: is_schooladmin(u) or is_superadmin(u))
@transaction.atomic
def teacher_create(request, school_id):
    school = get_object_or_404(School, id=school_id)

    if request.method == "POST":
        form = TeacherForm(request.POST, request.FILES, school=school)
        if form.is_valid():
            teacher = form.save()  # ✅ User is created inside the form
            messages.success(
                request,
                f"Teacher '{teacher.user.get_full_name()}' created successfully."
            )
            return redirect("school_admin:teacher_list", school_id=school.id)
        else:
            messages.error(request, f"Error creating teacher: {form.errors}")
    else:
        form = TeacherForm(school=school)

    return render(
        request,
        "school_admin/teachers/admin_form.html",
        {
            "form": form,
            "school": school,
        },
    )


# ------------------- EDIT TEACHER -------------------
@login_required
@user_passes_test(lambda u: is_schooladmin(u) or is_superadmin(u))
def teacher_edit(request, school_id, teacher_id):
    school = request.user.school_admin_profile.school
    teacher = get_object_or_404(Teacher, id=teacher_id, school=school)

    if request.method == "POST":
        form = TeacherForm(
            request.POST,
            request.FILES,
            instance=teacher,
            school=school
        )
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Teacher '{teacher.user.get_full_name()}' updated successfully."
            )
            return redirect("school_admin:teacher_list", school_id=school.id)
    else:
        form = TeacherForm(instance=teacher, school=school)

    return render(
        request,
        "school_admin/teachers/admin_form.html",
        {
            "form": form,
            "teacher": teacher,
            "school": school,
        },
    )





# DELETE
@login_required
def teacher_delete(request, school_id, teacher_id):
    if not school_admin_required(request.user):
        raise PermissionDenied
    school = get_object_or_404(School, id=school_id)
    teacher = get_object_or_404(Teacher, id=teacher_id, school=school)

    if request.method == "POST":
        teacher.delete()
        messages.success(request, "Teacher deleted successfully.")
        return redirect("school_admin:teacher_list", school_id=school.id)

    return render(request, "school_admin/teachers/admin_confirm_delete.html", {"teacher": teacher, "school": school})



from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def block_unblock_students(request, school_id):
    school = get_object_or_404(School, id=school_id)

    # Base queryset
    students = Student.objects.filter(school=school).order_by('user__first_name')

    # -----------------------------
    # ADDED FILTERS ONLY (no other logic touched)
    # -----------------------------
    all_classes = SchoolClass.objects.filter(school=school).order_by("name")

    class_filter = request.GET.get("class")
    name_filter = request.GET.get("search")

    if class_filter:
        students = students.filter(school_class_id=class_filter)

    if name_filter:
        students = students.filter(user__first_name__icontains=name_filter) | \
                   students.filter(user__last_name__icontains=name_filter)
    # -----------------------------

    if request.method == "POST":
        action = request.POST.get("action")
        student_id = request.POST.get("student_id")

        if action == "block_all":
            students.update(is_result_blocked=True, block_reason="Access blocked by admin")
            messages.success(request, "All students have been blocked from accessing results.")

        elif action == "unblock_all":
            students.update(is_result_blocked=False, block_reason="")
            messages.success(request, "All students have been unblocked.")

        elif action in ["block", "unblock"] and student_id:
            student = get_object_or_404(Student, id=student_id)
            if action == "block":
                student.is_result_blocked = True
                student.block_reason = "Access blocked by admin"
                student.save()
                messages.success(request, f"{student.user.get_full_name()} is now blocked.")
            else:
                student.is_result_blocked = False
                student.block_reason = ""
                student.save()
                messages.success(request, f"{student.user.get_full_name()} is now unblocked.")

        return redirect("school_admin:block_unblock_students", school_id=school.id)

    context = {
        "school": school,
        "students": students,
        "all_classes": all_classes,         # ADDED
        "selected_class": class_filter,     # ADDED
        "search_value": name_filter,        # ADDED
    }
    return render(request, "school_admin/block_unblock_students.html", context)



from results.models import Score
from django.shortcuts import render, get_object_or_404, redirect
from students.models import Student
from results.models import Score, Psychomotor, Affective, ResultComment
from accounts.models import School
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from .forms import ScoreForm
from results.utils import SESSION_LIST

# ------------------------
# LIST OF CLASSES
# ------------------------
# ------------------------
# CLASS LIST
# ------------------------
@login_required
def admin_class_list(request):
    classes = SchoolClass.objects.all()
    sessions = SESSION_LIST

    selected_session = request.GET.get("session", "")
    selected_term = request.GET.get("term", "")

    context = {
        "classes": classes,
        "sessions": sessions,
        "selected_session": selected_session,
        "selected_term": selected_term,
    }
    return render(request, "school_admin/admin/class_list.html", context)





# ------------------------
# STUDENTS IN A CLASS
# ------------------------
@login_required
def admin_class_students(request, class_id):

    term = request.GET.get("term")
    session = request.GET.get("session")

    school_class = get_object_or_404(SchoolClass, id=class_id)

    # filter students belonging to this class
    students = Student.objects.filter(school_class=school_class)

    # pass selections so template links can include them
    return render(request, "school_admin/admin/class_students.html", {
        "class": school_class,
        "students": students,
        "term": term,
        "session": session,
        "sessions": SESSION_LIST,
    })


# ------------------------
# VIEW STUDENT RESULTS
# ------------------------
import io
import base64
import random
import qrcode
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Sum, F

from django.db.models import Sum, Avg, Count

from django.shortcuts import get_object_or_404, redirect, render
from django.forms import modelformset_factory
from django.db.models import Sum, F
from results.models import grade_from_score_dynamic, ClassSubjectTeacher, ResultComment, ResultVerification
from results.views import _generate_qr_data_uri
from students.models import PromotionHistory
from accounts.models import SystemSetting

@login_required
def admin_student_results(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    school = student.school

    term = request.GET.get("term")
    session = request.GET.get("session")

    if not term or not session:
        latest_score = Score.objects.filter(student=student).order_by("-session").first()
        if latest_score:
            term = term or latest_score.term
            session = session or latest_score.session

    if session not in SESSION_LIST:
        raise ValueError(f"Invalid session supplied: {session}")

    # scores for this student, term, session
    scores_qs = Score.objects.filter(
        student=student, term=term, session=session
    ).select_related("subject")

    # teacher mapping
    cst_qs = ClassSubjectTeacher.objects.filter(
        school_class=student.school_class,
        subject__in=[s.subject for s in scores_qs]
    ).select_related("teacher__user")

    cst_map = {
        cst.subject_id: cst.teacher.user.get_full_name() if cst.teacher else "N/A"
        for cst in cst_qs
    }
    is_ca_enabled = scores_qs.filter(ca__gt=0).exists()  # <-- only True if any CA > 0
    # ---------- Build score list ----------
    scores = []
    overall_total = 0
    

    for s in scores_qs:
        ca = s.ca or 0
        if ca > 0:
            is_ca_enabled = True

        exam = s.exam or 0
        total = ca + exam
        overall_total += total

        scores.append({
            "id": s.id,
            "subject": s.subject.name,
            "ca": ca,
            "exam": exam,
            "total": total,
            "grade": grade_from_score_dynamic(total, school),
            "teacher": cst_map.get(s.subject_id, "N/A"),
        })

    avg = overall_total / len(scores) if scores else 0
    best_subject = max(scores, key=lambda x: x["total"]) if scores else None
    least_subject = min(scores, key=lambda x: x["total"]) if scores else None

    # ---------- Ranking ----------
    class_qs = Score.objects.filter(
        term=term, session=session, student__school_class=student.school_class
    ).values("student").annotate(total=Sum(F("ca") + F("exam")))

    ranking = sorted(class_qs, key=lambda x: x["total"] or 0, reverse=True)
    position = next(
        (i for i, r in enumerate(ranking, start=1) if r["student"] == student.id),
        None
    )
    class_size = len(ranking)

    # ---------- Formset ----------
    ScoreFormSet = modelformset_factory(Score, form=ScoreForm, extra=0)

    if request.method == "POST":
        formset = ScoreFormSet(
            request.POST,
            queryset=scores_qs,
            form_kwargs={"show_ca": is_ca_enabled}     #  ⭐ pass flag here
        )
        if formset.is_valid():
            formset.save()

            # ... unchanged logic ...
            # (rest of your POST logic stays the same)

            return redirect(request.path + f"?term={term}&session={session}")

    else:
        formset = ScoreFormSet(
            queryset=scores_qs,
            form_kwargs={"show_ca": is_ca_enabled}     #  ⭐ GET branch too
        )

    # ---------- other objects ----------
    psychomotor = Psychomotor.objects.filter(
        student=student, term=term, session=session).first()
    affective = Affective.objects.filter(
        student=student, term=term, session=session).first()

    result_comment = ResultComment.objects.filter(
        student=student, term=term, session=session).first()

    context = {
        "student": student,
        "school": school,
        "scores": scores,
        "overall_total": overall_total,
        "avg": avg,
        "position": position,
        "class_size": class_size,
        "best_subject": best_subject,
        "least_subject": least_subject,
        "psychomotor": psychomotor,
        "affective": affective,
        "psychomotor_fields": {
            "neatness": "Neatness",
            "agility": "Agility",
            "creativity": "Creativity",
            "sports": "Sports",
            "handwriting": "Handwriting",
        },
        "affective_fields": {
            "punctuality": "Punctuality",
            "cooperation": "Cooperation",
            "behavior": "Behavior",
            "attentiveness": "Attentiveness",
            "perseverance": "Perseverance",
        },
        "teacher_comment": result_comment.teacher_comment if result_comment else "",
        "principal_comment": result_comment.principal_comment if result_comment else "",
        "selected_term": term,
        "selected_session": session,

        # key for template + form
        "is_ca_enabled": is_ca_enabled,

        "formset": formset,
    }

    return render(request, "school_admin/admin/student_results.html", context)





# ------------------------
# EDIT STUDENT SCORE
# ------------------------
@login_required
def admin_edit_score(request, score_id):
    score = get_object_or_404(Score, id=score_id)

    if request.method == "POST":
        form = ScoreForm(request.POST, instance=score)
        if form.is_valid():
            form.save()
            return redirect("admin-student-results", student_id=score.student.id)
    else:
        form = ScoreForm(instance=score)

    return render(request, "school_admin/admin/edit_score.html", {
        "form": form,
        "score": score
    })





@login_required
def admin_student_cumulative(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    school = student.school

    # Session selection
    selected_session = request.GET.get("session") or (SESSION_LIST[-1] if SESSION_LIST else "")
    if selected_session not in SESSION_LIST:
        selected_session = SESSION_LIST[-1] if SESSION_LIST else selected_session

    TERM_KEYS = ["1", "2", "3"]
    TERM_LABEL = {"1": "First", "2": "Second", "3": "Third"}
    TERM_LABELS = [TERM_LABEL[k] for k in TERM_KEYS]

    # --------------------- POST: SAVE CA/EXAM + COMMENTS ----------------------
    if request.method == "POST":
        # --- Save CA & Exam ---
        score_qs = Score.objects.filter(student=student, session=selected_session)
        for s in score_qs:
            ca_key = f"ca_{s.id}"
            exam_key = f"exam_{s.id}"

            if ca_key in request.POST:
                try:
                    s.ca = float(request.POST.get(ca_key, 0) or 0)
                except (TypeError, ValueError):
                    s.ca = 0

            if exam_key in request.POST:
                try:
                    s.exam = float(request.POST.get(exam_key, 0) or 0)
                except (TypeError, ValueError):
                    s.exam = 0

            s.save()

        # ------------------- FIXED COMMENT-SAVING BLOCK -----------------------
        rc = ResultComment.objects.filter(
            student=student, session=selected_session, term="cum"
        ).first()

        if not rc:
            rc = ResultComment.objects.filter(
                student=student, session=selected_session
            ).exclude(term="cum").order_by("-term").first()

        if not rc:
            rc = ResultComment.objects.create(
                student=student,
                school=student.school,
                session=selected_session,
                term="cum",
                teacher_comment="",
                principal_comment=""
            )

        rc.teacher_comment = request.POST.get("teacher_comment", "")
        rc.principal_comment = request.POST.get("principal_comment", "")
        rc.save()

        return redirect(request.path + f"?session={selected_session}")

    # ------------------- ALL OTHER LOGIC UNTOUCHED --------------------------
    cst_qs = ClassSubjectTeacher.objects.filter(
        school_class=student.school_class
    ).select_related("subject", "teacher__user")
    cst_map = {cst.subject_id: (cst.teacher.user.get_full_name() if cst.teacher else "N/A") for cst in cst_qs}
    class_subjects = [cst.subject for cst in cst_qs]

    score_subjects = Subject.objects.filter(scores__student=student, scores__session=selected_session).distinct()
    subject_set = {s.id: s for s in class_subjects}
    for s in score_subjects:
        subject_set.setdefault(s.id, s)
    subjects_objs = list(subject_set.values())

    subjects = {}
    show_ca = False
    for subj in subjects_objs:
        entry = {"subject": subj.name, "teacher": cst_map.get(subj.id, "N/A")}
        for term_label in TERM_LABELS:
            entry[term_label] = None

        score_qs = Score.objects.filter(student=student, subject=subj, session=selected_session)
        for sc in score_qs:
            label = TERM_LABEL.get(sc.term)
            if not label:
                continue
            ca = sc.ca or 0
            exam = sc.exam or 0
            total = ca + exam
            if ca > 0:
                show_ca = True
            entry[label] = {
                "id": sc.id,
                "ca": ca,
                "exam": exam,
                "total": total,
                "grade": grade_from_score_dynamic(total, school),
                "teacher": sc.teacher.user.get_full_name() if sc.teacher else cst_map.get(subj.id, "N/A"),
            }

        term_totals = [v["total"] for v in [entry[t] for t in TERM_LABELS] if v]
        avg = sum(term_totals)/len(term_totals) if term_totals else 0
        entry["Average"] = avg
        entry["AverageGrade"] = grade_from_score_dynamic(avg, school) if term_totals else "N/A"
        subjects[subj.name] = entry

    subject_avgs = [data["Average"] for data in subjects.values()]
    avg_total = sum(subject_avgs)/len(subject_avgs) if subject_avgs else 0
    overall_avg_grade = grade_from_score_dynamic(avg_total, school) if subject_avgs else "N/A"
    best_subject = max(subjects.items(), key=lambda kv: kv[1]["Average"])[0] if subjects else ""
    weak_subject = min(subjects.items(), key=lambda kv: kv[1]["Average"])[0] if subjects else ""
    overall_total = sum(subject_avgs)

    class_qs = Score.objects.filter(
        student__school_class=student.school_class, session=selected_session
    ).values("student").annotate(total=Sum(F("ca")+F("exam")))
    ranking = sorted(class_qs, key=lambda x: x["total"] or 0, reverse=True)
    position = next((i for i, r in enumerate(ranking, start=1) if r["student"] == student.id), None)
    class_size = len(ranking)

    psychomotor, affective = {}, {}
    for f in ["neatness","agility","creativity","sports","handwriting"]:
        psychomotor[f] = 0
    for f in ["punctuality","cooperation","behavior","attentiveness","perseverance"]:
        affective[f] = 0

    for tkey in TERM_KEYS:
        p = Psychomotor.objects.filter(student=student, session=selected_session, term=tkey).first()
        if p:
            psychomotor = {f: getattr(p,f,0) for f in psychomotor.keys()}
            break

    for tkey in TERM_KEYS:
        a = Affective.objects.filter(student=student, session=selected_session, term=tkey).first()
        if a:
            affective = {f: getattr(a,f,0) for f in affective.keys()}
            break

    rc = ResultComment.objects.filter(student=student, session=selected_session, term="cum").first()
    if not rc:
        rc = ResultComment.objects.filter(student=student, session=selected_session).order_by("-term").first()
    teacher_comment = rc.teacher_comment if rc else ""
    principal_comment = rc.principal_comment if rc else ""

    verification_obj, _ = ResultVerification.objects.get_or_create(student=student)
    base = getattr(settings,"SITE_URL","/")
    verify_url = f"{base}/results/verify/{student.admission_no}/?token={verification_obj.verification_token}"
    qr_data_uri = _generate_qr_data_uri(verify_url, box_size=6) if "_generate_qr_data_uri" in globals() else ""
    principal_signature_url = getattr(school, "principal_signature", None)
    principal_signature_url = principal_signature_url.url if principal_signature_url else None

    # ⭐⭐⭐ ADDED: PROMOTION HISTORY ⭐⭐⭐
    promotion_history = list(
        PromotionHistory.objects.filter(student=student).order_by("-promoted_on")
    )

    context = {
        "student": student,
        "school": school,
        "selected_session": selected_session,
        "available_sessions": SESSION_LIST,
        "terms": TERM_LABELS,
        "subjects": subjects,
        "avg_total": avg_total,
        "overall_avg_grade": overall_avg_grade,
        "overall_total": overall_total,
        "best_subject": best_subject,
        "weak_subject": weak_subject,
        "position": position,
        "class_size": class_size,
        "psychomotor": psychomotor,
        "affective": affective,
        "teacher_comment": teacher_comment,
        "principal_comment": principal_comment,
        "qr_data_uri": qr_data_uri,
        "principal_signature_url": principal_signature_url,
        "show_ca": show_ca,

        # ⭐ ADDED INSIDE CONTEXT ⭐
        "promotion_history": promotion_history,
    }

    return render(request, "school_admin/admin/student_cumulative_edit.html", context)












@login_required
def admin_class_cumulative(request, class_id):
    school_class = get_object_or_404(SchoolClass, id=class_id)
    selected_session = request.GET.get("session", SESSION_LIST[-1])

    students = Student.objects.filter(school_class=school_class)

    context = {
        "class": school_class,
        "students": students,
        "session": selected_session,
    }
    return render(request, "school_admin/admin/class_cumulative.html", context)



@login_required
def promote_students(request, class_id):
    user = request.user
    if not user.is_schooladmin:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect("home")  # or another page

    school = user.school
    current_class = get_object_or_404(SchoolClass, id=class_id, school=school)

    # Use 'school_class' instead of 'current_class'
    students = Student.objects.filter(school_class=current_class)

    if request.method == "POST":
        selected_ids = request.POST.getlist("students")
        new_class_id = request.POST.get("new_class")
        session = request.POST.get("session")

        if not selected_ids:
            messages.error(request, "No students selected.")
            return redirect(request.path)

        new_class = get_object_or_404(SchoolClass, id=new_class_id, school=school)
        selected_students = Student.objects.filter(id__in=selected_ids)

        for student in selected_students:
            PromotionHistory.objects.create(
                student=student,
                session=session,
                old_class=student.school_class,
                new_class=new_class
            )
            student.promoted_from = student.school_class
            student.promoted_to = new_class
            student.school_class = new_class
            student.save()

        messages.success(request, "Selected students successfully promoted.")
        return redirect("school_admin:admin_class_list")

    all_classes = SchoolClass.objects.filter(school=school)

    return render(request, "school_admin/admin/promote_students.html", {
        "students": students,
        "current_class": current_class,
        "all_classes": all_classes,
        "sessions": SESSION_LIST,
    })




@login_required
def repeat_student(request, student_id):
    admin = request.user.schooladmin_profile
    school = admin.school

    student = get_object_or_404(Student, id=student_id, school=school)

    PromotionHistory.objects.create(
        student=student,
        session=SystemSetting.objects.first().current_session,
        old_class=student.current_class,
        new_class=student.current_class
    )

    messages.success(request, f"{student.full_name} marked as repeating class.")
    return redirect("class_list")




from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from results.models import ClassSubjectTeacher
from .forms import ClassSubjectTeacherForm
from results.utils import portal_required


@login_required
def class_subject_teacher_list(request, school_id):
    school = get_object_or_404(School, id=school_id)

    assignments = (
        ClassSubjectTeacher.objects
        .filter(school_class__school=school)
        .select_related("school_class", "subject", "teacher")
        .order_by("school_class__name", "subject__name")
    )

    return render(request, "school_admin/teachers/class_subject_teacher_list.html", {
        "school": school,
        "assignments": assignments,
    })



@login_required
def class_subject_teacher_create(request, school_id):
    school = get_object_or_404(School, id=school_id)

    if request.method == "POST":
        form = ClassSubjectTeacherForm(request.POST, school=school)
        if form.is_valid():
            form.save()
            messages.success(request, "Subject teacher assigned successfully.")
            return redirect("school_admin:class_subject_teacher_list", school_id=school.id)
    else:
        form = ClassSubjectTeacherForm(school=school)

    return render(request, "school_admin/teachers/class_subject_teacher_form.html", {
        "school": school,
        "form": form,
        "title": "Assign Subject Teacher",
    })



@login_required
def class_subject_teacher_update(request, school_id, pk):
    school = get_object_or_404(School, id=school_id)
    assignment = get_object_or_404(ClassSubjectTeacher, pk=pk)

    if request.method == "POST":
        form = ClassSubjectTeacherForm(request.POST, instance=assignment, school=school)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment updated successfully.")
            return redirect("school_admin:class_subject_teacher_list", school_id=school.id)
    else:
        form = ClassSubjectTeacherForm(instance=assignment, school=school)

    return render(request, "school_admin/teachers/class_subject_teacher_form.html", {
        "school": school,
        "form": form,
        "title": "Edit Subject Teacher Assignment",
    })


@login_required
def class_subject_teacher_delete(request, school_id, pk):
    school = get_object_or_404(School, id=school_id)
    assignment = get_object_or_404(ClassSubjectTeacher, pk=pk)

    assignment.delete()
    messages.success(request, "Assignment deleted.")
    return redirect("school_admin:class_subject_teacher_list", school_id=school.id)




from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages

from finance.models import SchoolAccountant
from .forms import AccountantUserForm, SchoolAccountantForm




@login_required
def accountant_list(request, school_id):
    # Get the school
    school = get_object_or_404(School, id=school_id)

    # Filter only users with role 'accountant' in this school
    accountants = SchoolAccountant.objects.filter(school=school, user__role='accountant')

    return render(request, "school_admin/accountant/list.html", {
        "accountants": accountants,
        "school": school
    })


@login_required
def accountant_toggle_status(request, pk):
    # Get the SchoolAccountant object
    accountant = get_object_or_404(SchoolAccountant, pk=pk)

    # Toggle both the linked user's is_active and the accountant record
    user = accountant.user
    if user and user.role == "accountant":
        user.is_active = not user.is_active
        user.save()
        accountant.is_active = user.is_active
        accountant.save()
        messages.success(request, f"Accountant '{user.username}' status updated successfully.")
    else:
        messages.error(request, "Invalid accountant or role mismatch.")

    return redirect("school_admin:accountant_list", accountant.school.id)



@login_required
def accountant_create(request, school_id):
    school = get_object_or_404(School, id=school_id)

    if request.method == "POST":
        user_form = AccountantUserForm(request.POST)
        acc_form = SchoolAccountantForm(request.POST)

        if user_form.is_valid() and acc_form.is_valid():
            # Create User
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data["password1"])
            user.is_staff = user.role in ["accountant", "schooladmin", "teacher"]
            user.school = school  # <-- Assign school here
            user.save()

            # Create SchoolAccountant if role is accountant
            if user.role == "accountant":
                accountant = acc_form.save(commit=False)
                accountant.user = user
                accountant.school = school
                accountant.save()

            messages.success(request, "Accountant created successfully")
            return redirect("school_admin:accountant_list", school.id)
    else:
        user_form = AccountantUserForm()
        acc_form = SchoolAccountantForm()

    return render(request, "school_admin/accountant/form.html", {
        "user_form": user_form,
        "acc_form": acc_form,
        "school": school
    })



@login_required
def accountant_update(request, pk):
    accountant = get_object_or_404(SchoolAccountant, pk=pk)
    user = accountant.user
    school = accountant.school or user.school  # fallback to ensure school is set

    if request.method == "POST":
        user_form = AccountantUserForm(request.POST, instance=user)
        acc_form = SchoolAccountantForm(request.POST, instance=accountant)

        if user_form.is_valid() and acc_form.is_valid():
            # Update User
            user = user_form.save(commit=False)
            password = user_form.cleaned_data.get("password1")
            if password:
                user.set_password(password)

            # Assign school if missing
            if not getattr(user, "school", None):
                user.school = school

            # Set is_staff based on role
            user.is_staff = user.role in ["accountant", "schooladmin", "teacher"]
            user.save()

            # Handle SchoolAccountant
            if user.role == "accountant":
                accountant = acc_form.save(commit=False)
                accountant.user = user
                accountant.school = school  # ensure school is set
                accountant.save()
            else:
                # Role changed away from accountant → delete SchoolAccountant
                if accountant.pk:
                    accountant.delete()

            messages.success(request, "User updated successfully")
            return redirect(
                "school_admin:accountant_list",
                school.id
            )

    else:
        user_form = AccountantUserForm(instance=user)
        acc_form = SchoolAccountantForm(instance=accountant)

    return render(request, "school_admin/accountant/form.html", {
        "user_form": user_form,
        "acc_form": acc_form,
        "school": school
    })
