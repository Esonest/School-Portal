from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import School, Teacher
from students.models import Student
from results.models import Score
from results.utils import SESSION_CHOICES

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)

    # ✅ NEW FIELDS
    session = models.CharField(max_length=20, choices=SESSION_CHOICES, null=True, blank=True)
    term = models.CharField(max_length=1, choices=Score.TERM_CHOICES, null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    remarks = models.TextField(blank=True, null=True)

    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_marked"
    )

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date']

    def save(self, *args, **kwargs):
        # Auto assign school
        if not self.school_id and self.student:
            self.school = self.student.school

        # ✅ Auto-fill session/term if missing
        if not self.session or not self.term:
            latest_score = self.student.scores.order_by('-id').first()
            if latest_score:
                self.session = latest_score.session
                self.term = latest_score.term

        super().save(*args, **kwargs)