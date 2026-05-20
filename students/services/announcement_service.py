from students.models import Student


from django.db.models import Q


def get_announcement_recipients(
    announcement
):

    students = Student.objects.filter(
        school=announcement.school,
        is_active=True
    )

    if "all" in announcement.targets:
        return students.distinct()

    filters = Q()

    if "class" in announcement.targets:
        filters |= Q(
            school_class__in=
            announcement.school_classes.all()
        )

    if "student" in announcement.targets:
        filters |= Q(
            id__in=
            announcement.students.values_list(
                "id",
                flat=True
            )
        )

    if filters:
        students = students.filter(filters)

    return students.distinct()