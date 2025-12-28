from django import forms
from students.models import Student
from accounts.models import User
from results.utils import generate_unique_username


tailwind_input = "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
tailwind_select = "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm bg-white focus:ring-2 focus:ring-blue-500"
tailwind_file = "block w-full text-sm text-gray-700 border border-gray-300 rounded-lg cursor-pointer bg-gray-50"


class StudentCreateForm(forms.ModelForm):
    # User fields
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": tailwind_input, "placeholder": "First name"})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": tailwind_input, "placeholder": "Last name"})
    )
    username = forms.CharField(
        required=False,  # optional, will auto-generate if empty
        widget=forms.TextInput(attrs={"class": tailwind_input, "placeholder": "Username"})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={"class": tailwind_input, "placeholder": "Password"})
    )

    class Meta:
        model = Student
        fields = [
            "admission_no",
            "school_class",
            "dob",
            "gender",
            "photo",
        ]
        widgets = {
            "admission_no": forms.TextInput(attrs={"class": tailwind_input}),
            "school_class": forms.Select(attrs={"class": tailwind_select}),
            "dob": forms.DateInput(attrs={"type": "date", "class": tailwind_input}),
            "gender": forms.Select(attrs={"class": tailwind_select}),
            "photo": forms.FileInput(attrs={"class": tailwind_file}),
        }

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop("school", None)
        super().__init__(*args, **kwargs)
        if self.school:
            self.fields["school_class"].queryset = self.fields["school_class"].queryset.filter(school=self.school)

    def save(self, commit=True):
        # Create the user first
        data = self.cleaned_data
        username = data.get("username") or generate_unique_username(data.get("first_name"))

        user = User.objects.create_user(
            username=username,
            first_name=data["first_name"],
            last_name=data["last_name"],
            password=data["password"],
            role="student",
            is_student=True,
            school=self.school
        )

        # Create the student profile
        student = super().save(commit=False)
        student.user = user
        student.school = self.school

        if commit:
            student.save()
            self.save_m2m()

        return student


class StudentUpdateForm(forms.ModelForm):
    # Add user fields
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": tailwind_input, "placeholder": "Username"})
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": tailwind_input, "placeholder": "Password (leave blank to keep unchanged)"})
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": tailwind_input, "placeholder": "First name"})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": tailwind_input, "placeholder": "Last name"})
    )

    class Meta:
        model = Student
        fields = [
            "username",
            "password",
            "first_name",
            "last_name",
            "admission_no",
            "school_class",
            "dob",
            "gender",
            "photo",
        ]
        widgets = {
            "admission_no": forms.TextInput(attrs={"class": tailwind_input}),
            "school_class": forms.Select(attrs={"class": tailwind_select}),
            "dob": forms.DateInput(attrs={"type": "date", "class": tailwind_input}),
            "gender": forms.Select(attrs={"class": tailwind_select}),
            "photo": forms.FileInput(attrs={"class": tailwind_file}),
        }

    def __init__(self, *args, **kwargs):
        self.school = kwargs.pop("school", None)  # Pass school from view
        super().__init__(*args, **kwargs)

        if self.school:
            # Filter classes to the specific school
            self.fields["school_class"].queryset = self.fields["school_class"].queryset.filter(school=self.school)

        # Populate initial values for linked user
        if self.instance and self.instance.user:
            self.fields["username"].initial = self.instance.user.username
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name

    def save(self, commit=True):
        student = super().save(commit=False)
        user = student.user

        # Update user fields
        user.username = self.cleaned_data["username"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)

        if commit:
            user.save()
            student.save()
            self.save_m2m()

        return student





from django import forms
from cbt.models import CBTExam, CBTQuestion, Subject, QuestionBank
from results.utils import SESSION_LIST


