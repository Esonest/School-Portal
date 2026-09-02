import random
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from .models import CBTExam, CBTQuestion, CBTSubmission
from students.models import Student
from results.utils import portal_required, normalize_latex
from django.http import Http404
from tis_website.models import AdmissionApplication




# --------------------------------------
# 🧾 List Active Exams
# --------------------------------------
@portal_required("cbt")
@login_required
def exam_list(request):
    now = timezone.now()

    # ✅ Get logged-in student safely
    student = getattr(request.user, 'student_profile', None) or getattr(request.user, 'student', None)
    if not student:
        return HttpResponseForbidden("You must be logged in as a student to view available exams.")

    # ✅ Get exams for:
    # 1. Student's school
    # 2. Student's class
    # 3. Active status
    # 4. Valid time window
    exams = CBTExam.objects.filter(
        school=student.school,
        school_class=student.school_class,   # 🔑 restrict to class
        active=True,
        start_time__lte=now,
        end_time__gte=now
    ).select_related("subject")

    # ✅ Mark already-taken exams
    taken_exam_ids = set(
        CBTSubmission.objects.filter(
            student=student,
            completed_on__isnull=False
        ).values_list('exam_id', flat=True)
    )

    for exam in exams:
        exam.already_taken = exam.id in taken_exam_ids

    return render(request, "cbt/exam_list.html", {
        "exams": exams,
    })




# --------------------------------------
# 🚦 Start Exam Page (Attempt Check)
# --------------------------------------
@portal_required("cbt")
@login_required
def start_exam_page(request, exam_id):

    exam = get_object_or_404(
        CBTExam,
        id=exam_id
    )

    student = None
    application = None
    submission = None
    school = None

    # ==============================
    # ADMISSION EXAM
    # ==============================
    if exam.exam_type == "admission":

        application_id = request.session.get(
            "admission_application_id"
        )

        if not application_id:
            raise Http404(
                "Candidate not found"
            )

        application = get_object_or_404(
            AdmissionApplication,
            id=application_id
        )

        submission = CBTSubmission.objects.filter(
            admission_candidate=application,
            exam=exam
        ).first()

        school = application.school

        # ✅ Candidate has viewed the instruction page
        request.session["exam_instruction_viewed"] = True

    # ==============================
    # NORMAL STUDENT EXAM
    # ==============================
    else:

        student = (
            getattr(request.user, "student_profile", None)
            or getattr(request.user, "student", None)
        )

        if not student:
            return HttpResponseForbidden(
                "You must be logged in as a student."
            )

        submission = CBTSubmission.objects.filter(
            student=student,
            exam=exam
        ).first()

        school = student.school

    already_taken = (
        submission is not None
        and submission.completed_on is not None
    )

    return render(
        request,
        "cbt/start_exam.html",
        {
            "exam": exam,
            "student": student,
            "application": application,
            "admission_mode": exam.exam_type == "admission",
            "already_taken": already_taken,
            "school": school,
        }
    )
# --------------------------------------
# 🧠 Start Exam Action (Single Attempt Only)
# --------------------------------------
@portal_required("cbt")
@login_required
def start_exam(request, exam_id):

    exam = get_object_or_404(CBTExam, id=exam_id)

    # ==========================
    # GET CANDIDATE / STUDENT
    # ==========================

    if exam.exam_type == "admission":

        application = get_object_or_404(
            AdmissionApplication,
            id=request.session.get("admission_application_id")
        )

        submission = CBTSubmission.objects.filter(
            admission_candidate=application,
            exam=exam
        ).first()


    else:

        student = getattr(request.user, "student_profile", None) or getattr(request.user, "student", None)

        if not student:
            return HttpResponseForbidden("Student account required.")

        submission = CBTSubmission.objects.filter(
            student=student,
            exam=exam
        ).first()
    now = timezone.now()
    if not (exam.start_time <= now <= exam.end_time):
        return HttpResponseForbidden("This exam is not active at the moment.")

    # 🚫 Check if already completed
    
    if submission:
        if submission.completed_on:
            return redirect("cbt:cbt_result_analysis", exam_id=exam.id)
        else:
            # resume
            request.session["question_order"] = submission.raw_answers.get("_question_order", [])
            # ✅ preserve original start time
            if "exam_start_time" not in request.session:
                request.session["exam_start_time"] = submission.raw_answers.get(
                    "_exam_start_time"
                )
            return redirect("cbt:take_exam", exam_id=exam.id, question_index=0)

    # ✅ create new submission
    if exam.exam_type == "admission":

        submission = CBTSubmission.objects.create(
            admission_candidate=application,
            exam=exam
        )

    else:

        submission = CBTSubmission.objects.create(
            student=student,
            exam=exam
        )

    question_order = list(exam.questions.values_list("id", flat=True))
    random.shuffle(question_order)

    exam_start_time = timezone.now().isoformat()

    submission.raw_answers["_question_order"] = question_order
    submission.raw_answers["_exam_start_time"] = exam_start_time
    submission.save(update_fields=["raw_answers"])

    request.session["question_order"] = question_order
    request.session["exam_start_time"] = exam_start_time

    return redirect("cbt:take_exam", exam_id=exam.id, question_index=0)


