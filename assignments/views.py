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


def get_user_role_access(user):

    teacher = getattr(
        user,
        "teacher_profile",
        None
    )

    school = getattr(
        user,
        "school",
        None
    )


    # Teacher
    if teacher:
        return {
            "role": "teacher",
            "teacher": teacher,
            "school": teacher.school
        }


    # School admin
    if getattr(user, "role", None) == "schooladmin":

        return {
            "role": "schooladmin",
            "school": user.school
        }


    # Super admin
    if getattr(user, "role", None) == "superadmin":

        return {
            "role": "superadmin",
            "school": None
        }


    return None



# ------------------------
# Teacher / Student dashboard
# ------------------------
@portal_required("assignments")
@login_required
def dashboard(request):

    user = request.user

    teacher_profile = getattr(
        user,
        "teacher_profile",
        None
    )


    student_profile = getattr(
        user,
        "student_profile",
        None
    )


    role = getattr(
        user,
        "role",
        None
    )



    # ==========================
    # TEACHER DASHBOARD
    # ==========================

    if teacher_profile:


        assignments = Assignment.objects.filter(
            teacher=teacher_profile,
            school=teacher_profile.school
        ).select_related(
            "subject",
            "teacher"
        ).prefetch_related(
            "classes"
        ).order_by(
            "-created_on"
        )


        pending = AssignmentSubmission.objects.filter(
            assignment__teacher=teacher_profile,
            status="submitted"
        ).select_related(
            "assignment",
            "student"
        ).order_by(
            "submitted_on"
        )[:20]


        return render(
            request,
            "assignments/dashboard.html",
            {
                "is_teacher": True,
                "is_admin": False,
                "is_superadmin": False,
                "assignments": assignments,
                "pending": pending,
                "school": teacher_profile.school,
            }
        )



    # ==========================
    # SCHOOL ADMIN
    # ==========================

    if role in [
        "schooladmin",
        "school_admin"
    ]:


        school = getattr(
            user,
            "school",
            None
        )


        if not school:
            raise Http404(
                "School not assigned."
            )


        assignments = Assignment.objects.filter(
            school=school
        ).select_related(
            "teacher",
            "subject"
        ).prefetch_related(
            "classes"
        ).order_by(
            "-created_on"
        )


        return render(
            request,
            "assignments/dashboard.html",
            {
                "is_teacher": False,
                "is_admin": True,
                "is_superadmin": False,
                "assignments": assignments,
                "school": school,
            }
        )



    # ==========================
    # SUPER ADMIN
    # ==========================

    if role == "superadmin":


        assignments = Assignment.objects.all().select_related(
            "school",
            "teacher",
            "subject"
        ).prefetch_related(
            "classes"
        ).order_by(
            "-created_on"
        )


        return render(
            request,
            "assignments/dashboard.html",
            {
                "is_teacher": False,
                "is_admin": True,
                "is_superadmin": True,
                "assignments": assignments,
            }
        )



    # ==========================
    # STUDENT
    # ==========================

    if student_profile:


        assignments = Assignment.objects.filter(
            school=student_profile.school,
            classes=student_profile.school_class,
            published=True,
            is_active=True
        ).exclude(
            expiry_date__lt=timezone.now()
        ).select_related(
            "subject",
            "teacher"
        ).distinct().order_by(
            "-created_on"
        )



        submissions = AssignmentSubmission.objects.filter(
            student=student_profile
        ).select_related(
            "assignment"
        )


        subs_map = {
            item.assignment_id:item
            for item in submissions
        }



        return render(
            request,
            "assignments/student_dashboard.html",
            {
                "is_teacher": False,
                "is_admin": False,
                "student": student_profile,
                "assignments": assignments,
                "submissions": submissions,
                "subs_map": subs_map,
                "now": timezone.now(),
            }
        )



    raise Http404(
        "Dashboard access denied."
    )


