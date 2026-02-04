from django import forms
from .models import LessonNote

class LessonNoteForm(forms.ModelForm):
    class Meta:
        model = LessonNote
        fields = (
            'title','subject','category','content','file',
            'session','term','visibility','classes','publish_date'
        )
        widgets = {
            'publish_date': forms.DateInput(attrs={'type': 'date', 'class':'w-full rounded-lg p-3 border-gray-300 focus:ring-2 focus:ring-indigo-400'}),
            'classes': forms.SelectMultiple(attrs={'size': 6, 'class':'w-full rounded-lg p-3 border-gray-300 focus:ring-2 focus:ring-indigo-400'}),
            'term': forms.Select(attrs={'class':'w-full rounded-lg p-3 border-gray-300 focus:ring-2 focus:ring-indigo-400'}),
            'session': forms.TextInput(attrs={'class':'w-full rounded-lg p-3 border-gray-300 focus:ring-2 focus:ring-indigo-400'}),
            'title': forms.TextInput(attrs={'class':'w-full rounded-lg p-3 border-gray-300 focus:ring-2 focus:ring-indigo-400'}),
            'category': forms.TextInput(attrs={'class':'w-full rounded-lg p-3 border-gray-300 focus:ring-2 focus:ring-indigo-400'}),
            'content': forms.Textarea(attrs={'rows':3, 'class':'w-full rounded-lg p-3 border-gray-300 focus:ring-2 focus:ring-indigo-400'}),
            'file': forms.ClearableFileInput(attrs={'class':'w-full'}),
            'visibility': forms.CheckboxInput(attrs={'class':'h-5 w-5 text-indigo-600'}),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        if teacher:
            # Only teacher's classes and subjects **within their school**
            self.fields['classes'].queryset = teacher.classes.filter(school=teacher.school)
            self.fields['subject'].queryset = teacher.subjects.filter(school=teacher.school)