@portal_required("cbt")
@login_required
def take_exam(request, exam_id, question_index):
    import random
    from django.utils import timezone

    exam = get_object_or_404(CBTExam, id=exam_id)

    student = None
    application = None


# Admission CBT
    if exam.exam_type == "admission":

        from tis_website.models import AdmissionApplication

        application_id = request.session.get(
            "admission_application_id"
        )

        if not application_id:
            raise Http404("Admission candidate not found")

        application = get_object_or_404(
            AdmissionApplication,
            id=application_id
        )

        submission = CBTSubmission.objects.filter(
            admission_candidate=application,
            exam=exam
        ).first()


# Normal Student CBT
    else:

        student = (
            getattr(request.user, "student_profile", None)
            or getattr(request.user, "student", None)
        )

        if not student:
            return HttpResponseForbidden(
                "You must be logged in as a student to take this exam."
            )

        submission = CBTSubmission.objects.filter(
            student=student,
            exam=exam
        ).first()


    if not submission:
        return redirect(
            "cbt:start_exam_page",
            exam_id=exam.id
        )

    # Prevent retake after completion
   # Prevent access after completion
    if submission.completed_on:
        return render(request, "cbt/exam_ended.html", {
            "exam": exam,
            "student": student,
            "application": application,
            "admission_mode": exam.exam_type == "admission",
        })

    # ------------------ QUESTION ORDER ------------------
    question_order = request.session.get("question_order") or submission.raw_answers.get("_question_order")
    if not question_order:
        question_order = list(
            CBTQuestion.objects.filter(exam=exam).values_list("id", flat=True)
        )
        random.shuffle(question_order)
        submission.raw_answers["_question_order"] = question_order
        submission.save(update_fields=["raw_answers"])
        request.session["question_order"] = question_order

    if question_index >= len(question_order):
        return render(request, "cbt/exam_ended.html", {
            "exam": exam,
            "student": student,
        })

    question_id = question_order[question_index]
    question = get_object_or_404(CBTQuestion, id=question_id)

    # ------------------ QUESTION TEXT / DIAGRAM / EQUATION ------------------
    question_data = {
        "text": question.text or "",
        "equation": question.equation or "",
        "diagram": getattr(question, "diagram", None),
    }




    # ------------------ QUESTION & SHUFFLE OPTIONS ------------------
    question_id = question.id
    shuffle_key = f"_shuffle_opts_{question_id}"
    correct_letter_key = f"_correct_letter_{question_id}"

# Get previously shuffled options (if student reloads page)
    shuffled_opts = submission.raw_answers.get(shuffle_key)

    