# ------------------------
# Create or edit assignment (teacher)
# ------------------------
@login_required
def create_assignment(request, pk=None):

    access = get_user_role_access(request.user)

    if not access:
        raise Http404("Permission denied")


    assignment = None


    if pk:

        if access["role"] == "teacher":

            assignment = get_object_or_404(
                Assignment,
                pk=pk,
                teacher=access["teacher"]
            )


        elif access["role"] == "schooladmin":

            assignment = get_object_or_404(
                Assignment,
                pk=pk,
                school=access["school"]
            )


        elif access["role"] == "superadmin":

            assignment = get_object_or_404(
                Assignment,
                pk=pk
            )



    if request.method == "POST":

        form = AssignmentForm(
            request.POST,
            request.FILES,
            instance=assignment,
            teacher=access.get("teacher"),
            school=access.get("school")
        )


        if form.is_valid():

            obj=form.save(commit=False)


            # Teacher ownership
            if access["role"]=="teacher":

                obj.teacher=access["teacher"]
                obj.school=access["teacher"].school


            # School admin
            elif access["role"]=="schooladmin":

                obj.school=access["school"]


            # Super admin
            elif access["role"]=="superadmin":

                obj.school=form.cleaned_data.get(
                    "school"
                )


            obj.save()

            form.save_m2m()


            messages.success(
                request,
                "Assignment saved successfully."
            )

            return redirect(
                "assignments:dashboard"
            )


    else:

        form=AssignmentForm(
            instance=assignment,
            teacher=access.get("teacher"),
            school=access.get("school")
        )


    return render(
        request,
        "assignments/create.html",
        {
            "form":form,
            "assignment":assignment
        }
    )


# ------------------------
# Assignment detail & submissions
# ------------------------

@login_required
def assignment_detail(request, pk):

    access=get_user_role_access(request.user)


    if access["role"]=="teacher":

        assignment=get_object_or_404(
            Assignment,
            pk=pk,
            teacher=access["teacher"]
        )


    elif access["role"]=="schooladmin":

        assignment=get_object_or_404(
            Assignment,
            pk=pk,
            school=access["school"]
        )


    else:

        assignment=get_object_or_404(
            Assignment,
            pk=pk
        )



    submissions=assignment.submissions.select_related(
        "student"
    )


    return render(
        request,
        "assignments/teacher_assignment_detail.html",
        {
            "assignment":assignment,
            "submissions":submissions
        }
    )
# ------------------------
# Delete assignment
# ------------------------

@login_required
def delete_assignment(request, pk):

    access=get_user_role_access(request.user)


    if not access:
        raise Http404()



    if access["role"]=="teacher":

        assignment=get_object_or_404(
            Assignment,
            pk=pk,
            teacher=access["teacher"]
        )


    elif access["role"]=="schooladmin":

        assignment=get_object_or_404(
            Assignment,
            pk=pk,
            school=access["school"]
        )


    else:

        assignment=get_object_or_404(
            Assignment,
            pk=pk
        )



    if request.method=="POST":

        assignment.delete()

        messages.success(
            request,
            "Assignment deleted successfully."
        )

        return redirect(
            "assignments:dashboard"
        )


    return render(
        request,
        "assignments/confirm_delete.html",
        {
            "assignment":assignment
        }
    )

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

    assignment = get_object_or_404(
        Assignment,
        pk=pk,
        published=True,
        classes=student.school_class
    )


    # Only fetch existing submission, do not create one yet
    submission = AssignmentSubmission.objects.filter(
        assignment=assignment,
        student=student
    ).first()


    if request.method == "POST":

        # Create form instance only when submitting
        form = SubmissionForm(
            request.POST,
            request.FILES,
            instance=submission
        )

        files = request.FILES.getlist('files')
        print(request.FILES)


        if form.is_valid():

            obj = form.save(commit=False)

            obj.assignment = assignment
            obj.student = student

            obj.status = (
                'late'
                if assignment.expiry_date and timezone.now() > assignment.expiry_date
                else 'submitted'
            )

            obj.save()


            for f in files:
                SubmissionFile.objects.create(
                    submission=obj,
                    file=f
                )


            messages.success(
                request,
                "Your assignment has been submitted."
            )

            return redirect('assignments:dashboard')


    else:

        form = SubmissionForm(
            instance=submission
        )


    return render(
        request,
        'assignments/submit_assignment.html',
        {
            'form': form,
            'assignment': assignment,
            'submission': submission
        }
    )

