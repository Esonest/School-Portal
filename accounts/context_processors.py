def global_school(request):
    user = request.user

    if not user.is_authenticated:
        return {}

    school = None

    try:
        # ✅ Detect school from all possible profiles
        if hasattr(user, 'student_profile'):
            school = user.student_profile.school

        elif hasattr(user, 'teacher_profile'):
            school = user.teacher_profile.school

        elif hasattr(user, 'school_admin_profile'):
            school = user.school_admin_profile.school

        elif hasattr(user, 'accountant_profile'):
            school = user.accountant_profile.school

        # fallback (if directly linked)
        elif hasattr(user, 'school'):
            school = user.school

    except Exception:
        school = None

    return {
        'school': school
    }