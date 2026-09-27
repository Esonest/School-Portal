from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import Http404, FileResponse
import os, mimetypes
from .models import LessonNote, LessonNoteSubmission
from .forms import LessonNoteForm
from results.utils import portal_required
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from cloudinary.utils import cloudinary_url
import requests

import cloudinary
from cloudinary.utils import cloudinary_url

from django.http import (
    Http404,
    HttpResponse,
)

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

    # ------------------------
    # Edit existing note
    # ------------------------
    if pk:

        if user.is_superadmin:
            note = get_object_or_404(
                LessonNote,
                pk=pk
            )

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


    # ------------------------
    # Submit form
    # ------------------------
    if request.method == "POST":

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


            # --------------------------------
# TEACHER NOTES REQUIRE APPROVAL
# --------------------------------

            if teacher_profile:

                lesson_note.teacher = teacher_profile
                lesson_note.school = teacher_profile.school

    # New teacher uploads and teacher edits
    # must be reviewed again.
                lesson_note.approval_status = 'pending'
                lesson_note.approved_by = None
                lesson_note.approved_on = None
                lesson_note.rejection_reason = ''

# --------------------------------
# SCHOOL ADMIN UPLOAD
# --------------------------------

            elif school:

                lesson_note.school = school

    # Notes created directly by the
    # school admin are automatically approved.
                lesson_note.approval_status = 'approved'
                lesson_note.approved_by = user
                lesson_note.approved_on = timezone.now()
                lesson_note.rejection_reason = ''

            lesson_note.save()
            form.save_m2m()


            if note:
                messages.success(
                    request,
                    "Lesson note updated successfully."
                )

            else:
                messages.success(
                    request,
                    "Lesson note uploaded successfully."
                )


            return redirect(
                "notes:dashboard"
            )


        else:

            messages.error(
                request,
                "Lesson note was not uploaded. Please correct the errors below."
            )


            for field, errors in form.errors.items():

                for error in errors:

                    messages.error(
                        request,
                        f"{field}: {error}"
                    )


    # ------------------------
    # Display empty/edit form
    # ------------------------
    else:

        form = LessonNoteForm(
            instance=note,
            teacher=teacher_profile,
            user=user
        )


    return render(
        request,
        "notes/teacher_upload.html",
        {
            "form": form,
            "note": note
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
from django.core.paginator import Paginator

from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def student_notes_list(request):

    student = (
        getattr(request.user, "student_profile", None)
        or getattr(request.user, "student", None)
    )

    if not student:
        raise Http404("Student profile required")


    today = timezone.now().date()


    notes = LessonNote.objects.select_related(
        "school",
        "subject",
        "teacher",
        "category"
    ).prefetch_related(
        "classes"
    ).filter(
        school=student.school,
        is_active=True,
        approval_status='approved',
        publish_date__lte=today,
    ).filter(
        Q(expiry_date__isnull=True) |
        Q(expiry_date__gte=today)
    ).filter(
        Q(visibility="all") |
        Q(
            visibility="classes",
            classes=student.school_class
        )
    ).distinct().order_by(
        "-publish_date"
    )


    paginator = Paginator(
        notes,
        10
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )


    return render(
        request,
        "notes/student_notes_list.html",
        {
            "notes": page_obj,
        }
    )

# ------------------------
# Note detail
# ------------------------

@login_required
def note_detail(request, pk):

    note = get_object_or_404(
        LessonNote,
        pk=pk,
        school=request.user.school
    )

    user = request.user

    teacher_profile = getattr(
        user,
        "teacher_profile",
        None
    )

    school = getattr(
        user,
        "school",
        None
    )

    student = (
        getattr(user, "student_profile", None)
        or getattr(user, "student", None)
    )

    # ==========================
    # SUPERADMIN
    # ==========================

    if user.is_superadmin:
        pass

    # ==========================
    # SCHOOL ADMIN
    # ==========================

    elif (
        user.role == "schooladmin"
        and school
        and note.school == school
    ):
        pass

    # ==========================
    # TEACHER
    # ==========================

    elif (
        teacher_profile
        and note.teacher == teacher_profile
    ):
        pass

    # ==========================
    # STUDENT
    # ==========================

    elif student:

        # --------------------------------
        # MUST BE APPROVED
        # --------------------------------

        if note.approval_status != "approved":
            raise Http404("Lesson note not available.")

        # --------------------------------
        # MUST BE ACTIVE
        # --------------------------------

        if not note.is_active:
            raise Http404("Lesson note not available.")

        # --------------------------------
        # CHECK PUBLISH DATE
        # --------------------------------

        if note.publish_date > timezone.now().date():
            raise Http404("Lesson note not yet available.")

        # --------------------------------
        # CHECK EXPIRY
        # --------------------------------

        if note.expired:
            raise Http404("Lesson note has expired.")

        # --------------------------------
        # PRIVATE NOTE
        # --------------------------------

        if note.visibility == "private":
            raise Http404("Not allowed")

        # --------------------------------
        # CLASS NOTE
        # --------------------------------

        if (
            note.visibility == "classes"
            and (
                not student.school_class
                or not note.classes.filter(
                    id=student.school_class.id
                ).exists()
            )
        ):
            raise Http404("Not allowed")

    else:

        raise Http404("Not allowed")

    return render(
        request,
        "notes/note_detail.html",
        {
            "note": note
        }
    )

# ------------------------
# Download note file
# ------------------------

from django.http import Http404, HttpResponseRedirect
from urllib.parse import quote

def stream_cloudinary_file(file_field):

    try:

        response = requests.get(
            file_field.url,
            timeout=30
        )


        if response.status_code != 200:

            print("==============================")
            print("❌ CLOUDINARY DOWNLOAD FAILED")
            print("STATUS:", response.status_code)
            print("URL:", file_field.url)
            print("CONTENT TYPE:", response.headers.get("content-type"))
            print("==============================")

            raise Http404(
                "Unable to retrieve the lesson note."
            )


        filename = (
            file_field.name
            .split("/")[-1]
        )


        file_response = HttpResponse(
            response.content,
            content_type="application/pdf"
        )


        file_response[
            "Content-Disposition"
        ] = (
            f'attachment; filename="{filename}"'
        )


        return file_response


    except Exception as e:

        print(
            "DOWNLOAD ERROR:",
            e
        )

        raise Http404(
            "Unable to download file."
        )


@login_required
def download_note_file(request, pk):
    """
    Securely download a lesson-note file.

    The lesson note is retrieved directly from Cloudinary's
    authenticated API and returned by Django as a download.

    This avoids the Cloudinary raw-delivery 401/404 problem.
    """

    import os
    import cloudinary
    from django.http import Http404, HttpResponse
    from django.shortcuts import get_object_or_404
    from django.utils import timezone

    # =========================================================
    # GET LESSON NOTE
    # =========================================================

    note = get_object_or_404(
        LessonNote,
        pk=pk
    )

    user = request.user

    teacher_profile = getattr(
        user,
        "teacher_profile",
        None
    )

    student = (
        getattr(user, "student_profile", None)
        or getattr(user, "student", None)
    )

    school = getattr(
        user,
        "school",
        None
    )

    # =========================================================
    # CHECK FILE EXISTS
    # =========================================================

    if not note.file:
        raise Http404(
            "No file attached to this lesson note."
        )

    # =========================================================
    # SCHOOL SECURITY
    # =========================================================

    if (
        school
        and note.school_id != school.id
        and not getattr(user, "is_superadmin", False)
    ):
        raise Http404(
            "You do not have permission to access this lesson note."
        )

    # =========================================================
    # PERMISSION CHECK
    # =========================================================

    allowed = False

    # ---------------------------------------------------------
    # SUPERADMIN
    # ---------------------------------------------------------

    if getattr(user, "is_superadmin", False):

        allowed = True

    # ---------------------------------------------------------
    # SCHOOL ADMIN
    # ---------------------------------------------------------

    elif (
        getattr(user, "role", None) == "schooladmin"
        and school
        and note.school_id == school.id
    ):

        allowed = True

    # ---------------------------------------------------------
    # TEACHER
    # ---------------------------------------------------------

    elif (
        teacher_profile
        and note.teacher_id == teacher_profile.id
    ):

        allowed = True

    # ---------------------------------------------------------
    # STUDENT
    # ---------------------------------------------------------

    elif student:

        # Students can only access active notes.
        if not note.is_active:
            raise Http404(
                "This lesson note is not currently available."
            )

        # Students can only access approved notes.
        if note.approval_status != "approved":
            raise Http404(
                "This lesson note has not been approved."
            )

        # Publish date.
        if (
            note.publish_date
            and note.publish_date > timezone.now().date()
        ):
            raise Http404(
                "This lesson note is not yet available."
            )

        # Expiry date.
        if (
            note.expiry_date
            and note.expiry_date < timezone.now().date()
        ):
            raise Http404(
                "This lesson note has expired."
            )

        # -----------------------------------------------------
        # ALL STUDENTS
        # -----------------------------------------------------

        if note.visibility == "all":

            allowed = True

        # -----------------------------------------------------
        # SPECIFIC CLASSES
        # -----------------------------------------------------

        elif note.visibility == "classes":

            if (
                student.school_class
                and note.classes.filter(
                    pk=student.school_class.pk
                ).exists()
            ):
                allowed = True

    # =========================================================
    # FINAL PERMISSION CHECK
    # =========================================================

    if not allowed:

        raise Http404(
            "You do not have permission to download this file."
        )

    # =========================================================
    # CLOUDINARY RESOURCE
    # =========================================================

    try:

        # IMPORTANT:
        # Keep the "media/" prefix.
        #
        # Example:
        # media/lesson_notes/TOPIC_-___MATTER_jr4yyp.pdf

        public_id = note.file.name

        print(
            "🔎 CLOUDINARY PUBLIC ID:",
            public_id
        )

        # Ask Cloudinary API for the actual resource.
        resource = cloudinary.api.resource(
            public_id,
            resource_type="raw",
            type="upload",
        )

        print(
            "✅ CLOUDINARY RESOURCE FOUND"
        )

        print(
            "RESOURCE TYPE:",
            resource.get("resource_type")
        )

        print(
            "DELIVERY TYPE:",
            resource.get("type")
        )

        print(
            "VERSION:",
            resource.get("version")
        )

        print(
            "BYTES:",
            resource.get("bytes")
        )

        print(
            "SECURE URL:",
            resource.get("secure_url")
        )

    except Exception as e:

        print(
            "❌ CLOUDINARY RESOURCE ERROR:",
            repr(e)
        )

        raise Http404(
            "Unable to locate the lesson note in Cloudinary."
        )

    # =========================================================
    # DOWNLOAD THE ORIGINAL RESOURCE THROUGH CLOUDINARY API
    # =========================================================

    try:

        # Cloudinary's API client has access to the authenticated
        # Cloudinary account. Use the API resource information
        # to create an authenticated download URL.
        #
        # IMPORTANT:
        # private_download_url() requires the file format.

        from cloudinary.utils import private_download_url

        filename = os.path.basename(
            public_id
        )

        # Raw files retain their extension.
        file_format = ""

        if "." in filename:

            file_format = filename.rsplit(
                ".",
                1
            )[1]

        print(
            "📄 FILE FORMAT:",
            file_format
        )

        download_url = private_download_url(
            public_id,
            file_format,
            resource_type="raw",
            type="upload",
            attachment=True,
        )

        print(
            "🔐 CLOUDINARY DOWNLOAD URL CREATED"
        )

    except Exception as e:

        print(
            "❌ CLOUDINARY DOWNLOAD URL ERROR:",
            repr(e)
        )

        raise Http404(
            "Unable to create the lesson note download."
        )

    # =========================================================
    # FETCH THE FILE
    # =========================================================

    try:

        import requests

        file_response = requests.get(
            download_url,
            timeout=60,
        )

    except requests.RequestException as e:

        print(
            "❌ CLOUDINARY DOWNLOAD REQUEST ERROR:",
            repr(e)
        )

        raise Http404(
            "Unable to download the lesson note."
        )

    # =========================================================
    # CHECK RESPONSE
    # =========================================================

    if file_response.status_code != 200:

        print(
            "❌ LESSON NOTE DOWNLOAD FAILED"
        )

        print(
            "STATUS:",
            file_response.status_code
        )

        print(
            "CONTENT TYPE:",
            file_response.headers.get(
                "Content-Type"
            )
        )

        print(
            "RESPONSE:",
            file_response.text[:500]
        )

        raise Http404(
            "Cloudinary could not retrieve this lesson note."
        )

    # =========================================================
    # CONTENT TYPE
    # =========================================================

    content_type = (
        file_response.headers.get(
            "Content-Type"
        )
        or "application/octet-stream"
    )

    # Force PDF content type for PDF lesson notes.
    if filename.lower().endswith(".pdf"):

        content_type = "application/pdf"

    # =========================================================
    # RETURN FILE THROUGH DJANGO
    # =========================================================

    response = HttpResponse(
        file_response.content,
        content_type=content_type,
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    response["Content-Length"] = str(
        len(file_response.content)
    )

    response["Cache-Control"] = (
        "private, no-store"
    )

    print(
        "✅ LESSON NOTE DOWNLOAD SUCCESSFUL:",
        filename
    )

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
        ).select_related(
            "subject",
            "teacher",
            "approved_by"
        ).order_by(
            "approval_status",
            "-publish_date"
        )

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



# ------------------------
# School Admin: approve note
# ------------------------

@portal_required("lesson_note")
@login_required
def approve_note(request, pk):

    user = request.user
    school = getattr(user, "school", None)

    if user.is_superadmin:

        note = get_object_or_404(
            LessonNote,
            pk=pk
        )

    elif (
        user.role == "schooladmin"
        and school
    ):

        note = get_object_or_404(
            LessonNote,
            pk=pk,
            school=school
        )

    else:

        raise Http404("Not allowed")

    if request.method != "POST":

        raise Http404("Invalid request.")

    note.approval_status = "approved"
    note.approved_by = user
    note.approved_on = timezone.now()
    note.rejection_reason = ""
    note.save(
        update_fields=[
            "approval_status",
            "approved_by",
            "approved_on",
            "rejection_reason",
            "updated_on",
        ]
    )

    messages.success(
        request,
        f'"{note.title}" has been approved and is now available to students.'
    )

    return redirect(
        "notes:dashboard"
    )


@portal_required("lesson_note")
@login_required
def reject_note(request, pk):

    user = request.user
    school = getattr(user, "school", None)

    if user.is_superadmin:

        note = get_object_or_404(
            LessonNote,
            pk=pk
        )

    elif (
        user.role == "schooladmin"
        and school
    ):

        note = get_object_or_404(
            LessonNote,
            pk=pk,
            school=school
        )

    else:

        raise Http404("Not allowed")

    if request.method != "POST":

        raise Http404("Invalid request.")

    reason = request.POST.get(
        "rejection_reason",
        ""
    ).strip()

    note.approval_status = "rejected"
    note.approved_by = None
    note.approved_on = None
    note.rejection_reason = reason

    note.save(
        update_fields=[
            "approval_status",
            "approved_by",
            "approved_on",
            "rejection_reason",
            "updated_on",
        ]
    )

    messages.warning(
        request,
        f'"{note.title}" was rejected.'
    )

    return redirect(
        "notes:dashboard"
    )


# ------------------------
# School Admin: toggle note active/inactive
# ------------------------

@portal_required("lesson_note")
@login_required
def toggle_note_active(request, pk):

    user = request.user
    school = getattr(user, "school", None)

    # -------------------------
    # SUPERADMIN
    # -------------------------

    if user.is_superadmin:

        note = get_object_or_404(
            LessonNote,
            pk=pk
        )

    # -------------------------
    # SCHOOL ADMIN
    # -------------------------

    elif (
        user.role == "schooladmin"
        and school
    ):

        note = get_object_or_404(
            LessonNote,
            pk=pk,
            school=school
        )

    else:

        raise Http404("Not allowed")

    if request.method != "POST":
        raise Http404("Invalid request.")

    note.is_active = not note.is_active

    note.save(
        update_fields=[
            "is_active",
            "updated_on",
        ]
    )

    if note.is_active:

        messages.success(
            request,
            f'"{note.title}" has been activated.'
        )

    else:

        messages.warning(
            request,
            f'"{note.title}" has been deactivated.'
        )

    return redirect(
        "notes:dashboard"
    )    

