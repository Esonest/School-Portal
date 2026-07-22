from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import School, Teacher  # central school model
from students.models import SchoolClass, Student
from results.models import Subject
from cloudinary_storage.storage import RawMediaCloudinaryStorage


User = settings.AUTH_USER_MODEL


# -------------------------
# ASSIGNMENT MODEL
# -------------------------
from django.db import models
from django.utils import timezone

from accounts.models import School, Teacher
from students.models import SchoolClass, Student
from results.models import Subject
from cloudinary_storage.storage import RawMediaCloudinaryStorage


class Assignment(models.Model):

    TERM_CHOICES = [
        ('1', 'Term 1'),
        ('2', 'Term 2'),
        ('3', 'Term 3'),
    ]


    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="assignments"
    )

    title = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )


    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignments_created"
    )


    classes = models.ManyToManyField(
        SchoolClass,
        blank=True,
        help_text="Choose classes this assignment applies to"
    )


    session = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )


    term = models.CharField(
        max_length=1,
        choices=TERM_CHOICES,
        blank=True,
        null=True
    )


    due_date = models.DateTimeField(
        null=True,
        blank=True
    )


    expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Assignment will disappear after this date."
    )


    max_score = models.PositiveIntegerField(
        default=100
    )


    is_active = models.BooleanField(
        default=True
    )


    published = models.BooleanField(
        default=True
    )


    file = models.FileField(
        storage=RawMediaCloudinaryStorage(),
        upload_to="assignments/files/",
        null=True,
        blank=True
    )


    created_on = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:
        ordering = [
            "-created_on"
        ]


    def __str__(self):

        return f"{self.title} - {self.school.name}"



    def is_expired(self):

        if self.expiry_date:

            return timezone.now() > self.expiry_date

        return False



    def is_available(self):

        return (
            self.is_active
            and self.published
            and not self.is_expired()
        )



    def is_overdue(self):

        return (
            self.due_date
            and timezone.now() > self.due_date
        )



    def student_count(self):

        return sum(
            c.student_set.count()
            for c in self.classes.all()
        )


# -------------------------
# SUBMISSION MODEL
# -------------------------
class AssignmentSubmission(models.Model):
    STATUS = (
        ('submitted', 'Submitted'),
        ('draft', 'Draft'),
        ('graded', 'Graded'),
        ('late', 'Late'),
    )

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    school = models.ForeignKey(School, on_delete=models.CASCADE, default='', related_name='assignment_submissions')

    submitted_on = models.DateTimeField(auto_now_add=True)
    text = models.TextField(blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_submissions'
    )
    graded_on = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='submitted')

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submitted_on']
        verbose_name = "Assignment Submission"
        verbose_name_plural = "Assignment Submissions"

    def __str__(self):
        return f"{self.assignment.title} - {self.student}"

    def mark_graded(self, score, feedback, grader):
        self.score = score
        self.feedback = feedback
        self.graded_by = grader
        self.graded_on = timezone.now()
        self.status = 'graded'
        self.save()

    def save(self, *args, **kwargs):
        if not self.school_id:
            self.school = self.assignment.school
        super().save(*args, **kwargs)


# -------------------------
# SUBMISSION FILES
# -------------------------
class SubmissionFile(models.Model):
    submission = models.ForeignKey(AssignmentSubmission, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='assignments/submissions/')
    uploaded_on = models.DateTimeField(auto_now_add=True)

    def filename(self):
        import os
        return os.path.basename(self.file.name)

    def __str__(self):
        return f"File for {self.submission}"
