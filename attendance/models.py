from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import School, Teacher
from students.models import Student


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, default='', related_name='attendances')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    remarks = models.TextField(blank=True, null=True)
    marked_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendances_marked'
    )

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date']
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"

    def __str__(self):
        return f"{self.student.full_name()} - {self.date} ({self.status})"

    def save(self, *args, **kwargs):
        # Automatically assign school if not manually set
        if not self.school_id and self.student:
            self.school = self.student.school
        super().save(*args, **kwargs)
