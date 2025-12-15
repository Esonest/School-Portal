from django import forms
from .models import Student

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('admission_no','school_class','dob','gender')
        widgets = {
            'dob': forms.DateInput(attrs={'type':'date'})
        }