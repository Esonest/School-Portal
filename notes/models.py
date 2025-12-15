from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import School,Teacher
from students.models import Student, SchoolClass
from results.models import Subject


# -----------------------------
# CATEGORY MODEL
# -----------------------------
class NoteCategory(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE,default='', related_name='note_categories')
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.school.name})"

    class Meta:
        unique_together = ('school', 'name')
        ordering = ['name']
        verbose_name = "Note Category"
        verbose_name_plural = "Note Categories"


# -----------------------------
# LESSON NOTE MODEL
# -----------------------------
class LessonNote(models.Model):
    VISIBILITY_CHOICES = (
        ('all', 'All Students'),
        ('classes', 'Specific Classes'),
        ('private', 'Only Me (Teacher)'),
    )

    TERM_CHOICES = [
        ('1', 'Term 1'),
        ('2', 'Term 2'),
        ('3', 'Term 3'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, default='', related_name='lesson_notes')
    title = models.CharField(max_length=255)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='lesson_notes')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(NoteCategory, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField(blank=True)
    session = models.CharField(max_length=20, blank=True, null=True)
    term = models.CharField(max_length=1, choices=TERM_CHOICES, blank=True, null=True)
    file = models.FileField(upload_to='lesson_notes/', null=True, blank=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='all')
    classes = models.ManyToManyField(SchoolClass, blank=True, help_text="If visibility is 'Specific Classes', choose classes.")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    publish_date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ('-publish_date', '-created_on')
        verbose_name = "Lesson Note"
        verbose_name_plural = "Lesson Notes"

    def __str__(self):
        return f"{self.title} ({self.subject}) - {self.school.name}"

    def save(self, *args, **kwargs):
        if not self.school_id and self.teacher:
            self.school = self.teacher.school
        super().save(*args, **kwargs)


# -----------------------------
# LESSON NOTE SUBMISSION
# -----------------------------
class LessonNoteSubmission(models.Model):
    STATUS = (
        ('submitted', 'Submitted'),
        ('draft', 'Draft'),
        ('graded', 'Graded'),
        ('late', 'Late'),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, default='', related_name='note_submissions')
    note = models.ForeignKey(LessonNote, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='note_submissions')
    submitted_on = models.DateTimeField(auto_now_add=True)
    text = models.TextField(blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    graded_on = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='submitted')

    class Meta:
        unique_together = ('note', 'student')
        ordering = ['-submitted_on']
        verbose_name = "Lesson Note Submission"
        verbose_name_plural = "Lesson Note Submissions"

    def __str__(self):
        return f"{self.note.title} - {self.student}"

    def save(self, *args, **kwargs):
        if not self.school_id and self.student:
            self.school = self.student.school
        super().save(*args, **kwargs)

    def mark_graded(self, score, feedback, grader):
        self.score = score
        self.feedback = feedback
        self.graded_by = grader
        self.graded_on = timezone.now()
        self.status = 'graded'
        self.save()


# -----------------------------
# SUBMISSION FILES
# -----------------------------
class SubmissionFile(models.Model):
    submission = models.ForeignKey(LessonNoteSubmission, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='notes/submissions/')
    uploaded_on = models.DateTimeField(auto_now_add=True)

    def filename(self):
        import os
        return os.path.basename(self.file.name)

    def __str__(self):
        return f"File for {self.submission}"
