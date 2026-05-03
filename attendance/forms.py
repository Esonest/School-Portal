from django import forms
from .models import Attendance
from students.models import Student
from students.models import SchoolClass


INPUT_CLASS = "w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition bg-white"
TEXTAREA_CLASS = "w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition bg-white"

class AttendanceForm(forms.Form):

    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": INPUT_CLASS})
    )

    date = forms.DateField(
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": INPUT_CLASS
        })
    )

    status = forms.ChoiceField(
        choices=Attendance.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": INPUT_CLASS})
    )

    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.none(),
        widget=forms.CheckboxSelectMultiple()
    )

    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 3,
            "class": TEXTAREA_CLASS,
            "placeholder": "Optional remarks (e.g. Late, Sick, etc.)"
        })
    )

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)

        if school:
            self.fields["school_class"].queryset = SchoolClass.objects.filter(school=school)
            self.fields["students"].queryset = Student.objects.filter(school=school)


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