# Teacher: grade a submission
from accounts.models import Teacher
@login_required
def grade_submission(request, submission_id):
    """
    Grade assignment submission.
    Allowed:
    - Assignment teacher
    - School admin
    - Superadmin
    """

    user = request.user

    role = getattr(
        user,
        "role",
        None
    )


    submission = get_object_or_404(
        AssignmentSubmission.objects.select_related(
            "assignment",
            "student",
            "assignment__teacher",
            "assignment__school"
        ),
        pk=submission_id
    )


    assignment = submission.assignment


    teacher_profile = getattr(
        user,
        "teacher_profile",
        None
    )


    # -------------------------
    # PERMISSION CHECK
    # -------------------------

    allowed = False


    if teacher_profile and assignment.teacher == teacher_profile:

        allowed = True


    elif role in [
        "schooladmin",
        "school_admin"
    ] and user.school == assignment.school:

        allowed = True


    elif role == "superadmin":

        allowed = True



    if not allowed:

        messages.error(
            request,
            "You are not authorized to grade this submission."
        )

        return redirect(
            "assignments:dashboard"
        )



    # -------------------------
    # PROCESS FORM
    # -------------------------

    if request.method == "POST":

        form = GradeForm(
            request.POST
        )


        if form.is_valid():

            score = form.cleaned_data["score"]

            feedback = form.cleaned_data["feedback"]



            grader = teacher_profile



            submission.mark_graded(
                score,
                feedback,
                grader
            )


            messages.success(
                request,
                "Submission graded successfully."
            )


            return redirect(
                "assignments:teacher_assignment_detail",
                pk=assignment.pk
            )



    else:


        form = GradeForm(
            initial={
                "score": submission.score or "",
                "feedback": submission.feedback
            }
        )



    return render(
        request,
        "assignments/grade_submission.html",
        {
            "form": form,
            "submission": submission,
        }
    )





# ======================================================
# DOWNLOAD SUBMISSION FILE
# ======================================================



