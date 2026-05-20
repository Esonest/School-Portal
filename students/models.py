from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import School


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


    parent_name = models.CharField(
        max_length=255,
        blank=True
    )

    parent_email = models.EmailField(
        blank=True,
        null=True
    )

    parent_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    student_email = models.EmailField(
        blank=True,
        null=True
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
    

    # Access Control
    # -----------------------------
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive students cannot login to the portal"
    )

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

    def has_virtual_accounts(self):
        return self.virtual_accounts.exists()
    
    def primary_virtual_account(self):
        return self.virtual_accounts.filter(is_primary=True).first()

    def __str__(self):
        return f"{self.full_name()} ({self.admission_no})"


# finance/models.py or students/models.py

class VirtualAccount(models.Model):
    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
        related_name="virtual_accounts"
    )

    account_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True
    )

    account_name = models.CharField(
        max_length=255
    )

    bank_name = models.CharField(
        max_length=100
    )

    bank_slug = models.CharField(
        max_length=50,
        db_index=True
    )

    is_primary = models.BooleanField(
        default=False,
        help_text="Preferred account to show first on dashboard"
    )

    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "-created_at"]

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


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



# models.py
from django.db import models
from django.conf import settings
from django.utils import timezone


class Announcement(models.Model):

    CHANNEL_CHOICES = (
        ("portal", "Portal Only"),
        ("email", "Email"),
        ("whatsapp", "WhatsApp"),
    )

    TARGET_CHOICES = (
        ("all", "Entire School"),
        ("class", "Specific Class"),
        ("student", "Specific Student"),
        ("teachers", "Teachers"),
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="announcements"
    )

    title = models.CharField(max_length=255)

    message = models.TextField()

    targets = models.JSONField(
        default=list,
        blank=True
    )

    school_classes = models.ManyToManyField(
        SchoolClass,
        blank=True,
        related_name="announcement_classes"
    )

    students = models.ManyToManyField(
        Student,
        blank=True,
        related_name="announcement_students"
    )

    send_channels = models.JSONField(
        default=list,
        blank=True
    )



    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    publish_date = models.DateTimeField(default=timezone.now)

    expiry_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-publish_date"]

    def __str__(self):
        return self.title




# notifications/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):

    CHANNEL_CHOICES = [
        ("email", "Email"),
        ("whatsapp", "WhatsApp"),
        ("portal", "Portal"),
    ]

    AUDIENCE_CHOICES = [
        ("all_students", "All Students"),
        ("all_parents", "All Parents"),
        ("class_students", "Class Students"),
        ("class_parents", "Class Parents"),
        ("single_student", "Single Student"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    title = models.CharField(max_length=255)

    message = models.TextField()

    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES
    )

    audience = models.CharField(
        max_length=30,
        choices=AUDIENCE_CHOICES
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    total_recipients = models.PositiveIntegerField(default=0)

    successful_sent = models.PositiveIntegerField(default=0)

    failed_sent = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.channel})"


class NotificationRecipient(models.Model):

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="recipients"
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    recipient = models.CharField(max_length=255)

    status = models.CharField(
        max_length=20,
        default="pending"
    )

    response = models.TextField(blank=True)

    sent_at = models.DateTimeField(
        null=True,
        blank=True
    )


class SchoolCommunicationSetting(models.Model):
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE
    )

    # Email
    email_enabled = models.BooleanField(default=False)

    smtp_sender_name = models.CharField(
        max_length=255,
        blank=True
    )

    smtp_sender_email = models.EmailField(blank=True)

    brevo_api_key = models.CharField(
        max_length=255,
        blank=True
    )

    # WhatsApp
    whatsapp_enabled = models.BooleanField(default=False)

    whatsapp_token = models.TextField(blank=True)

    whatsapp_phone_id = models.CharField(
        max_length=255,
        blank=True
    )

    whatsapp_business_number = models.CharField(
        max_length=50,
        blank=True
    )


class MessageLog(models.Model):

    CHANNELS = (
        ("email", "Email"),
        ("whatsapp", "WhatsApp"),
    )

    STATUS = (
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE)

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE
    )

    recipient = models.CharField(max_length=255)

    channel = models.CharField(max_length=20, choices=CHANNELS)

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="pending"
    )

    response = models.TextField(blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)