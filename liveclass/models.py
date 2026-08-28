from django.db import models
from django.utils import timezone


# models.py

class LiveClass(models.Model):
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

    camera_enabled = models.BooleanField(default=False)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("live", "Live"),
        ("ended", "Ended"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled"
    )

    room_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    # ✅ NEW FIELDS
    recording_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    recording_url = models.TextField(
        blank=True,
        null=True
    )

    recording_status = models.CharField(
        max_length=50,
        default="idle"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_time"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_time >= self.end_time:
            raise ValidationError(
                "End time must be after start time."
            )

    def update_status(self):
        now = timezone.now()

        new_status = (
            "live"
            if self.start_time <= now <= self.end_time
            else "ended"
            if now > self.end_time
            else "scheduled"
        )

        if self.status != new_status:
            self.status = new_status
            super().save(
                update_fields=["status"]
            )

    def __str__(self):
        return f"{self.title} ({self.class_room})"


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

    # ✅ Properly indented save method
    def save(self, *args, **kwargs):
        if self.left_at and self.joined_at:
            delta = self.left_at - self.joined_at
            self.duration_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.live_class.title}"


# models.py

class LiveClassWaiting(models.Model):
    live_class = models.ForeignKey(
        LiveClass,
        on_delete=models.CASCADE,
        related_name="waiting_list"
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="waiting_classes"
    )
    updated_at = models.DateTimeField(auto_now=True)
    approved = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)

    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("live_class", "student")
        ordering = ["requested_at"]

    def __str__(self):
        status = "Approved" if self.approved else "Waiting"
        return f"{self.student} → {self.live_class.title} ({status})"