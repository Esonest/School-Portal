import random
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from .models import CBTExam, CBTQuestion, CBTSubmission
from students.models import Student
from results.utils import portal_required


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
    exam = get_object_or_404(CBTExam, id=exam_id)
    student = getattr(request.user, "student_profile", None) or getattr(request.user, "student", None)
    if not student:
        return HttpResponseForbidden("You must be logged in as a student.")

    # check if student already took exam
    submission = CBTSubmission.objects.filter(student=student, exam=exam).first()
    already_taken = submission and submission.completed_on is not None

    return render(request, "cbt/start_exam.html", {
        "exam": exam,
        "student": student,
        "already_taken": already_taken,
        "school": getattr(student, "school", None),
    })



# --------------------------------------
# 🧠 Start Exam Action (Single Attempt Only)
# --------------------------------------
@portal_required("cbt")
@login_required
def start_exam(request, exam_id):
    exam = get_object_or_404(CBTExam, id=exam_id)
    student = getattr(request.user, "student_profile", None) or getattr(request.user, "student", None)

    if not student:
        return HttpResponseForbidden("You must be logged in as a student.")

    now = timezone.now()
    if not (exam.start_time <= now <= exam.end_time):
        return HttpResponseForbidden("This exam is not active at the moment.")

    # 🚫 Check if already completed
    submission = CBTSubmission.objects.filter(student=student, exam=exam).first()
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
    submission = CBTSubmission.objects.create(student=student, exam=exam)

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
    student = getattr(request.user, "student_profile", None) or getattr(request.user, "student", None)

    if not student:
        return HttpResponseForbidden("You must be logged in as a student to take this exam.")

    submission = CBTSubmission.objects.filter(student=student, exam=exam).first()
    if not submission:
        return redirect("cbt:start_exam_page", exam_id=exam.id)

    # Prevent retake after completion
    if submission.completed_on:
        return redirect("cbt:exam_result", exam_id=exam.id)

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
        return redirect("cbt:submit_exam", exam_id=exam.id)

    question_id = question_order[question_index]
    question = get_object_or_404(CBTQuestion, id=question_id)

    # ------------------ SHUFFLE OPTIONS (TEXT ONLY) ------------------
    shuffle_key = f"_shuffle_text_{question_id}"
    correct_letter_key = f"_correct_letter_{question_id}"

    shuffled_texts = submission.raw_answers.get(shuffle_key)

    if not shuffled_texts:
        option_texts = [
            question.option_a,
            question.option_b,
            question.option_c,
            question.option_d,
        ]
        random.shuffle(option_texts)
        shuffled_texts = option_texts

        # ✅ SAVE SHUFFLED TEXTS
        submission.raw_answers[shuffle_key] = shuffled_texts

        # ✅ DETERMINE & SAVE CORRECT LETTER (BASED ON SHUFFLE)
        correct_text = getattr(
            question,
            f"option_{question.correct_option.lower()}",
            None
        )

        if correct_text in shuffled_texts:
            correct_index = shuffled_texts.index(correct_text)
            correct_letter = ["A", "B", "C", "D"][correct_index]
            submission.raw_answers[correct_letter_key] = correct_letter

        submission.save(update_fields=["raw_answers"])

    options = [
        ("A", shuffled_texts[0]),
        ("B", shuffled_texts[1]),
        ("C", shuffled_texts[2]),
        ("D", shuffled_texts[3]),
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

    return render(request, "cbt/take_exam.html", {
        "exam": exam,
        "question": question,
        "options": options,
        "question_index": question_index,
        "current_question_number": question_index + 1,
        "total_questions": len(question_order),
        "progress": progress,
        "time_limit": time_limit,
        "exam_start_time": exam_start_time,
        "student": student,
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
    student = getattr(request.user, "student_profile", None) or getattr(request.user, "student", None)

    if not student:
        return HttpResponseForbidden("You must be logged in as a student to submit this exam.")

    submission = CBTSubmission.objects.filter(student=student, exam=exam).first()
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

    return redirect("cbt:student_exam_result", exam_id=exam.id)


# --------------------------------------
#


# --------------------------------------
# 📊 Student Exam Result (Accurate with Reshuffling)
# --------------------------------------
@portal_required("cbt")
@login_required
def student_exam_result(request, exam_id):
    exam = get_object_or_404(CBTExam, id=exam_id)

    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return render(request, "cbt/student_result.html", {
            "error": "You are not registered as a student."
        })
    
    school = getattr(student, "school", None)
    school_logo_url = getattr(school.logo, 'url', None) if school and school.logo else None

    submission = get_object_or_404(CBTSubmission, exam=exam, student=student)
    answers = submission.raw_answers or {}

    total_questions = exam.questions.count()
    attempted = 0
    correct = 0

    for question in exam.questions.all():
        qid = str(question.id)
        student_choice = answers.get(qid)
        if not student_choice:
            continue

        attempted += 1

        # Retrieve reshuffled texts
        shuffle_key = f"_shuffle_text_{question.id}"
        shuffled_texts = answers.get(shuffle_key)
        if not shuffled_texts:
            shuffled_texts = [question.option_a, question.option_b, question.option_c, question.option_d]

        letter_to_text = {
            "A": shuffled_texts[0],
            "B": shuffled_texts[1],
            "C": shuffled_texts[2],
            "D": shuffled_texts[3],
        }

        correct_text = getattr(question, f"option_{question.correct_option.lower()}", None)
        correct_letter = None
        for letter, text in letter_to_text.items():
            if text.strip().lower() == correct_text.strip().lower():
                correct_letter = letter
                break

        if student_choice == correct_letter:
            correct += 1

    wrong = attempted - correct
    percentage = round((correct / total_questions) * 100, 2) if total_questions > 0 else 0
    status = "Pass" if percentage >= 50 else "Fail"

    # Update record if needed
    submission.score = correct
    submission.total_questions = total_questions
    submission.correct_answers = correct
    submission.wrong_answers = wrong
    submission.percentage = percentage
    submission.status = status
    submission.save(update_fields=["score", "total_questions", "correct_answers", "wrong_answers", "percentage", "status"])

    return render(request, "cbt/student_exam_result.html", {
        "exam": exam,
        "submission": submission,
        "student": student,
        "total_questions": total_questions,
        "attempted": attempted,
        "correct": correct,
        "wrong": wrong,
        "percentage": percentage,
        "status": status,
        "school": submission.student.user.school,
        "school_logo_url": school_logo_url,
    })




from django.core.exceptions import PermissionDenied


@login_required
def student_submission_detail(request, submission_id):
    # assumes user has related Student object
    student = getattr(request.user, 'student', None)
    if not request.user.is_student_user:
        raise PermissionDenied("Only students can view this page.")
    
    school = getattr(student, "school", None)
    school_logo_url = getattr(school.logo, 'url', None) if school and school.logo else None

    submission = get_object_or_404(
        CBTSubmission.objects.select_related("student", "exam"),
        id=submission_id,
        student__user=request.user
    )

    answers = submission.raw_answers or {}

    answered_ids = [int(k) for k in answers.keys() if str(k).isdigit()]

    questions = list(submission.exam.questions.filter(id__in=answered_ids))
    questions.sort(key=lambda q: answered_ids.index(q.id))  # preserve answer order

    # append unanswered questions
    unanswered = submission.exam.questions.exclude(id__in=answered_ids)
    questions.extend(unanswered)

    # rebuild correct answers after shuffle
    correct_map = {}
    for q in questions:
        original = {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d}
        orig_text = original.get(q.correct_option, "").strip().lower()
        shuffled = answers.get(f"_shuffle_text_{q.id}", [])
        if not shuffled:
            correct_map[q.id] = q.correct_option
            continue
        shuffled_norm = [s.strip().lower() for s in shuffled]
        try:
            idx = shuffled_norm.index(orig_text)
            correct_map[q.id] = chr(65 + idx)
        except ValueError:
            correct_map[q.id] = q.correct_option

    context = {
        "submission": submission,
        "exam": submission.exam,
        "questions": questions,
        "answers": answers,
        "correct_map": correct_map,
        "school": submission.student.user.school,
        "school_logo_url": school_logo_url,

    }

    return render(request, "cbt/student_submission_detail.html", context)