@login_required
def download_submission_file(request, file_id):
    import os
    import logging
    import requests
    import cloudinary

    from cloudinary.utils import private_download_url
    from django.http import Http404, HttpResponse

    user = request.user
    role = getattr(user, "role", None)

    sf = get_object_or_404(
        SubmissionFile.objects.select_related(
            "submission",
            "submission__student",
            "submission__assignment",
            "submission__assignment__school"
        ),
        pk=file_id
    )

    assignment = sf.submission.assignment

    student = getattr(user, "student_profile", None)
    teacher = getattr(user, "teacher_profile", None)

    allowed = False

    # Student who submitted the file
    if student and sf.submission.student == student:
        allowed = True

    # Assignment teacher
    elif teacher and assignment.teacher == teacher:
        allowed = True

    # School administrator
    elif (
        role in ["schooladmin", "school_admin"]
        and user.school == assignment.school
    ):
        allowed = True

    # Superadmin
    elif role == "superadmin":
        allowed = True

    if not allowed:
        raise Http404(
            "Not authorized to download this file."
        )

    if not sf.file:
        raise Http404("No submission file is attached.")

    # Retrieve the file from Cloudinary
    try:
        public_id = sf.file.name

        resource = cloudinary.api.resource(
            public_id,
            resource_type="raw",
            type="upload",
        )

    except Exception as e:
        logging.exception(
            "SUBMISSION CLOUDINARY RESOURCE ERROR: %s",
            repr(e)
        )
        raise Http404(
            "Unable to locate the submitted file in Cloudinary."
        )

    # Generate authenticated download URL
    try:
        filename = sf.filename() or os.path.basename(public_id)

        file_format = ""
        cloudinary_filename = os.path.basename(public_id)

        if "." in cloudinary_filename:
            file_format = cloudinary_filename.rsplit(".", 1)[1]

        download_url = private_download_url(
            public_id,
            file_format,
            resource_type="raw",
            type="upload",
            attachment=True,
        )

    except Exception as e:
        logging.exception(
            "SUBMISSION DOWNLOAD URL ERROR: %s",
            repr(e)
        )
        raise Http404(
            "Unable to create the submission download."
        )

    # Download file from Cloudinary
    try:
        file_response = requests.get(
            download_url,
            timeout=60
        )

    except requests.RequestException as e:
        logging.exception(
            "SUBMISSION DOWNLOAD REQUEST ERROR: %s",
            repr(e)
        )
        raise Http404(
            "Unable to retrieve the submitted file."
        )

    if file_response.status_code != 200:
        logging.error(
            "SUBMISSION DOWNLOAD FAILED. Status: %s; "
            "Content-Type: %s; Response: %s",
            file_response.status_code,
            file_response.headers.get("Content-Type"),
            file_response.text[:500]
        )
        raise Http404(
            "Cloudinary could not retrieve the submitted file."
        )

    content_type = (
        file_response.headers.get("Content-Type")
        or "application/octet-stream"
    )

    if filename.lower().endswith(".pdf"):
        content_type = "application/pdf"

    response = HttpResponse(
        file_response.content,
        content_type=content_type
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{os.path.basename(filename)}"'
    )
    response["Content-Length"] = str(len(file_response.content))
    response["Cache-Control"] = "private, no-store"

    return response


