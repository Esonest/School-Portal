from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.models import Teacher
from students.models import Student, SchoolClass
from results.models import  Score, Subject, Affective, Psychomotor
from .forms import AssignmentCreateForm, LessonNoteForm
from assignments.models import Assignment
from notes.models import LessonNote
from django.forms import modelformset_factory
from django.db import transaction

# helper decorator
def teacher_required(view_func):
    return user_passes_test(lambda u: hasattr(u, 'teacher'), login_url='accounts:login')(view_func)

@login_required
@teacher_required
def dashboard(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    classes = teacher.classes.all()
    context = {'teacher': teacher, 'classes': classes}
    return render(request, 'results/teacher_dashboard.html', context)

@login_required
@teacher_required
def classes_list(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    classes = teacher.classes.all()
    return render(request, 'teachers/classes.html', {'teacher': teacher, 'classes': classes})

@login_required
@teacher_required
def class_students(request, class_slug):
    sch_class = get_object_or_404(SchoolClass, slug=class_slug)
    students = Student.objects.filter(school_class=sch_class)
    teacher = get_object_or_404(Teacher, user=request.user)
    return render(request, 'teachers/class_students.html', {'class': sch_class, 'students': students, 'teacher': teacher})

@login_required
@teacher_required
def enter_scores(request, exam_id, class_slug=None):
    exam = get_object_or_404(Exam, id=exam_id)
    teacher = get_object_or_404(Teacher, user=request.user)
    # restrict subjects to teacher's subjects
    subjects = teacher.subjects.all()
    # students optionally filtered by class
    students = Student.objects.filter(school_class__slug=class_slug) if class_slug else Student.objects.all()

    ScoreFormSetLocal = modelformset_factory(Score, fields=('student','subject','ca','exam_score'), extra=0)

    if request.method == 'POST':
        formset = ScoreFormSetLocal(request.POST, queryset=Score.objects.filter(exam=exam, student__in=students))
        if formset.is_valid():
            with transaction.atomic():
                instances = formset.save(commit=False)
                for obj in instances:
                    obj.exam = exam
                    obj.save()
            return redirect('teachers:enter_scores', exam_id=exam.id)
    else:
        # prepare initial queryset: existing scores or create blanks for each student-subject
        existing = Score.objects.filter(exam=exam, student__in=students)
        if not existing.exists():
            # create Score objects for each student-subject combination so formset can display
            objs = []
            for st in students:
                for subj in subjects:
                    objs.append(Score(student=st, subject=subj, exam=exam))
            Score.objects.bulk_create(objs)
        formset = ScoreFormSetLocal(queryset=Score.objects.filter(exam=exam, student__in=students))

    return render(request, 'teachers/enter_scores.html', {'formset': formset, 'exam': exam, 'teacher': teacher, 'students': students, 'subjects': subjects})

@login_required
@teacher_required
def enter_affective(request, exam_id, class_slug=None):
    exam = get_object_or_404(Exam, id=exam_id)
    students = Student.objects.filter(school_class__slug=class_slug) if class_slug else Student.objects.all()
    if request.method == 'POST':
        form = AffectiveForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('teachers:enter_affective', exam_id=exam.id)
    else:
        form = AffectiveForm(initial={'exam': exam})
    records = Affective.objects.filter(exam=exam, student__in=students)
    return render(request, 'teachers/affective.html', {'form': form, 'records': records, 'exam': exam})

@login_required
@teacher_required
def enter_psychomotor(request, exam_id, class_slug=None):
    exam = get_object_or_404(Exam, id=exam_id)
    students = Student.objects.filter(school_class__slug=class_slug) if class_slug else Student.objects.all()
    if request.method == 'POST':
        form = PsychomotorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('teachers:enter_psychomotor', exam_id=exam.id)
    else:
        form = PsychomotorForm(initial={'exam': exam})
    records = Psychomotor.objects.filter(exam=exam, student__in=students)
    return render(request, 'teachers/psychomotor.html', {'form': form, 'records': records, 'exam': exam})

@login_required
@teacher_required
def create_assignment(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    if request.method == 'POST':
        form = AssignmentCreateForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.save()
            return redirect('teachers:assignments')
    else:
        form = AssignmentCreateForm()
    return render(request, 'teachers/create_assignment.html', {'form': form})

@login_required
@teacher_required
def assignments_list(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    qs = Assignment.objects.order_by('-created_on')
    return render(request, 'teachers/assignments_list.html', {'assignments': qs})

@login_required
@teacher_required
def upload_note(request):
    if request.method == 'POST':
        form = LessonNoteForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('teachers:notes')
    else:
        form = LessonNoteForm()
    notes = LessonNote.objects.order_by('-created_on')
    return render(request, 'teachers/upload_note.html', {'form': form, 'notes': notes})

@login_required
@teacher_required
def manage_cbt(request):
    # placeholder view to link to CBT admin or custom CBT management
    exams = Exam.objects.order_by('-date')
    return render(request, 'teachers/manage_cbt.html', {'exams': exams})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import teacher_required

@login_required
@teacher_required
def teacher_dashboard(request):
    teacher = request.user.teacher_profile
    context = {'teacher': teacher}
    return render(request, 'teachers/teacher_dashboard.html', context)




@login_required
@teacher_required
def teacher_result_dashboard(request):
    teacher = request.user.teacher_profile
    
    school = teacher.school  # ✅ Clean and readable
    school_id = school.id if school else None

    results = []  # You can populate this later
    context = {
        'teacher': teacher,
        'results': results,
        'school': school,
        'school_id': school_id
    }
    return render(request, 'results/teacher_result_dashboard.html', context)
