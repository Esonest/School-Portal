from django import forms
from .models import LessonNote
from students.models import SchoolClass
from results.models import Subject

class LessonNoteForm(forms.ModelForm):
    class Meta:
        model = LessonNote
        fields = (
            'title','subject','content','file',
            'session','term','visibility','classes','publish_date'
        )
        widgets = {
            'publish_date': forms.DateInput(attrs={'type': 'date'}),
            'classes': forms.SelectMultiple(attrs={'size': 6}),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        # HARD LOCK: show nothing by default
        self.fields['classes'].queryset = SchoolClass.objects.none()
        self.fields['subject'].queryset = Subject.objects.none()

        if teacher:
            self.fields['classes'].queryset = (
                teacher.classes
                .filter(school=teacher.school)
                .distinct()
            )

            self.fields['subject'].queryset = (
                teacher.subjects
                .filter(school=teacher.school)
                .distinct()
            )
