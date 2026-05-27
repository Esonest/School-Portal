from django import forms
from .models import LessonNote
from students.models import SchoolClass
from results.models import Subject
from results.utils import SESSION_LIST

class LessonNoteForm(forms.ModelForm):
    class Meta:
        model = LessonNote
        fields = (
            'title', 'subject', 'content', 'file',
            'session', 'term', 'visibility',
            'classes', 'publish_date'
        )
        widgets = {
            'publish_date': forms.DateInput(attrs={'type': 'date'}),
            'classes': forms.SelectMultiple(attrs={'size': 6}),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # -------------------------
        # SESSION DROPDOWN (SAFE NORMALIZATION)
        # -------------------------
        session_choices = []
        for item in SESSION_LIST:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                session_choices.append((item[0], item[1]))
            else:
                session_choices.append((item, item))

        self.fields['session'] = forms.ChoiceField(
            choices=session_choices,
            required=False
        )

        # -------------------------
        # DEFAULT LOCK (SECURITY)
        # -------------------------
        self.fields['classes'].queryset = SchoolClass.objects.none()
        self.fields['subject'].queryset = Subject.objects.none()

        # -------------------------
        # SCHOOL ADMIN
        # -------------------------
        if user and hasattr(user, 'school') and not teacher:
            self.fields['classes'].queryset = SchoolClass.objects.filter(
                school=user.school
            )

            self.fields['subject'].queryset = Subject.objects.filter(
                school=user.school
            )

        # -------------------------
        # TEACHER
        # -------------------------
        elif teacher:
            self.fields['classes'].queryset = (
                teacher.classes.filter(school=teacher.school).distinct()
            )

            self.fields['subject'].queryset = (
                teacher.subjects.filter(school=teacher.school).distinct()
            )