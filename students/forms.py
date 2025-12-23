from django import forms
from .models import Student

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('dob', 'photo','gender')
        widgets = {
            'dob': forms.DateInput(attrs={'type':'date'})
        }