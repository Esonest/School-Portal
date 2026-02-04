from django import forms
from .models import Assignment, AssignmentSubmission, SubmissionFile

from django import forms
from .models import Assignment, SchoolClass, Subject

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = (
            'title',
            'description',
            'subject',
            'classes',
            'session',
            'term',
            'due_date',
            'max_score',
            'file',
            'published'
        )
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type':'datetime-local', 'class':'w-full rounded-lg p-3 border-gray-300 focus:ring-2 focus:ring-indigo-400'}),
            'classes': forms.SelectMultiple(attrs={'size':6, 'class':'w-full rounded-lg p-3 border-gray-300 focus:ring-2 focus:ring-indigo-400'}),
            'term': forms.Select(attrs={'class':'w-full rounded-lg p-3 border-gray-300 focus:ring-2 focus:ring-indigo-400'}),
            'session': forms.TextInput(attrs={'class':'w-full rounded-lg p-3 border-gray-300 focus:ring-2 focus:ring-indigo-400'}),
            'title': forms.TextInput(attrs={'class':'w-full rounded-lg p-3 border-gray-300 focus:ring-2 focus:ring-indigo-400'}),
            'description': forms.Textarea(attrs={'rows':3, 'class':'w-full rounded-lg p-3 border-gray-300 focus:ring-2 focus:ring-indigo-400'}),
            'max_score': forms.NumberInput(attrs={'class':'w-full rounded-lg p-3 border-gray-300 focus:ring-2 focus:ring-indigo-400'}),
            'file': forms.ClearableFileInput(attrs={'class':'w-full'}),
            'published': forms.CheckboxInput(attrs={'class':'h-5 w-5 text-indigo-600'}),
        }

    def __init__(self, *args, **kwargs):
        # Expect teacher and school to be passed from view
        teacher = kwargs.pop('teacher', None)
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)

        # Filter classes and subjects
        if teacher:
            self.fields['classes'].queryset = teacher.classes.all()
            self.fields['subject'].queryset = teacher.subjects.all()
        elif school:
            self.fields['classes'].queryset = SchoolClass.objects.filter(school=school)
            self.fields['subject'].queryset = Subject.objects.filter(school=school)

        # Optional: If you want to restrict session to the current year
        # self.fields['session'].initial = '2025/2026'


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ('text',)

class SubmissionFileForm(forms.ModelForm):
    class Meta:
        model = SubmissionFile
        fields = ('file',)

class GradeForm(forms.Form):
    score = forms.DecimalField(max_digits=6, decimal_places=2)
    feedback = forms.CharField(widget=forms.Textarea, required=False)
