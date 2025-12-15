from django import forms
from .models import Attendance
from students.models import Student

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ('student','date','status','remarks')
        widgets = {
            'date': forms.DateInput(attrs={'type':'date'}),
        }


class BulkAttendanceForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}))
    status = forms.ChoiceField(choices=Attendance.STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.none(),
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, class_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if class_queryset is not None:
            self.fields['students'].queryset = class_queryset

