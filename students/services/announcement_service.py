from students.models import Student


def get_announcement_recipients(
    announcement
):

    students = Student.objects.filter(
        school=announcement.school,
        is_active=True
    )

    if "class" in announcement.targets:

        students = students.filter(
            school_class__in=
            announcement.school_classes.all()
        )

    if "student" in announcement.targets:

        students = students.filter(
            id__in=
            announcement.students.values_list(
                "id",
                flat=True
            )
        )

    return students.distinct()