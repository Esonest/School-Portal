from django import forms
from .models import Assignment, AssignmentSubmission, SubmissionFile

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ('title','description','subject','classes', 'session', 'term','due_date','max_score','file','published')
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type':'datetime-local'}),
            'classes': forms.SelectMultiple(attrs={'size':6}),
            'term': forms.Select(attrs={'class': 'form-control'}),
            'session': forms.TextInput(attrs={'class': 'form-control'}),
            
        }

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
