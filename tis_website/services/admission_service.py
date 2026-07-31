from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from students.models import Student, SchoolClass
from accounts.models import SystemSetting

User = get_user_model()


def create_student_from_application(application):
    """
    Creates User + Student from an approved application.

    Returns:
        student,
        raw_password
    """

    # already created
    if application.student:
        return application.student, None

    password = get_random_string(8)

    username = application.application_number

    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=application.student_name,
        email=application.parent_email,
    )

    user.role = "student"
    user.is_student = True
    user.school = application.school

    # IMPORTANT
    # Login will only work after payment
    user.is_active = False

    user.save()

    school_class = SchoolClass.objects.filter(
        school=application.school,
        name__iexact=application.class_applying_for
    ).first()

    setting = SystemSetting.objects.first()

    current_session = ""
    current_term = ""

    if setting:
        current_session = setting.current_session
        current_term = setting.current_term

    student = Student.objects.create(

        user=user,

        school=application.school,

        admission_no=application.application_number,

        school_class=school_class,

        session=current_session,

        term=current_term,

        dob=application.date_of_birth,

        gender="M" if application.gender == "Male" else "F",

        parent_name=application.parent_name,

        parent_email=application.parent_email,

        parent_phone=application.parent_phone,

        photo=application.passport,

        is_active=False,

    )

    application.student = student

    application.save(update_fields=["student"])

    return student, password    