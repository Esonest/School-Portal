from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


# =============================
#  MAIN USER MODEL
# =============================


class School(models.Model):
    """
    Each school has its own identity, logo, motto, and address.
    All major portals link to this model via ForeignKey.
    """

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
    logo = models.CharField(max_length=255,blank=True,help_text="Path relative to static/, e.g. img/schools/my_school.png")
    address = models.TextField(blank=True)
    motto = models.CharField(max_length=255, blank=True)
    principal_signature = models.ImageField(
        upload_to="signatures/", blank=True, null=True
    )

    # 🎨 Theme color for the school
    theme_color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        default="indigo",
        help_text="Primary theme color used across the school portal",
    )

    active = models.BooleanField(default=True)
    created_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]



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

    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='user_profiles/', blank=True, null=True)

    def __str__(self):
        # Always show username as primary representation
        return self.username

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
