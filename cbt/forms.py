from django import forms
from django.forms import inlineformset_factory
from .models import CBTExam, CBTQuestion, Subject, SchoolClass

class CBTExamForm(forms.ModelForm):
    class Meta:
        model = CBTExam
        fields = [
            'title', 'subject', 'session', 'term', 'school_class',
            'start_time', 'end_time', 'duration_minutes', 'active'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class CBTQuestionForm(forms.ModelForm):
    class Meta:
        model = CBTQuestion
        exclude = ('exam',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2}),
            'option_a': forms.TextInput(),
            'option_b': forms.TextInput(),
            'option_c': forms.TextInput(),
            'option_d': forms.TextInput(),
            'correct_option': forms.Select(),
            'marks': forms.NumberInput(attrs={'min': 1}),
        }

# Inline formset to create multiple questions for one exam
CBTQuestionFormSet = inlineformset_factory(
    CBTExam,
    CBTQuestion,
    form=CBTQuestionForm,
    extra=20,  # default number of question forms shown
    can_delete=True
)