# 🔥 If old structure (no diagram key), rebuild
    if shuffled_opts and (
        "diagram" not in shuffled_opts[0] or
        "equation" not in shuffled_opts[0]
    ):
        shuffled_opts = None

    if not shuffled_opts:


        option_pool = [
            {
                "text": question.option_a,
                "equation":question.option_a_equation,
                "diagram": question.option_a_diagram.url if question.option_a_diagram else None,
                "is_correct": question.correct_option == "A",
            },
            {
                "text": question.option_b,
                "equation": question.option_b_equation,
                "diagram": question.option_b_diagram.url if question.option_b_diagram else None,
                "is_correct": question.correct_option == "B",
            },
            {
                "text": question.option_c,
                "equation":question.option_c_equation,
                "diagram": question.option_c_diagram.url if question.option_c_diagram else None,
                "is_correct": question.correct_option == "C",
            },
            {
                "text": question.option_d,
                "equation": question.option_d_equation,
                "diagram": question.option_d_diagram.url if question.option_d_diagram else None,
                "is_correct": question.correct_option == "D",
            },
        ]



    # Remove empty options
        option_pool = [
            opt for opt in option_pool
            if (
                (opt["text"] and opt["text"].strip())
                or opt.get("equation")
                or opt.get("diagram")
            )
        ]

    # Shuffle options
        import random
        random.shuffle(option_pool)
        shuffled_opts = option_pool

    # Save shuffled options in submission
        submission.raw_answers[shuffle_key] = shuffled_opts

    # Determine correct letter AFTER shuffle
        for i, opt in enumerate(shuffled_opts):
            if opt["is_correct"]:
                submission.raw_answers[correct_letter_key] = ["A", "B", "C", "D"][i]
                break

        submission.save(update_fields=["raw_answers"])

# Build final options list for template
    options = [
        {
            "label": label,
            "text": opt["text"],
            "equation": opt["equation"],
            "diagram": opt.get("diagram"),
                
        }
        for label, opt in zip(["A", "B", "C", "D"], shuffled_opts)
    ]


    # ------------------ HANDLE ANSWER ------------------
    if request.method == "POST":
        selected_option = request.POST.get("answer")
        if selected_option:
            submission.raw_answers[str(question.id)] = selected_option
            submission.save(update_fields=["raw_answers"])

    # ---------------- CHECK UNANSWERED QUESTIONS ----------------
        unanswered_indices = [
            i for i, q_id in enumerate(question_order) if str(q_id) not in submission.raw_answers
        ]

        if unanswered_indices:
            # Go to next unanswered question AFTER current index
            next_unanswered = None
            for idx in unanswered_indices:
                if idx > question_index:
                    next_unanswered = idx
                    break
            if next_unanswered is None:
                # If none after current, go to first unanswered
                next_unanswered = unanswered_indices[0]

            return redirect("cbt:take_exam", exam_id=exam.id, question_index=next_unanswered)
        else:
            # All questions answered → redirect to submit page
            return redirect("cbt:submit_exam", exam_id=exam.id)


    # ------------------ PROGRESS ------------------
    progress = int((question_index + 1) / len(question_order) * 100)

    # ------------------ EXAM START TIME ------------------
    exam_start_time = request.session.get("exam_start_time") or submission.raw_answers.get("_exam_start_time")

    if not exam_start_time:
        exam_start_time = int(timezone.now().timestamp())
        request.session["exam_start_time"] = exam_start_time
        submission.raw_answers["_exam_start_time"] = exam_start_time
        submission.save(update_fields=["raw_answers"])
    else:
        if isinstance(exam_start_time, str):
            from django.utils.dateparse import parse_datetime
            dt = parse_datetime(exam_start_time)
            if dt:
                exam_start_time = int(dt.timestamp())
                request.session["exam_start_time"] = exam_start_time

        exam_start_time = int(exam_start_time)

    time_limit = exam.duration_minutes * 60
     

    selected_answer = submission.raw_answers.get(str(question.id))
    return render(request, "cbt/take_exam.html", {
        "exam": exam,
        "question": question,
        "question_data": question_data,
        "options": options,
        "selected_answer": selected_answer,
        "question_index": question_index,
        "current_question_number": question_index + 1,
        "total_questions": len(question_order),
        "progress": progress,
        "time_limit": time_limit,
        "exam_start_time": exam_start_time,
        "student": student,
        "application": application,
        "admission_mode": exam.exam_type == "admission",
    })




