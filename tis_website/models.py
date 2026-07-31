from django.db import models
from accounts.models import School
from django.utils.text import slugify
from students.models import SchoolClass
import uuid





class SchoolWebsite(models.Model):

    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name="website"
    )


    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True
    )


    motto = models.CharField(
        max_length=255
    )


    vision = models.TextField()


    mission = models.TextField()


    history = models.TextField()



    principal_name = models.CharField(
        max_length=200
    )


    principal_photo = models.ImageField(
        upload_to="website/principal/",
        blank=True,
        null=True
    )


    principal_message = models.TextField()



    address = models.TextField(
        blank=True
    )


    phone = models.CharField(
        max_length=20,
        blank=True
    )


    email = models.EmailField(
        blank=True
    )


    facebook = models.URLField(
        blank=True
    )


    instagram = models.URLField(
        blank=True
    )


    whatsapp = models.CharField(
        max_length=20,
        blank=True
    )



    updated_at = models.DateTimeField(
        auto_now=True
    )



    def save(self, *args, **kwargs):

        if not self.slug:

            self.slug = slugify(
                self.school.name
            )


        super().save(
            *args,
            **kwargs
        )



    def __str__(self):

        return self.school.name

class HomepageContent(models.Model):

    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name="homepage"
    )


    hero_title = models.CharField(
        max_length=200,
        default="Welcome to Tech International School"
    )


    hero_subtitle = models.TextField(
        default="Building Future Leaders Through Technology, Innovation and Excellence"
    )


    hero_image = models.ImageField(
        upload_to="website/homepage/",
        blank=True,
        null=True
    )


    primary_button_text = models.CharField(
        max_length=50,
        default="Apply Now"
    )


    primary_button_link = models.CharField(
        max_length=200,
        default="/school/admissions/"
    )


    secondary_button_text = models.CharField(
        max_length=50,
        default="Student Portal"
    )


    secondary_button_link = models.CharField(
        max_length=200,
        default="/accounts/login/"
    )


    updated_at = models.DateTimeField(
        auto_now=True
    )


    def __str__(self):

        return f"{self.school.name} Homepage"    


class WhyChooseUs(models.Model):

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="why_choose"
    )


    title = models.CharField(
        max_length=100
    )


    description = models.TextField()


    icon = models.CharField(
        max_length=50,
        blank=True
    )


    order = models.PositiveIntegerField(
        default=1
    )


    class Meta:

        ordering = [
            "order"
        ]


    def __str__(self):

        return self.title



class SchoolStatistic(models.Model):

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="statistics"
    )


    number = models.CharField(
        max_length=50
    )


    title = models.CharField(
        max_length=100
    )


    order = models.PositiveIntegerField(
        default=1
    )


    class Meta:

        ordering = [
            "order"
        ]


    def __str__(self):

        return f"{self.number} {self.title}"      


from django.db import models
from accounts.models import School



class NewsEvent(models.Model):

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="news_events"
    )


    title = models.CharField(
        max_length=200
    )


    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True
    )


    image = models.ImageField(
        upload_to="website/news/",
        blank=True,
        null=True
    )


    content = models.TextField()



    event_date = models.DateField(
        blank=True,
        null=True
    )



    is_published = models.BooleanField(
        default=True
    )



    created_at = models.DateTimeField(
        auto_now_add=True
    )


    updated_at = models.DateTimeField(
        auto_now=True
    )



    class Meta:

        ordering = [
            "-created_at"
        ]



    def save(self, *args, **kwargs):

        if not self.slug:

            from django.utils.text import slugify

            self.slug = slugify(
                self.title
            )

        super().save(*args, **kwargs)



    def __str__(self):

        return self.title      


