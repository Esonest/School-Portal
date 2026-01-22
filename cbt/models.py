from django.db import models
from django.utils import timezone
from students.models import Student, SchoolClass
from accounts.models import School, Teacher
from results.models import Subject
import random
from ckeditor.fields import RichTextField
from results.utils import normalize_latex, normalize_latex_in_html, wrap_latex





# -------------------------
# EXAM MODEL
# -------------------------
class CBTExam(models.Model):
    TERM_CHOICES = [
        ('1', 'Term 1'),
        ('2', 'Term 2'),
        ('3', 'Term 3'),
    ]

    title = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, default='', related_name='cbt_exams')
    created_by = models.ForeignKey(Teacher, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_exams')

    session = models.CharField(max_length=20, default='')
    term = models.CharField(max_length=1, choices=TERM_CHOICES, default='')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    active = models.BooleanField(default=False)

    class Meta:
        verbose_name = "CBT Exam"
        verbose_name_plural = "CBT Exams"
        db_table = "CBTExam"

    def __str__(self):
        return f"{self.title} - {self.subject.name} ({self.session}, Term {self.term})"

    def is_active(self):
        now = timezone.now()
        return self.active and self.start_time <= now <= self.end_time


# -------------------------
# QUESTION MODEL
# -------------------------
import random
from django.db import models

class CBTQuestion(models.Model):
    exam = models.ForeignKey(CBTExam, on_delete=models.CASCADE, related_name='questions')
    text = RichTextField(config_name='equation_only')
    equation = models.TextField(
        blank=True,
        help_text="Raw LaTeX only, e.g. x^2 + 4x + 4 = 0"
    )

    option_a = models.CharField(max_length=400)
    option_b = models.CharField(max_length=400)
    option_c = models.CharField(max_length=400, blank=True)
    option_d = models.CharField(max_length=400, blank=True)

    correct_option = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    )
    marks = models.IntegerField(default=1)

    class Meta:
        db_table = "CBTQuestion"

    def get_shuffled_options(self):
        """
        Returns a shuffled list of (label, text).
        Labels remain original (A/B/C/D) so marking stays correct.
        """
        options = [
            ('A', self.option_a),
            ('B', self.option_b),
            ('C', self.option_c),
            ('D', self.option_d),
        ]

        # remove empty options
        options = [(label, text) for label, text in options if text and text.strip()]

        random.shuffle(options)
        return options
    

    def save(self, *args, **kwargs):
        # -------------------------------
        # PERMANENT FIX: Store raw LaTeX only
        # -------------------------------
        if self.text:
            self.text = self.text.strip()
        if self.equation:
            self.equation = self.equation.strip()  # <-- no \( ... \)
        self.option_a = self.option_a.strip() if self.option_a else ""
        self.option_b = self.option_b.strip() if self.option_b else ""
        self.option_c = self.option_c.strip() if self.option_c else ""
        self.option_d = self.option_d.strip() if self.option_d else ""

        super().save(*args, **kwargs) 

    def __str__(self):
        return f"Q{self.id} - {self.exam.title}"


class Topic(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="topics"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="topics"
    )
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ("school", "subject", "name")
        ordering = ["name"]

     

    def __str__(self):
        return self.name
# -------------------------
# QUESTION BANK (REPOSITORY)
# -------------------------
class QuestionBank(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="question_bank"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="question_bank"
    )
    created_by = models.ForeignKey(
        Teacher,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_questions"
    )

    # Optional: link to class, term, and session
    school_class = models.ForeignKey(
        "students.SchoolClass",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="question_bank"
    )
    term = models.CharField(
        max_length=1,
        choices=[('1', 'Term 1'), ('2', 'Term 2'), ('3', 'Term 3')],
        blank=True
    )
    session = models.CharField(
        max_length=20,
        blank=True
    )

    topic = models.ForeignKey(
        Topic,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="questions"
    )

    text = RichTextField(config_name='equation_only')

    equation = models.TextField(
        blank=True,
        help_text="Raw LaTeX only, e.g. x^2 + 4x + 4 = 0"
    )

    option_a = models.CharField(max_length=400)
    option_b = models.CharField(max_length=400)
    option_c = models.CharField(max_length=400, blank=True)
    option_d = models.CharField(max_length=400, blank=True)

    correct_option = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    )
    marks = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "QuestionBank"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # Ensure LaTeX is wrapped for MathJax
        if self.text:
            # Wrap any raw LaTeX with $...$ if not already wrapped
            self.text = wrap_latex(self.text)  

            # Normalize raw LaTeX fields for options
        self.equation = normalize_latex(self.equation)
        self.option_a = normalize_latex(self.option_a)
        self.option_b = normalize_latex(self.option_b)
        self.option_c = normalize_latex(self.option_c)
        self.option_d = normalize_latex(self.option_d)

        super().save(*args, **kwargs)
  

    def __str__(self):
        return f"{self.subject.name} - Q{self.id}"




# -------------------------
# SUBMISSION MODEL
# -------------------------
class CBTSubmission(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(CBTExam, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, default='', related_name='cbt_submissions')

    score = models.FloatField(default=0)
    started_on = models.DateTimeField(default=timezone.now)
    completed_on = models.DateTimeField(null=True, blank=True)
    raw_answers = models.JSONField(default=dict)  # {"question_id": "A"}

    # For analysis
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    wrong_answers = models.PositiveIntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    status = models.CharField(max_length=10, default='Pending')

    class Meta:
        verbose_name = "CBT Submission"
        verbose_name_plural = "CBT Submissions"
        unique_together = ('student', 'exam')
        db_table = "CBTSubmission"

    def save(self, *args, **kwargs):
        if not self.school_id:
            self.school = self.student.school
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name()} - {self.exam.title}"






