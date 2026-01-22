from django import forms
from accounts.models import User, SchoolAdmin, School


  # update if your profile model is named differently

class CreateAndAssignAdminForm(forms.Form):
    # User info
    username = forms.CharField(max_length=150, label="Username")
    first_name = forms.CharField(max_length=150, label="First Name")
    last_name = forms.CharField(max_length=150, label="Last Name")
    email = forms.EmailField(required=False, label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

    # School for assignment (optional)
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        required=False,
        label="Assign to School",
        empty_label="-- No School --"
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def save(self):
        # Extract cleaned data
        data = self.cleaned_data
        school = data.get("school")

        # Create the user as school admin
        user = User.objects.create_user(
            username=data["username"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data.get("email", ""),
            password=data["password"],
            role="schooladmin",
            school=school  # can be None
        )

        # Create SchoolAdminProfile only if a school is assigned
        if school:
            SchoolAdmin.objects.create(
                user=user,
                school=school
            )

        return user


# -------------------------
# SCHOOL CREATION / EDIT FORM
# -------------------------

from django.conf import settings
import os

from django import forms
from .models import School

from django import forms
from .models import School

class SchoolForm(forms.ModelForm):
    logo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-input"}),
        label="School Logo"
    )

    class Meta:
        model = School
        fields = [
            "name",
            "address",
            "motto",
            "logo",
            "theme_color",
            "principal_signature",
            "paystack_public_key",
            "paystack_secret_key",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "id": "school-name-input"}),
            "address": forms.TextInput(attrs={"class": "form-input"}),
            "motto": forms.TextInput(attrs={"class": "form-input"}),
            "theme_color": forms.Select(attrs={"class": "form-input", "id": "theme-color-select"}),
            "principal_signature": forms.ClearableFileInput(attrs={"class": "form-input"}),

            # --- Add Paystack key input fields ---
            "paystack_public_key": forms.TextInput(attrs={"class": "form-input", "placeholder": "Paystack Public Key"}),
            "paystack_secret_key": forms.TextInput(attrs={"class": "form-input", "placeholder": "Paystack Secret Key"}),
        }


# -------------------------
# SCHOOL DELETE (CONFIRMATION)
# -------------------------
class SchoolDeleteForm(forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label="Yes, delete this school permanently."
    )



# superadmin/forms/student_forms.py
from django import forms
from django.contrib.auth import get_user_model
from students.models import Student, SchoolClass
from accounts.models import School

User = get_user_model()

class StudentUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False, help_text="Leave blank to auto-generate a password")
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "profile_picture", "password"]
        widgets = {
            "username": forms.TextInput(attrs={"class":"w-full border p-2 rounded"}),
            "first_name": forms.TextInput(attrs={"class":"w-full border p-2 rounded"}),
            "last_name": forms.TextInput(attrs={"class":"w-full border p-2 rounded"}),
            "email": forms.EmailInput(attrs={"class":"w-full border p-2 rounded"}),
            "profile_picture": forms.FileInput(attrs={"class":"w-full"}),
        }

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["school", "school_class", "dob", "gender", "photo"]
        widgets = {
            "school": forms.Select(attrs={"class":"w-full border p-2 rounded"}),
            "school_class": forms.Select(attrs={"class":"w-full border p-2 rounded"}),
            "dob": forms.DateInput(attrs={"type":"date","class":"w-full border p-2 rounded"}),
            "photo": forms.FileInput(attrs={"class":"w-full"}),
        }

class BulkUploadForm(forms.Form):
    file = forms.FileField(label="CSV file (admission_no optional)", help_text="CSV columns: first_name,last_name,email,school_id,class_id,dob,gender,session,term")



# superadmin/forms.py

from django import forms
from accounts.models import Teacher, School
from students.models import SchoolClass
from results.models import Subject

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ["user", "school", "subjects", "classes"]

    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )

    classes = forms.ModelMultipleChoiceField(
        queryset=SchoolClass.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )


class TeacherImportForm(forms.Form):
    file = forms.FileField()



class SchoolClassForm(forms.ModelForm):

    class Meta:
        model = SchoolClass
        fields = ["name", "school"]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input w-full border rounded p-2",
                "placeholder": "Enter class name (e.g., JSS 1A)",
            }),
            "school": forms.Select(attrs={
                "class": "form-select w-full border rounded p-2",
            }),
        
        }




class SubjectForm(forms.ModelForm):

    class Meta:
        model = Subject
        fields = ["name", "school"]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input w-full border rounded p-2",
                "placeholder": "Enter subject name (e.g., Mathematics)",
            }),
            "school": forms.Select(attrs={
                "class": "form-select w-full border rounded p-2",
            }),
        }



from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()




class UserCreateForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']

    def clean_password2(self):
        pw1 = self.cleaned_data.get('password1')
        pw2 = self.cleaned_data.get('password2')
        if pw1 != pw2:
            raise forms.ValidationError("Passwords do not match!")
        return pw2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user





class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username", "password", "role", "is_active"]


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": (
                    "w-full px-4 py-3 bg-gray-100 rounded-xl "
                    "border border-gray-300 focus:outline-none "
                    "focus:ring-2 focus:ring-blue-500"
                )
            })




from .models import SchoolPortalSetting

class SchoolPortalSettingForm(forms.ModelForm):
    class Meta:
        model = SchoolPortalSetting
        exclude = ("school",)
        widgets = {
            field: forms.CheckboxInput(attrs={"class": "h-5 w-5 text-indigo-600"})
            for field in [
                "cbt_enabled",
                "results_enabled",
                "lesson_note_enabled",
                "attendance_enabled",
                "finance_enabled",
                "teachers_enabled",
                "students_enabled",
                "assignments_enabled",
            ]
        }
