from django.db import models
from django.db.models import UniqueConstraint
from django.conf import settings
from students.models import Student, SchoolClass
from accounts.models import School, Teacher
import secrets



# -------------------------
# SUBJECT MODEL
# -------------------------
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True,null=True,blank=True)
    exam_duration = models.IntegerField(default=30, help_text="Default duration in minutes")
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        default='',
        related_name='subjects'
    )

    class Meta:
        unique_together = ('name', 'school')
        verbose_name_plural = 'Subjects'

    def __str__(self):
        return f"{self.name} - {self.school.name}"
    

class ClassSubjectTeacher(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="subject_teachers")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="class_teachers")
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name="class_subjects")

    class Meta:
        unique_together = ('school_class', 'subject')
        verbose_name = "Class Subject Teacher"
        verbose_name_plural = "Class Subject Teachers"

    def __str__(self):
        return f"{self.school_class.name} - {self.subject.name} → {self.teacher}"




# results/models.py
from django.db import models
from django.db.models import UniqueConstraint

# results/models.py
 # adjust the import to your School model

from django.db import models

class GradeSetting(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE)

    # Store grades as JSON: {"A": 90, "B1": 85, "B2": 80, "C1": 75, "D": 60, "F": 0}
    grades = models.JSONField(default=dict)

    # Store per-grade comments for principal and teacher
    # Example: {"A": "Excellent work", "B": "Good effort", ...}
    grade_interpretations = models.JSONField(default=dict, blank=True)
    principal_comments = models.JSONField(default=dict, blank=True)
    teacher_comments = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.school.name} Grade Settings"




def grade_from_score_dynamic(score, school):
    from .models import GradeSetting
    settings, _ = GradeSetting.objects.get_or_create(school=school)

    # Sort grades descending by score to check highest first
    sorted_grades = sorted(settings.grades.items(), key=lambda x: x[1], reverse=True)

    for grade, min_score in sorted_grades:
        if score >= min_score:
            return grade
    return "F"



class ClassScoreSetting(models.Model):
    school_class = models.OneToOneField(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="score_setting"
    )
    ca_max = models.FloatField(default=40, help_text="Maximum score for CA")
    exam_max = models.FloatField(default=60, help_text="Maximum score for Exam")

    class Meta:
        verbose_name = "Class Score Setting"
        verbose_name_plural = "Class Score Settings"

    @property
    def uses_ca(self):
        """Return True if CA is enabled for this class."""
        return self.ca_max > 0

    def __str__(self):
        return f"{self.school_class.name} - CA {self.ca_max} / Exam {self.exam_max}"


class Score(models.Model):
    TERM_CHOICES = [('1', 'Term 1'), ('2', 'Term 2'), ('3', 'Term 3')]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="scores")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='scores')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, null=True,blank=True)
    ca = models.FloatField(default=0)
    exam = models.FloatField(default=0)
    session = models.CharField(max_length=20)
    term = models.CharField(max_length=1, choices=TERM_CHOICES)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='scores')
    teacher = models.ForeignKey(
        Teacher, null=True, blank=True, on_delete=models.SET_NULL, related_name='scores'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['student', 'subject', 'session', 'term'],
                name='unique_score_entry'
            )
        ]

    def total(self):
        """
        Returns total score using class-specific CA/Exam max.
        Ignores CA if CA is disabled.
        """
        try:
            setting = self.student.school_class.score_setting
            ca_max = setting.ca_max
            exam_max = setting.exam_max
        except ClassScoreSetting.DoesNotExist:
            ca_max = 40
            exam_max = 60

        exam_score = min(self.exam, exam_max)
        ca_score = min(self.ca, ca_max) if ca_max > 0 else 0

        return ca_score + exam_score

    @property
    def grade(self):
        """Return grade based on dynamic grading function"""
        return grade_from_score_dynamic(self.total(), self.school)

    def __str__(self):
        return f"{self.student} - {self.subject.name} ({self.session} Term {self.term})"









# -------------------------
# PSYCHOMOTOR
# -------------------------
class Psychomotor(models.Model):
    TERM_CHOICES = Score.TERM_CHOICES
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, default='', related_name='psychomotors')
    session = models.CharField(max_length=20)
    term = models.CharField(max_length=1, choices=TERM_CHOICES)

    neatness = models.PositiveSmallIntegerField(default=0)
    agility = models.PositiveSmallIntegerField(default=0)
    creativity = models.PositiveSmallIntegerField(default=0)
    sports = models.PositiveSmallIntegerField(default=0)
    handwriting = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'session', 'term'], name='unique_psychomotor_entry')
        ]

    def save(self, *args, **kwargs):
        if not self.school_id:
            self.school = self.student.school
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.student} Psychomotor ({self.session} Term {self.term})"


# -------------------------
# AFFECTIVE
# -------------------------
class Affective(models.Model):
    TERM_CHOICES = Score.TERM_CHOICES
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, default='', related_name='affectives')
    session = models.CharField(max_length=20)
    term = models.CharField(max_length=1, choices=TERM_CHOICES)

    punctuality = models.PositiveSmallIntegerField(default=0)
    cooperation = models.PositiveSmallIntegerField(default=0)
    behavior = models.PositiveSmallIntegerField(default=0)
    attentiveness = models.PositiveSmallIntegerField(default=0)
    perseverance = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'session', 'term'], name='unique_affective_entry')
        ]

    def save(self, *args, **kwargs):
        if not self.school_id:
            self.school = self.student.school
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} Affective ({self.session} Term {self.term})"


# -------------------------
# RESULT VERIFICATION
# -------------------------
class ResultVerification(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, default='', related_name='verifications')
    created_at = models.DateTimeField(auto_now_add=True)
    verification_token = models.CharField(max_length=128, unique=True, db_index=True)
    valid = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.verification_token:
            self.verification_token = secrets.token_urlsafe(32)
        if not self.school_id:
            self.school = self.student.school
        super().save(*args, **kwargs)


# -------------------------
# RESULT COMMENT
# -------------------------
class ResultComment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, default='', related_name='result_comments')
    term = models.CharField(max_length=5)
    session = models.CharField(max_length=20)
    is_locked = models.BooleanField(default=False)
    principal_comment = models.TextField()
    teacher_comment = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'term', 'session')

    def save(self, *args, **kwargs):
        if not self.school_id:
            self.school = self.student.school
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name()} - {self.term} - {self.session}"


from django.db import models

class SchoolGradeComment(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="grade_comments")
    grade = models.CharField(max_length=2)  # A, B, C, D, F
    comment_type = models.CharField(
        max_length=10,
        choices=(('principal', 'Principal'), ('teacher', 'Teacher'))
    )
    text = models.TextField(help_text="Use {name} to include student's name")
    interpretation = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional: Enter a grade interpretation like 'Excellent', 'Good', etc."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('school', 'grade', 'comment_type', 'text')

    def __str__(self):
        return f"{self.school.name} - {self.grade} - {self.comment_type}"



