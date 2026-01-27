from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import School  # already correct


class SchoolClass(models.Model):
    name = models.CharField(max_length=100)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="classes")

    class Meta:
        unique_together = ('name', 'school')  # ensures no duplicate class names within same school
        verbose_name_plural = "Classes"

    def __str__(self):
        return f"{self.name} - {self.school.name}"


# students/models.py
from django.db import models
from django.conf import settings
from accounts.models import School
from students.models import SchoolClass


class Student(models.Model):
    TERM_CHOICES = (
        ('1', 'Term 1'),
        ('2', 'Term 2'),
        ('3', 'Term 3'),
    )

    # -----------------------------
    # Core Identity
    # -----------------------------
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="student_profile",
        on_delete=models.CASCADE
    )

    admission_no = models.CharField(
        max_length=30,
        unique=True,
        db_index=True
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="students"
    )

    # -----------------------------
    # Academic Placement
    # -----------------------------
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        help_text="Current class of the student"
    )

    # Promotion tracking (does NOT affect current logic)
    promoted_from = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promoted_from_students"
    )

    promoted_to = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promoted_to_students"
    )

    session = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Current academic session"
    )

    term = models.CharField(
        max_length=1,
        choices=TERM_CHOICES,
        null=True,
        blank=True
    )

    # -----------------------------
    # Bio Data
    # -----------------------------
    dob = models.DateField(null=True, blank=True)

    gender = models.CharField(
        max_length=10,
        choices=(('M', 'Male'), ('F', 'Female')),
        null=True,
        blank=True
    )

    photo = models.ImageField(
        upload_to="student_photos/",
        null=True,
        blank=True
    )

    # -----------------------------
    # Paystack Virtual Account
    # -----------------------------
    paystack_customer_code = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Paystack customer code"
    )

    virtual_account_number = models.CharField(
        max_length=20,
        unique=True,      # ✅ REQUIRED
        db_index=True,    # ✅ FAST LOOKUP
        null=True,
        blank=True
    )


    virtual_account_name = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    virtual_bank_name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    virtual_bank_slug = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    va_verified_at = models.DateTimeField(null=True, blank=True)

    # -----------------------------
    # Access Control
    # -----------------------------
    is_result_blocked = models.BooleanField(default=False)

    block_reason = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    # -----------------------------
    # Meta
    # -----------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # -----------------------------
    # Helpers
    # -----------------------------
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    def has_virtual_account(self):
        return bool(self.virtual_account_number)

    def __str__(self):
        return f"{self.full_name()} ({self.admission_no})"



# cumulative result per student per session
class cumulative_result(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    session = models.CharField(max_length=20)
    total_first = models.FloatField(default=0)
    total_second = models.FloatField(default=0)
    total_third = models.FloatField(default=0)
    cumulative_average = models.FloatField(default=0)
    generated_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('student','session'),)

    def compute_from_results(self):
        from results.models import Result
        qs = Result.objects.filter(student=self.student, exam__session=self.session)
        # aggregate per term
        totals = {'first':0,'second':0,'third':0}
        counts = {'first':0,'second':0,'third':0}
        for r in qs:
            term = r.exam.term
            totals[term] += r.total_score
            counts[term] += 1
        self.total_first = totals['first']
        self.total_second = totals['second']
        self.total_third = totals['third']
        grand_total = sum(totals.values())
        grand_count = sum(counts.values()) or 1
        self.cumulative_average = grand_total / grand_count
        self.save()


class PromotionHistory(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="promotion_records"
    )

    # Session of the promotion e.g. 2024/2025
    session = models.CharField(max_length=20)

    # From which class → to which class
    old_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        related_name="promotions_old"
    )
    new_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        related_name="promotions_new"
    )

    # Auto timestamp
    promoted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name()} | {self.old_class} → {self.new_class} ({self.session})"