@login_required
def download_assignment_file(request, pk):
    """
    Securely download an assignment resource through
    Cloudinary's authenticated API.

    Uses the same working download approach as Notes.
    """

    import os
    import requests
    import cloudinary

    from cloudinary.utils import private_download_url
    from django.http import Http404, HttpResponse
    from django.shortcuts import get_object_or_404
    from django.utils import timezone

    # =====================================================
    # GET ASSIGNMENT
    # =====================================================

    assignment = get_object_or_404(
        Assignment,
        pk=pk
    )

    user = request.user

    role = getattr(user, "role", None)

    teacher = getattr(
        user,
        "teacher_profile",
        None
    )

    student = getattr(
        user,
        "student_profile",
        None
    )

    school = getattr(
        user,
        "school",
        None
    )

    # =====================================================
    # CHECK FILE
    # =====================================================

    if not assignment.file:
        raise Http404(
            "No file attached to this assignment."
        )

    # =====================================================
    # PERMISSION CHECK
    # =====================================================

    allowed = False

    # SUPERADMIN

    if (
        role == "superadmin"
        or getattr(user, "is_superadmin", False)
    ):

        allowed = True

    # SCHOOL ADMIN

    elif (
        role in ["schooladmin", "school_admin"]
        and school
        and assignment.school_id == school.id
    ):

        allowed = True

    # TEACHER

    elif (
        teacher
        and assignment.teacher_id == teacher.id
    ):

        allowed = True

    # STUDENT

    elif student:

        if (
            assignment.school_id == student.school_id
            and assignment.is_active
            and assignment.published
            and assignment.classes.filter(
                pk=student.school_class_id
            ).exists()
            and (
                not assignment.expiry_date
                or assignment.expiry_date >= timezone.now()
            )
        ):

            allowed = True

    # FINAL PERMISSION CHECK

    if not allowed:

        raise Http404(
            "You do not have permission to download this assignment."
        )

    # =====================================================
    # CLOUDINARY RESOURCE
    # =====================================================

    try:

        public_id = assignment.file.name

        print(
            "ASSIGNMENT CLOUDINARY PUBLIC ID:",
            public_id
        )

        resource = cloudinary.api.resource(
            public_id,
            resource_type="raw",
            type="upload",
        )

        print(
            "ASSIGNMENT CLOUDINARY RESOURCE FOUND"
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
            "SECURE URL:",
            resource.get("secure_url")
        )

    except Exception as e:

        import logging

        logging.exception(
            "ASSIGNMENT CLOUDINARY RESOURCE ERROR: %s",
            repr(e)
        )

        raise Http404(
            "Unable to locate the assignment file in Cloudinary."
        )

    # =====================================================
    # GENERATE AUTHENTICATED DOWNLOAD URL
    # =====================================================

    try:

        filename = os.path.basename(
            public_id
        )

        file_format = ""

        if "." in filename:

            file_format = filename.rsplit(
                ".",
                1
            )[1]

        print(
            "ASSIGNMENT FILE FORMAT:",
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
            "ASSIGNMENT AUTHENTICATED DOWNLOAD URL CREATED"
        )

    except Exception as e:

        import logging

        logging.exception(
            "ASSIGNMENT DOWNLOAD URL ERROR: %s",
            repr(e)
        )

        raise Http404(
            "Unable to create the assignment download."
        )

    # =====================================================
    # DOWNLOAD FILE FROM CLOUDINARY
    # =====================================================

    try:

        file_response = requests.get(
            download_url,
            timeout=60
        )

    except requests.RequestException as e:

        import logging

        logging.exception(
            "ASSIGNMENT DOWNLOAD REQUEST ERROR: %s",
            repr(e)
        )

        raise Http404(
            "Unable to retrieve the assignment file."
        )

    # =====================================================
    # CHECK DOWNLOAD RESPONSE
    # =====================================================

    if file_response.status_code != 200:

        print(
            "ASSIGNMENT DOWNLOAD FAILED"
        )

        print(
            "STATUS:",
            file_response.status_code
        )

        print(
            "CONTENT TYPE:",
            file_response.headers.get("Content-Type")
        )

        print(
            "RESPONSE:",
            file_response.text[:500]
        )

        raise Http404(
            "Cloudinary could not retrieve this assignment file."
        )

    # =====================================================
    # CONTENT TYPE
    # =====================================================

    content_type = (
        file_response.headers.get(
            "Content-Type"
        )
        or "application/octet-stream"
    )

    if filename.lower().endswith(".pdf"):

        content_type = "application/pdf"

    # =====================================================
    # RETURN FILE THROUGH DJANGO
    # =====================================================

    response = HttpResponse(
        file_response.content,
        content_type=content_type
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
        "ASSIGNMENT DOWNLOAD SUCCESSFUL:",
        filename
    )

    return response

# ======================================================
# SUBMISSION LIST
# ======================================================


@login_required
def submission_list(request, assignment_id=None):

    user = request.user

    role = getattr(
        user,
        "role",
        None
    )


    teacher = getattr(
        user,
        "teacher_profile",
        None
    )


    student = getattr(
        user,
        "student_profile",
        None
    )



    # -------------------------
    # TEACHER
    # -------------------------

    if teacher:


        qs = AssignmentSubmission.objects.filter(
            assignment__teacher=teacher
        )



    # -------------------------
    # SCHOOL ADMIN
    # -------------------------

    elif role in [
        "schooladmin",
        "school_admin"
    ]:


        qs = AssignmentSubmission.objects.filter(
           assignment__school=user.school
        )



    # -------------------------
    # SUPERADMIN
    # -------------------------

    elif role == "superadmin":


        qs = AssignmentSubmission.objects.all()



    # -------------------------
    # STUDENT
    # -------------------------

    elif student:


        qs = AssignmentSubmission.objects.filter(
            student=student
        )



    else:

        raise Http404(
            "Permission denied."
        )



    if assignment_id:

        qs = qs.filter(
            assignment_id=assignment_id
        )



    qs = qs.select_related(
        "assignment",
        "student"
    ).order_by(
        "-submitted_on"
    )



    return render(
        request,
        "assignments/submission_list.html",
        {
            "submissions": qs
        }
    )