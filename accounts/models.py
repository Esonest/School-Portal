from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


# =============================
#  MAIN USER MODEL
# =============================

class School(models.Model):
    COLOR_CHOICES = [
        ("indigo", "Indigo"),
        ("blue", "Blue"),
        ("green", "Green"),
        ("red", "Red"),
        ("yellow", "Yellow"),
        ("purple", "Purple"),
        ("pink", "Pink"),
        ("teal", "Teal"),
        ("gray", "Gray"),
    ]

    name = models.CharField(max_length=255, unique=True)

    # ✅ IMAGE UPLOAD ONLY
    logo = models.ImageField(
        upload_to="school_logos/",
        blank=True,
        null=True,
        help_text="Upload school logo (Cloudinary)",
    )

    address = models.TextField(blank=True)
    motto = models.CharField(max_length=255, blank=True)

    principal_signature = models.ImageField(
        upload_to="signatures/",
        blank=True,
        null=True,
    )

    theme_color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        default="indigo",
    )
    
    notification_email = models.EmailField(
        blank=True,
        null=True
    )

    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    email_enabled = models.BooleanField(default=True)

    whatsapp_enabled = models.BooleanField(default=False)

    paystack_public_key = models.CharField(max_length=255, blank=True, null=True)
    paystack_secret_key = models.CharField(max_length=255, blank=True, null=True)

    active = models.BooleanField(default=True)
    created_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name




class SystemSetting(models.Model):
    current_session = models.CharField(max_length=20)
    current_term = models.CharField(max_length=20)


class User(AbstractUser):
    """
    Unified User model for all user types (Admin, Teacher, Student, etc.)
    Roles are distinguished using a role field.
    Each user belongs to a school (except super admins).
    """
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('schooladmin', 'School Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('accountant', 'Accountant'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    school = models.ForeignKey(
        'School',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )

    # Legacy compatibility
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='user_profiles/', blank=True, null=True)

    def __str__(self):
        # Always show username as primary representation
        return self.username


    @property
    def is_active_user(self):
        """Checks if user is active and not deleted"""
        return not self.is_deleted and self.is_active    

    @property
    def is_superadmin(self):
        return self.role == 'superadmin' or self.is_superuser

    @property
    def is_schooladmin(self):
        return self.role == 'schooladmin'

    @property
    def is_teacher_user(self):
        return self.role == 'teacher' or self.is_teacher

    @property
    def is_student_user(self):
        return self.role == 'student' or self.is_student

    @property
    def is_accountant_user(self):
        return self.role == 'accountant' or self.is_accountant    


from django.db import models
from django.conf import settings



class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='teacher_profile',
        on_delete=models.CASCADE
    )
    staff_id = models.CharField(max_length=50, unique=True)
    school = models.ForeignKey(
        School,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='teachers'
    )
    classes = models.ManyToManyField('students.SchoolClass', blank=True, related_name='teachers')
    subjects = models.ManyToManyField('results.Subject', blank=True, related_name='teachers')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def get_full_name(self):
        return self.user.get_full_name() or self.user.username



from django.db import models
from django.conf import settings


class SchoolAdmin(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="school_admin_profile"
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.get_full_name()} - Admin of {self.school.name}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=255)

    email = models.EmailField()

    subject = models.CharField(max_length=255)

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_handled = models.BooleanField(
        default=False
    )

    email_sent = models.BooleanField(
        default=False
    )

    email_response = models.TextField(
        blank=True
    )

    def __str__(self):
        return f"{self.name} - {self.subject}"




class DemoBooking(models.Model):

    STATUS_CHOICES = (
        ("new", "New"),
        ("contacted", "Contacted"),
        ("completed", "Completed"),
    )

    school_name = models.CharField(
        max_length=255
    )

    contact_person = models.CharField(
        max_length=255
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=20
    )

    student_population = models.CharField(
        max_length=100,
        blank=True
    )

    message = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new"
    )

    email_sent = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.school_name} - {self.contact_person}"
   

class Subscriber(models.Model):

    email = models.EmailField(
        unique=True
    )

    subscribed_at = models.DateTimeField(
        auto_now_add=True
    )

    active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return self.email