class CBTExamForm(forms.ModelForm):
    session = forms.ChoiceField(
        choices=[(s, s) for s in SESSION_LIST],
        required=True
    )

    class Meta:
        model = CBTExam
        fields = [
            'title',
            'subject',
            'session',
            'term',
            'school_class',
            'start_time',
            'end_time',
            'duration_minutes',
            'active'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # ---------- GLOBAL TAILWIND STYLING ----------
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": (
                    "w-full border-gray-300 rounded px-3 py-2 text-slate-800 "
                    "placeholder-slate-400 focus:outline-none focus:ring-2 "
                    "focus:ring-indigo-500 transition"
                )
            })

        # ---------- SCHOOL FILTERING ----------
        if user:
            if getattr(user, 'is_superadmin', False):
                # Superadmin: all subjects/classes
                self.fields['subject'].queryset = Subject.objects.all()
                self.fields['school_class'].queryset = SchoolClass.objects.all()
            else:
                # School admin: only subjects/classes in their school
                school = getattr(user.school_admin_profile, "school", None)
                if school:
                    self.fields['subject'].queryset = Subject.objects.filter(school=school)
                    self.fields['school_class'].queryset = SchoolClass.objects.filter(school=school)






class CBTQuestionForm(forms.ModelForm):
    class Meta:
        model = CBTQuestion
        fields = [
            'text', 'option_a', 'option_b',
            'option_c', 'option_d', 'correct_option', 'marks'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # allow empty forms so unused questions don't block save
        for field in self.fields.values():
            field.required = False



from results.utils import SESSION_LIST
from students.models import SchoolClass
from django.forms import modelformset_factory, BaseModelFormSet
from django.forms import BaseModelFormSet




class QuestionBankForm(forms.ModelForm):
    text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "w-full min-h-[140px] text-base rounded-lg border border-gray-300 px-3 py-2 "
                     "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        })
    )

    option_a = forms.CharField( required=False,widget=forms.TextInput(attrs={"class": "w-full border rounded-lg px-3 py-2"}))
    option_b = forms.CharField(required=False,widget=forms.TextInput(attrs={"class": "w-full border rounded-lg px-3 py-2"}))
    option_c = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "w-full border rounded-lg px-3 py-2"}))
    option_d = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "w-full border rounded-lg px-3 py-2"}))
    correct_option = forms.ChoiceField(
        required=False,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        widget=forms.Select(attrs={"class": "w-full border rounded-lg px-3 py-2"})
    )
    marks = forms.IntegerField( required=False,widget=forms.NumberInput(attrs={"class": "w-full border rounded-lg px-3 py-2"}))

    class Meta:
        model = QuestionBank
        fields = ['text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'marks']

    def has_changed(self):
        if not self.is_bound:
            return False

        text_key = f"{self.prefix}-text"
        return bool(self.data.get(text_key, "").strip())    

from django.forms import BaseModelFormSet


class BaseQuestionFormSet(BaseModelFormSet):
    """
    Custom formset for QuestionBank.
    Accepts a `user` keyword safely but does not touch `subject`.
    """

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)





QuestionFormSet = modelformset_factory(
    QuestionBank,
    form=QuestionBankForm,
    formset=BaseQuestionFormSet,
    extra=10,
    can_delete=True
)






from django import forms
from notes.models import LessonNote, NoteCategory, SchoolClass

class LessonNoteForm(forms.ModelForm):
    class Meta:
        model = LessonNote
        fields = ['title', 'subject', 'category', 'content', 'session', 'term', 'file', 'visibility', 'classes']
        widgets = {
            'content': forms.Textarea(attrs={'rows':4, 'class':'border p-2 w-full'}),
            'classes': forms.SelectMultiple(attrs={'class':'border p-2 w-full'}),
            'term': forms.Select(attrs={'class':'border p-2 w-full'}),
            'visibility': forms.Select(attrs={'class':'border p-2 w-full'}),
        }



from django import forms
from attendance.models import Attendance

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["student", "date", "status", "remarks"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "remarks": forms.Textarea(attrs={"rows": 2}),
        }




