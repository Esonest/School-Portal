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


class Student(models.Model):
    TERM_CHOICES = [
        ('1', 'Term 1'),
        ('2', 'Term 2'),
        ('3', 'Term 3'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='student_profile',
        on_delete=models.CASCADE
    )
    admission_no = models.CharField(max_length=30, unique=True)
    school = models.ForeignKey(School, default='', on_delete=models.CASCADE)

    # MAIN CLASS FIELD (kept because your whole logic uses this)
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        related_name='students',
        null=True,
        blank=True
    )

    # NEW FIELDS FOR PROMOTION SUPPORT (do NOT break your logic)
    promoted_from = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promotions_from'
    )
    promoted_to = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='promotions_to'
    )

    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=(('M', 'Male'), ('F', 'Female')),
        blank=True,
        null=True
    )
    photo = models.ImageField(upload_to='student_photos/', null=True, blank=True)

    session = models.CharField(max_length=20, null=True, blank=True)
    term = models.CharField(max_length=1, choices=TERM_CHOICES, blank=True, default='')

    is_result_blocked = models.BooleanField(default=False)
    block_reason = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def full_name(self):
        return self.user.get_full_name() or self.user.username

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