# --------------------------------------
# ⚙️ AJAX Save Answer
# --------------------------------------
@portal_required("cbt")
@csrf_exempt
@login_required
def ajax_save_answer(request):
    if request.method == "POST":
        exam_id = request.POST.get("exam_id")
        question_id = request.POST.get("question_id")
        answer = request.POST.get("answer")

        student = getattr(request.user, 'student_profile', None) or getattr(request.user, 'student', None)
        if not student:
            return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)

        try:
            exam = CBTExam.objects.get(id=exam_id)
            question = CBTQuestion.objects.get(id=question_id, exam=exam)
        except (CBTExam.DoesNotExist, CBTQuestion.DoesNotExist):
            return JsonResponse({"status": "error", "message": "Invalid question or exam"}, status=404)

        submission, _ = CBTSubmission.objects.get_or_create(student=student, exam=exam)

        if submission.completed_on:
            return JsonResponse({"status": "error", "message": "Exam already submitted"}, status=400)

        submission.raw_answers[str(question.id)] = answer
        submission.save(update_fields=["raw_answers"])
        return JsonResponse({"status": "success", "saved": True})

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


# --------------------------------------
# 🏁 Submit Exam
# --------------------------------------
# --------------------------------------
# 🏁 Submit Exam (Now Handles Reshuffled Options Correctly)
# --------------------------------------
@portal_required("cbt")
@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(CBTExam, id=exam_id)
    if exam.exam_type == "admission":
    
        application = get_object_or_404(
            AdmissionApplication,
            id=request.session["admission_application_id"]
            )
    
        submission = CBTSubmission.objects.filter(
            admission_candidate=application,
            exam=exam
        ).first()
    
    else:
    
        student = getattr(request.user, "student_profile", None) or getattr(request.user, "student", None)
    
        if not student:
            return HttpResponseForbidden(...)
    
        submission = CBTSubmission.objects.filter(
            student=student,
            exam=exam
        ).first()
    if not submission:
        return redirect("cbt:start_exam_page", exam_id=exam.id)

    # Stop if already submitted
    if submission.completed_on:
        return redirect("cbt:student_exam_result", exam_id=exam.id)

    correct_count = 0
    wrong_count = 0
    attempted = 0
    total_questions = exam.questions.count()

    for question in exam.questions.all():
        qid = str(question.id)
        student_choice = submission.raw_answers.get(qid)  # 'A', 'B', 'C', 'D'
        if not student_choice:
            continue

        attempted += 1

        # ✅ FIRST: try locked correct letter (most reliable)
        correct_letter = submission.raw_answers.get(f"_correct_letter_{question.id}")

        # 🔁 FALLBACK: your original logic (UNCHANGED)
        if not correct_letter:
            shuffle_key = f"_shuffle_text_{question.id}"
            shuffled_texts = submission.raw_answers.get(shuffle_key)

            if not shuffled_texts:
                shuffled_texts = [
                    question.option_a,
                    question.option_b,
                    question.option_c,
                    question.option_d,
                ]

            letter_to_text = {
                "A": shuffled_texts[0],
                "B": shuffled_texts[1],
                "C": shuffled_texts[2],
                "D": shuffled_texts[3],
            }

            correct_text = getattr(
                question,
                f"option_{question.correct_option.lower()}",
                None
            )

            for letter, text in letter_to_text.items():
                if (
                    text
                    and correct_text
                    and text.strip().lower() == correct_text.strip().lower()
                ):
                    correct_letter = letter
                    break

        # Final comparison
        if student_choice == correct_letter:
            correct_count += 1
        else:
            wrong_count += 1

    percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    status = "Pass" if percentage >= 50 else "Fail"

    submission.score = correct_count
    submission.total_questions = total_questions
    submission.correct_answers = correct_count
    submission.wrong_answers = wrong_count
    submission.percentage = round(percentage, 2)
    submission.status = status
    submission.completed_on = timezone.now()
    submission.save()

    # ============================================
# ADMISSION CBT INTEGRATION
# ============================================
   # ============================================
# ADMISSION CBT INTEGRATION
# ============================================

    if exam.exam_type == "admission":

        application = submission.admission_candidate

        application.exam_completed = True
        application.exam_score = submission.percentage

        application.status = (
            "passed"
            if submission.percentage >= application.exam_pass_mark
            else "failed"
        )

        application.save()

    return redirect("cbt:student_exam_result", exam_id=exam.id)


# --------------------------------------
#


