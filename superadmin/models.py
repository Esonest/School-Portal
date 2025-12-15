from django.db import models
from django.db.models import UniqueConstraint
from django.conf import settings
from students.models import Student, SchoolClass
from accounts.models import School, Teacher
import secrets


class SchoolPortalSetting(models.Model):
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name="portal_settings"
    )

    # Core portals
    cbt_enabled = models.BooleanField(default=True)
    results_enabled = models.BooleanField(default=True)
    lesson_note_enabled = models.BooleanField(default=True)
    attendance_enabled = models.BooleanField(default=True)
    finance_enabled = models.BooleanField(default=True)

    # User management
    teachers_enabled = models.BooleanField(default=True)
    students_enabled = models.BooleanField(default=True)

    # Academics
    assignments_enabled = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school.name} Portal Settings"