from django import forms
from accounts.models import User, Teacher
from students.models import SchoolClass
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class TeacherForm(forms.ModelForm):
    username = forms.CharField()
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(required=False)
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2})
    )

    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput
    )

    class Meta:
        model = Teacher
        fields = [
            "staff_id",
            "school",
            "classes",
            "subjects",
        ]

    def __init__(self, *args, **kwargs):
        self.is_edit = kwargs.pop("is_edit", False)
        self.school = kwargs.pop("school", None)  # ✅ SINGLE SOURCE OF TRUTH
        super().__init__(*args, **kwargs)

        if self.school:
            # Lock school
            self.fields["school"].queryset = (
                self.fields["school"].queryset.filter(id=self.school.id)
            )
            self.fields["school"].initial = self.school
            self.fields["school"].disabled = True

            # Restrict to school data
            self.fields["classes"].queryset = (
                self.fields["classes"].queryset.filter(school=self.school)
            )
            self.fields["subjects"].queryset = (
                self.fields["subjects"].queryset.filter(school=self.school)
            )

        if self.is_edit and self.instance.pk:
            user = self.instance.user
            self.fields["username"].initial = user.username
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email
            self.fields["phone"].initial = user.phone
            self.fields["address"].initial = user.address
            self.fields["password"].widget = forms.HiddenInput()
        else:
            self.fields["password"].required = True

    # ---------------- SAVE LOGIC (CRITICAL PART) ----------------
    @transaction.atomic
    def save(self, commit=True):
        teacher = super().save(commit=False)

        if self.is_edit:
            # -------- UPDATE USER --------
            user = teacher.user
            user.username = self.cleaned_data["username"]
            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            user.email = self.cleaned_data["email"]
            user.phone = self.cleaned_data["phone"]
            user.address = self.cleaned_data["address"]
            user.school = self.school
            user.save()

        else:
            # -------- CREATE USER --------
            user = User.objects.create_user(
                username=self.cleaned_data["username"],
                password=self.cleaned_data["password"],
                first_name=self.cleaned_data["first_name"],
                last_name=self.cleaned_data["last_name"],
                email=self.cleaned_data["email"],
            )
            user.phone = self.cleaned_data["phone"]
            user.address = self.cleaned_data["address"]
            user.role = "teacher"
            user.is_teacher = True
            user.school = self.school
            user.save()

            teacher.user = user

        teacher.school = self.school

        if commit:
            teacher.save()
            self.save_m2m()

        return teacher









from results.models import Score

class ScoreForm(forms.ModelForm):
    class Meta:
        model = Score
        fields = ['ca', 'exam']
        widgets = {
            'ca': forms.NumberInput(attrs={'class': 'border rounded px-2 py-1 w-24'}),
            'exam': forms.NumberInput(attrs={'class': 'border rounded px-2 py-1 w-24'}),
        }

    def __init__(self, *args, **kwargs):
        show_ca = kwargs.pop("show_ca", True)
        super().__init__(*args, **kwargs)

        if not show_ca:
            self.fields.pop("ca", None)    # 💥 remove CA dynamically


from results.models import ClassSubjectTeacher, Subject


TAILWIND_INPUT = "w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-400"

class ClassSubjectTeacherForm(forms.ModelForm):
    class Meta:
        model = ClassSubjectTeacher
        fields = ["school_class", "subject", "teacher"]
        widgets = {
            "school_class": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "subject": forms.Select(attrs={"class": TAILWIND_INPUT}),
            "teacher": forms.Select(attrs={"class": TAILWIND_INPUT}),
        }

    def __init__(self, *args, **kwargs):
        school = kwargs.pop("school", None)
        super().__init__(*args, **kwargs)

        if school:
            self.fields["school_class"].queryset = SchoolClass.objects.filter(school=school)
            self.fields["subject"].queryset = Subject.objects.filter(school=school)
            self.fields["teacher"].queryset = Teacher.objects.filter(school=school)




# school_admin/forms.py

from django import forms
from django.contrib.auth import get_user_model
from finance.models import SchoolAccountant

TAILWIND_INPUT = "w-full border-gray-300 rounded px-3 py-2"

User = get_user_model()

class AccountantUserForm(forms.ModelForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": TAILWIND_INPUT})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": TAILWIND_INPUT})
    )
    role = forms.CharField(
        widget=forms.HiddenInput(),  # hide role field from form
        initial="accountant"         # force role to accountant
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone", "role"]
        widgets = {
            "username": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "first_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "last_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "email": forms.EmailInput(attrs={"class": TAILWIND_INPUT}),
            "phone": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Passwords do not match")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.role = "accountant"  # ensure role is accountant
        if commit:
            user.save()
        return user


class SchoolAccountantForm(forms.ModelForm):
    """
    Handles SchoolAccountant-specific fields only.
    """
    class Meta:
        model = SchoolAccountant
        fields = ["staff_id", "is_active"]
        widgets = {
            "staff_id": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "is_active": forms.CheckboxInput(),
        }

    def save(self, commit=True):
        accountant = super().save(commit=False)
        if commit:
            accountant.save()
        return accountant