# --------------------------------------
# 📊 Student Exam Result (Accurate with Reshuffling)
# --------------------------------------
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CBTExam, CBTSubmission
from students.models import Student
from results.utils import wrap_latex
from django.http import HttpResponseForbidden

@portal_required("cbt")
@login_required
def student_exam_result(request, exam_id):
    exam = get_object_or_404(CBTExam, id=exam_id)

    student = getattr(request.user, "student_profile", None) or getattr(request.user, "student", None)

# Find submission depending on exam type
    if exam.exam_type == "admission":

        application = get_object_or_404(
            AdmissionApplication,
            id=request.session.get("admission_application_id")
        )

        submission = get_object_or_404(
            CBTSubmission,
            exam=exam,
            admission_candidate=application
        )

        school = application.school

    else:

        if not student:
            return HttpResponseForbidden(
                "You are not registered as a student."
            )

        submission = get_object_or_404(
            CBTSubmission,
            exam=exam,
            student=student
        )

        school = student.school


    school_logo_url = (
        school.logo.url
        if school and school.logo
        else None
    )
    answers = submission.raw_answers or {}

    total_questions = exam.questions.count()
    attempted = 0
    correct_count = 0
    question_map = []

    for q in exam.questions.all():
        qid = str(q.id)

        selected = answers.get(qid)
        correct = answers.get(f"_correct_letter_{qid}")
        shuffled_opts = answers.get(f"_shuffle_opts_{qid}")

        # Build structured options (LIKE take_exam)
        if shuffled_opts:
            options = [
                {
                    "label": label,
                    "text": opt.get("text"),
                    "equation": opt.get("equation"),
                    "diagram": opt.get("diagram"),
                }
                for label, opt in zip(["A", "B", "C", "D"], shuffled_opts)
            ]
        else:
            options = [
                {"label": "A", "text": q.option_a, "equation": None, "diagram": getattr(q, "diagram_a", None)},
                {"label": "B", "text": q.option_b, "equation": None, "diagram": getattr(q, "diagram_b", None)},
                {"label": "C", "text": q.option_c, "equation": None, "diagram": getattr(q, "diagram_c", None)},
                {"label": "D", "text": q.option_d, "equation": None, "diagram": getattr(q, "diagram_d", None)},
            ]

        if selected:
            attempted += 1
            if selected == correct:
                correct_count += 1

        question_map.append({
            "question": q,
            "selected": selected,
            "correct": correct,
            "options": options,
            "marks": q.marks,
        })

    wrong_count = attempted - correct_count
    percentage = round((correct_count / total_questions) * 100, 2) if total_questions else 0
    status = "Pass" if percentage >= exam.pass_mark else "Fail"

    submission.score = correct_count
    submission.total_questions = total_questions
    submission.correct_answers = correct_count
    submission.wrong_answers = wrong_count
    submission.percentage = percentage
    submission.status = status


    if submission.admission_candidate:

        application = submission.admission_candidate

        application.exam_completed = True

        application.exam_score = percentage


        if percentage >= exam.pass_mark:

            application.status = "passed"

        else:

            application.status = "failed"


        application.save()


    submission.save(update_fields=[
        "score", "total_questions", "correct_answers",
        "wrong_answers", "percentage", "status"
    ])

    return render(request, "cbt/student_exam_result.html", {
        "exam": exam,
        "submission": submission,
        "student": student,
        "application": application if exam.exam_type == "admission" else None,
        "admission_mode": exam.exam_type == "admission",
        "school": school,
        "school_logo_url": school_logo_url,
        "question_map": question_map,
        "total_questions": total_questions,
        "attempted": attempted,
        "correct": correct_count,
        "wrong": wrong_count,
        "percentage": percentage,
        "status": status,
    })


from django.core.exceptions import PermissionDenied



