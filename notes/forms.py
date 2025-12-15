from django import forms
from .models import LessonNote

class LessonNoteForm(forms.ModelForm):
    class Meta:
        model = LessonNote
        fields = ('title', 'subject', 'category', 'content', 'file', 'session', 'term', 'visibility', 'classes', 'publish_date')
        widgets = {
            'publish_date': forms.DateInput(attrs={'type': 'date'}),
            'classes': forms.SelectMultiple(attrs={'size': 6}),
            'term': forms.Select(attrs={'class': 'form-control'}),
            'session': forms.TextInput(attrs={'class': 'form-control'}),
        }

