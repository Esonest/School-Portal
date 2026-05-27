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

@login_required
def teacher_notes_list(request):
    user = request.user
    teacher_profile = getattr(user, 'teacher_profile', None)
    school = getattr(user, 'school', None)

    # Superadmin → all notes
    if user.is_superadmin:
        notes = LessonNote.objects.all()

    # School admin → all notes in school
    elif school:
        notes = LessonNote.objects.filter(
            school=school
        ).order_by('-publish_date')

    # Teacher → only their own notes
    elif teacher_profile:
        notes = LessonNote.objects.filter(
            teacher=teacher_profile
        ).order_by('-publish_date')

    else:
        raise Http404("Not allowed")

    return render(
        request,
        'notes/teacher_notes_list.html',
        {'notes': notes}
    )

# ------------------------
# Teacher: upload/edit note
@portal_required("lesson_note")
@login_required
def teacher_upload_note(request, pk=None):
    user = request.user
    teacher_profile = getattr(user, 'teacher_profile', None)
    school = getattr(user, 'school', None)

    note = None

    if pk:
        if user.is_superadmin:
            note = get_object_or_404(LessonNote, pk=pk)

        elif school:
            note = get_object_or_404(
                LessonNote,
                pk=pk,
                school=school
            )

        elif teacher_profile:
            note = get_object_or_404(
                LessonNote,
                pk=pk,
                teacher=teacher_profile
            )

        else:
            raise Http404("Not allowed")

    if request.method == 'POST':
        form = LessonNoteForm(
            request.POST,
            request.FILES,
            instance=note,
            teacher=teacher_profile,
            user=user
        )

        if form.is_valid():
            lesson_note = form.save(commit=False)

            # Teacher upload
            if teacher_profile:
                lesson_note.teacher = teacher_profile
                lesson_note.school = teacher_profile.school

            # School admin upload
            elif school:
                lesson_note.school = school

            lesson_note.save()
            form.save_m2m()
            return redirect('notes:dashboard')

    else:
        form = LessonNoteForm(
            instance=note,
            teacher=teacher_profile,
            user=user
        )

    return render(
        request,
        'notes/teacher_upload.html',
        {
            'form': form,
            'note': note
        }
    )



# ------------------------
# Teacher: delete note
# ------------------------

@login_required
def teacher_delete_note(request, pk):
    user = request.user
    teacher_profile = getattr(user, 'teacher_profile', None)
    school = getattr(user, 'school', None)

    # Superadmin
    if user.is_superadmin:
        note = get_object_or_404(
            LessonNote,
            pk=pk
        )

    # School admin → delete any note in school
    elif school:
        note = get_object_or_404(
            LessonNote,
            pk=pk,
            school=school
        )

    # Teacher → only own notes
    elif teacher_profile:
        note = get_object_or_404(
            LessonNote,
            pk=pk,
            teacher=teacher_profile
        )

    else:
        raise Http404("Not allowed")

    if request.method == 'POST':
        note.delete()
        return redirect('notes:teacher_notes_list')

    return render(
        request,
        'notes/teacher_delete_confirm.html',
        {'note': note}
    )


# ------------------------
# Student / public notes
# ------------------------

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
@portal_required("lesson_note")
@login_required
def dashboard(request):
    user = request.user
    teacher_profile = getattr(user, 'teacher_profile', None)
    school = getattr(user, 'school', None)
    student = getattr(user, 'student_profile', None) or getattr(user, 'student', None)

    # School Admin
    if school and not teacher_profile and not student:
        notes = LessonNote.objects.filter(
            school=school
        ).order_by('-publish_date')

        pending = LessonNoteSubmission.objects.filter(
            note__school=school,
            status='submitted'
        ).order_by('submitted_on')[:20]

        context = {
            'is_school_admin': True,
            'can_create_notes': True,
            'notes': notes,
            'pending': pending
        }

    # Teacher
    elif teacher_profile:
        notes = LessonNote.objects.filter(
            teacher=teacher_profile
        ).order_by('-publish_date')

        pending = LessonNoteSubmission.objects.filter(
            note__teacher=teacher_profile,
            status='submitted'
        ).order_by('submitted_on')[:20]

        context = {
            'is_teacher': True,
            'can_create_notes': True,
            'notes': notes,
            'pending': pending
        }

    # Student
    elif student:
        notes = LessonNote.objects.filter(
            classes=student.school_class
        ).distinct().order_by('-publish_date')

        submissions = LessonNoteSubmission.objects.filter(
            student=student
        ).select_related('note')

        subs_map = {s.note_id: s for s in submissions}

        context = {
            'is_teacher': False,
            'notes': notes,
            'submissions': submissions,
            'subs_map': subs_map
        }

    else:
        raise Http404("Profile required")

    return render(
        request,
        'notes/dashboard.html',
        context
    )