class Gallery(models.Model):

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="gallery"
    )


    title = models.CharField(
        max_length=200
    )


    image = models.ImageField(
        upload_to="website/gallery/"
    )


    description = models.TextField(
        blank=True
    )


    is_published = models.BooleanField(
        default=True
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    updated_at = models.DateTimeField(
        auto_now=True
    )



    class Meta:

        ordering = [
            "-created_at"
        ]



    def __str__(self):

        return self.title        


from django.conf import settings



class AdmissionApplication(models.Model):


    STATUS_CHOICES = (

        ("pending", "Pending"),

        ("exam_assigned", "Exam Assigned"),

        ("exam_completed", "Exam Completed"),

        ("passed", "Passed"),

        ("failed", "Failed"),

        ("approved", "Approved"),

        ("rejected", "Rejected"),

    )



    GENDER_CHOICES = (

        ("Male", "Male"),

        ("Female", "Female"),

    )



    # ==========================
    # SCHOOL CONNECTION
    # ==========================

    school = models.ForeignKey(

        School,

        on_delete=models.CASCADE,

        related_name="admission_applications"

    )



    # ==========================
    # UNIQUE APPLICATION ACCESS
    # ==========================

    application_number = models.CharField(

        max_length=30,

        unique=True,

        editable=False

    )


    admission_token = models.UUIDField(

        default=uuid.uuid4,

        unique=True,

        editable=False

    )



    # ==========================
    # STUDENT INFORMATION
    # ==========================

    student_name = models.CharField(

        max_length=200

    )


    date_of_birth = models.DateField()



    gender = models.CharField(

        max_length=20,

        choices=GENDER_CHOICES

    )
    


    accepted = models.BooleanField(
        default=False
    )

    accepted_on = models.DateTimeField(
        null=True,
        blank=True
    )


    student_created = models.BooleanField(
        default=False
    ) 


    invoice_generated = models.BooleanField(
        default=False
    )

    
    class_applying_for = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admission_applications"
    )

    

    previous_school = models.CharField(

        max_length=200,

        blank=True

    )



    # ==========================
    # PARENT INFORMATION
    # ==========================

    parent_name = models.CharField(

        max_length=200

    )


    parent_phone = models.CharField(

        max_length=20

    )


    parent_email = models.EmailField()
    student_email = models.EmailField(
        blank=True,
        null=True
    )



    address = models.TextField()



    # ==========================
    # DOCUMENTS
    # ==========================

    passport = models.ImageField(

        upload_to="admissions/passport/",

        blank=True,

        null=True

    )


    document = models.FileField(

        upload_to="admissions/documents/",

        blank=True,

        null=True

    )



    # ==========================
    # CBT EXAM CONNECTION
    # ==========================


    admission_exam = models.ForeignKey(

        "cbt.CBTExam",

        on_delete=models.SET_NULL,

        null=True,

        blank=True,

        related_name="admission_candidates"

    )



    exam_score = models.DecimalField(

        max_digits=5,

        decimal_places=2,

        null=True,

        blank=True

    )



    exam_pass_mark = models.DecimalField(

        max_digits=5,

        decimal_places=2,

        default=50

    )



    exam_completed = models.BooleanField(

        default=False

    )



    # ==========================
    # ADMISSION STATUS
    # ==========================


    status = models.CharField(

        max_length=30,

        choices=STATUS_CHOICES,

        default="pending"

    )



    admission_letter_generated = models.BooleanField(

        default=False

    )

    resume_date = models.DateField(
        null=True,
        blank=True
    )

    admission_session = models.CharField(
        max_length=50,
        blank=True
    )

    admission_term = models.CharField(
        max_length=50,
        blank=True
    )

    accepted_offer = models.BooleanField(
        default=False
    )

    accepted_on = models.DateTimeField(
        null=True,
        blank=True
    )

    approved_on = models.DateTimeField(
        null=True,
        blank=True
    )


    student_username = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    student_password = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )


    # ==========================
    # TIMESTAMPS
    # ==========================


    created_at = models.DateTimeField(

        auto_now_add=True

    )


    updated_at = models.DateTimeField(

        auto_now=True

    )





    class Meta:

        ordering = [

            "-created_at"

        ]





    def save(self, *args, **kwargs):


        if not self.application_number:


            prefix = "TIS"


            count = AdmissionApplication.objects.count() + 1


            self.application_number = (

                f"{prefix}{count:05d}"

            )


        super().save(*args, **kwargs)





    def __str__(self):

        return (

            f"{self.student_name} - "
            f"{self.application_number}"

        )


from django.db import models
from cbt.models import CBTExam


class AdmissionExamSubmission(models.Model):

    application = models.OneToOneField(
        AdmissionApplication,
        on_delete=models.CASCADE,
        related_name="exam_submission"
    )

    exam = models.ForeignKey(
        CBTExam,
        on_delete=models.CASCADE
    )

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    total_questions = models.PositiveIntegerField(default=0)

    correct_answers = models.PositiveIntegerField(default=0)

    wrong_answers = models.PositiveIntegerField(default=0)

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    answers = models.JSONField(default=dict)

    started_at = models.DateTimeField(auto_now_add=True)

    submitted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    passed = models.BooleanField(default=False)

    class Meta:

        ordering = ["-started_at"]

    def __str__(self):

        return self.application.student_name    

