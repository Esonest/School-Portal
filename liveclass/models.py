import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


class LiveClass(models.Model):

    STATUS_CHOICES = (
        ("scheduled", "Scheduled"),
        ("live", "Live"),
        ("ended", "Ended"),
    )

    school = models.ForeignKey(
        "accounts.School",
        on_delete=models.CASCADE,
        related_name="live_classes"
    )

    subject = models.ForeignKey(
        "results.Subject",
        on_delete=models.CASCADE
    )

    class_room = models.ForeignKey(
        "students.SchoolClass",
        on_delete=models.CASCADE
    )

    teacher = models.ForeignKey(
        "accounts.Teacher",
        on_delete=models.CASCADE,
        related_name="live_classes"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    room_name = models.CharField(max_length=255, unique=True)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.room_name:
            self.room_name = f"{self.school.id}_{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    def update_status(self):
        now = timezone.now()

        if self.start_time <= now <= self.end_time:
            self.status = "live"
        elif now > self.end_time:
            self.status = "ended"
        else:
            self.status = "scheduled"

        super().save(update_fields=["status"])

    def __str__(self):
        return f"{self.title} - {self.school.name}"

class LiveClassAttendance(models.Model):
    live_class = models.ForeignKey(
        LiveClass,
        on_delete=models.CASCADE,
        related_name="attendances"
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="live_class_attendance"
    )

    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("live_class", "student")
        ordering = ["-joined_at"]

    def __str__(self):
        return f"{self.student} - {self.live_class.title}"
