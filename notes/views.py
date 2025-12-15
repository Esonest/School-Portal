from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import Http404, FileResponse
import os, mimetypes
from .models import LessonNote, LessonNoteSubmission
from .forms import LessonNoteForm
from results.utils import portal_required

# ------------------------
# Teacher: list notes
# ------------------------
@portal_required("notes")
@login_required
def teacher_notes_list(request):
    teacher_profile = getattr(request.user, 'teacher_profile', None)
    if not teacher_profile:
        raise Http404("No teacher profile found.")

    notes = LessonNote.objects.filter(teacher=teacher_profile).order_by('-publish_date')
    return render(request, 'notes/teacher_notes_list.html', {'notes': notes})


# ------------------------
# Teacher: upload/edit note
# ------------------------
@portal_required("notes")
@login_required
def teacher_upload_note(request, pk=None):
    teacher_profile = getattr(request.user, 'teacher_profile', None)
    if not teacher_profile:
        raise Http404("No teacher profile found.")

    note = get_object_or_404(LessonNote, pk=pk, teacher=teacher_profile) if pk else None

    if request.method == 'POST':
        form = LessonNoteForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            lesson_note = form.save(commit=False)
            lesson_note.teacher = teacher_profile
            lesson_note.save()
            form.save_m2m()
            return redirect('notes:dashboard')
    else:
        form = LessonNoteForm(instance=note)

    return render(request, 'notes/teacher_upload.html', {'form': form, 'note': note})


# ------------------------
# Teacher: delete note
# ------------------------
@portal_required("notes")
@login_required
def teacher_delete_note(request, pk):
    teacher_profile = getattr(request.user, 'teacher_profile', None)
    if not teacher_profile:
        raise Http404("No teacher profile found.")

    note = get_object_or_404(LessonNote, pk=pk, teacher=teacher_profile)

    if request.method == 'POST':
        note.delete()
        return redirect('notes:teacher_notes_list')

    return render(request, 'notes/teacher_delete_confirm.html', {'note': note})


# ------------------------
# Student / public notes
# ------------------------
@portal_required("notes")
@login_required
def student_notes_list(request):
    student = getattr(request.user, 'student_profile', None) or getattr(request.user, 'student', None)
    if not student:
        raise Http404("Student profile required")

    qs = LessonNote.objects.filter(publish_date__lte=timezone.now())
    qs_all = qs.filter(visibility='all')
    qs_private = qs.filter(visibility='private', teacher=getattr(request.user, 'teacher_profile', None))
    qs_classes = qs.filter(visibility='classes', classes=student.school_class) if student.school_class else LessonNote.objects.none()

    notes = (qs_all | qs_classes | qs_private).distinct().order_by('-publish_date')
    return render(request, 'notes/student_notes_list.html', {'notes': notes})


# ------------------------
# Note detail
# ------------------------
@portal_required("notes")
@login_required
def note_detail(request, pk):
    note = get_object_or_404(LessonNote, pk=pk)
    teacher_profile = getattr(request.user, 'teacher_profile', None)
    student = getattr(request.user, 'student_profile', None) or getattr(request.user, 'student', None)

    if note.visibility == 'private' and note.teacher != teacher_profile:
        raise Http404("Not allowed")
    if note.visibility == 'classes' and (not student or student.school_class not in note.classes.all()):
        if not teacher_profile:
            raise Http404("Not allowed")

    return render(request, 'notes/note_detail.html', {'note': note})


# ------------------------
# Download note file
# ------------------------
@portal_required("notes")
@login_required
def download_note_file(request, pk):
    note = get_object_or_404(LessonNote, pk=pk)
    teacher_profile = getattr(request.user, 'teacher_profile', None)
    student = getattr(request.user, 'student_profile', None) or getattr(request.user, 'student', None)

    if not note.file:
        raise Http404("No file attached.")

    if note.visibility == 'private' and note.teacher != teacher_profile:
        raise Http404("Not allowed")
    if note.visibility == 'classes' and (not student or student.school_class not in note.classes.all()):
        if not teacher_profile:
            raise Http404("Not allowed")

    file_path = note.file.path
    filename = os.path.basename(file_path)
    content_type, encoding = mimetypes.guess_type(file_path)
    content_type = content_type or 'application/octet-stream'

    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ------------------------
# Notes dashboard
# ------------------------
@portal_required("notes")
@login_required
def dashboard(request):
    user = request.user
    teacher_profile = getattr(user, 'teacher_profile', None)
    student = getattr(user, 'student_profile', None) or getattr(user, 'student', None)

    if teacher_profile:
        notes = LessonNote.objects.filter(teacher=teacher_profile).order_by('-publish_date')
        pending = LessonNoteSubmission.objects.filter(note__teacher=teacher_profile, status='submitted').order_by('submitted_on')[:20]
        context = {'is_teacher': True, 'notes': notes, 'pending': pending}
    elif student:
        notes = LessonNote.objects.filter(classes=student.school_class).order_by('-publish_date')
        submissions = LessonNoteSubmission.objects.filter(student=student).select_related('note')
        subs_map = {s.note_id: s for s in submissions}
        context = {'is_teacher': False, 'notes': notes, 'submissions': submissions, 'subs_map': subs_map}
    else:
        raise Http404("Profile required")

    return render(request, 'notes/dashboard.html', context)