@login_required
def student_submission_detail(request, submission_id):

    submission = get_object_or_404(
        CBTSubmission.objects.select_related(
            "student",
            "exam",
            "admission_candidate"
        ),
        id=submission_id
    )


    # Permission check
    if submission.student:

        if submission.student.user != request.user:
            raise PermissionDenied(
                "You cannot view this submission."
            )

        school = submission.student.school


    elif submission.admission_candidate:

        if request.session.get("admission_application_id") != submission.admission_candidate.id:
            raise PermissionDenied(
                "You cannot view this submission."
            )

        school = submission.admission_candidate.school


    else:
        raise PermissionDenied(
            "Invalid submission."
        )


    school_name = getattr(school, "name", "")
    school_motto = getattr(school, "motto", "")
    school_logo_url = getattr(
        school.logo,
        "url",
        None
    ) if school and school.logo else None

    # Answers
    answers = submission.raw_answers or {}

    # Preserve answered order
    answered_ids = [int(k) for k in answers.keys() if str(k).isdigit()]
    questions = list(submission.exam.questions.filter(id__in=answered_ids))
    questions.sort(key=lambda q: answered_ids.index(q.id))

    # Append unanswered questions
    unanswered = submission.exam.questions.exclude(id__in=answered_ids)
    questions.extend(unanswered)

    # Build question map
    question_map = []
    for q in questions:
        qid = str(q.id)
        selected = answers.get(qid)
        correct = answers.get(f"_correct_letter_{qid}")
        shuffled_opts = answers.get(f"_shuffle_opts_{qid}")

        if shuffled_opts:
            options = [
                {
                    "label": label,
                    "text": opt.get("text"),
                    "equation": opt.get("equation"),
                    "diagram": opt.get("diagram"),
                }
                for label, opt in zip(["A", "B", "C", "D"], shuffled_opts)
            ]
        else:
            options = []
            for label in ["A", "B", "C", "D"]:
                options.append({
                    "label": label,
                    "text": getattr(q, f"option_{label.lower()}"),
                    "equation": normalize_latex(getattr(q, f"option_{label.lower()}_equation")),
                    "diagram": getattr(q, f"option_{label.lower()}_diagram").url if getattr(q, f"option_{label.lower()}_diagram") else None,
                })

        question_map.append({
            "question": q,
            "selected": selected,
            "correct": correct,
            "options": options,
            "marks": getattr(q, "marks", 1),  # optional, if you track marks
        })

    return render(request, "cbt/student_submission_detail.html", {
        "submission": submission,
        "exam": submission.exam,
        "question_map": question_map,
        "school": school,
        "school_name": school_name,
        "school_motto": school_motto,
        "school_logo_url": school_logo_url,
    })




# ============================================
# ADMISSION CBT START
# ============================================

@portal_required("cbt")
@login_required
def start_admission_exam(request, exam_id):

    exam = get_object_or_404(
        CBTExam,
        id=exam_id,
        exam_type="admission"
    )


    # Ensure candidate read instructions first
    if not request.session.get(
        "exam_instruction_viewed"
    ):
        return redirect(
            "cbt:start_exam_page",
            exam_id=exam.id
        )


    application = get_object_or_404(
        AdmissionApplication,
        id=request.session.get(
            "admission_application_id"
        )
    )


    submission = CBTSubmission.objects.filter(
        admission_candidate=application,
        exam=exam
    ).first()

# ============================================
# PREVIOUSLY COMPLETED
# ============================================

    if submission and submission.completed_on:

        return render(
            request,
            "tis_website/public/exam_not_available.html",
            {
                "application": application,
                "exam": exam,
                "submission": submission,
                "reason": "already_completed",
            },
        )

# ============================================
# CREATE SUBMISSION IF FIRST ATTEMPT
# ============================================

    if not submission:

        submission = CBTSubmission.objects.create(
            admission_candidate=application,
            exam=exam
        )


    question_order = list(
        exam.questions.values_list(
            "id",
            flat=True
        )
    )

    random.shuffle(question_order)


    exam_start_time = timezone.now().isoformat()


    submission.raw_answers["_question_order"] = question_order
    submission.raw_answers["_exam_start_time"] = exam_start_time

    submission.save(
        update_fields=[
            "raw_answers"
        ]
    )


    request.session["question_order"] = question_order
    request.session["exam_start_time"] = exam_start_time


    # remove instruction flag after starting
    request.session.pop(
        "exam_instruction_viewed",
        None
    )


    return redirect(
        "cbt:take_exam",
        exam_id=exam.id,
        question_index=0
    )