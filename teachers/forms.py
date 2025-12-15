from django import forms
from django.forms import modelformset_factory
from results.models import Score, Affective, Psychomotor
from assignments.models import Assignment
from notes.models import LessonNote

class AssignmentCreateForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ('title','description','subject','due_date','file')

class LessonNoteForm(forms.ModelForm):
    class Meta:
        model = LessonNote
        fields = ('title','subject','content','file')