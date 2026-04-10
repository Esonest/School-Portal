from django import forms
from .models import Student, Score, Psychomotor, Affective

# Bulk student addition
class StudentBulkForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'

# Bulk score entry
from django import forms
from django.forms import ModelForm
from django.apps import apps

Score = apps.get_model('results', 'Score')  # adjust if Score is in another app

class ScoreBulkForm(ModelForm):
    class Meta:
        model = Score
        fields = ['student', 'ca', 'exam']   # include total so hidden input exists
        widgets = {
            'student': forms.HiddenInput(),
            'ca': forms.NumberInput(attrs={
                'min': 0, 'max': 40, 'step': 1,
                'class': 'ca-input w-24 px-2 py-1 border rounded text-center'
            }),
            'exam': forms.NumberInput(attrs={
                'min': 0, 'max': 60, 'step': 1,
                'class': 'exam-input w-24 px-2 py-1 border rounded text-center'
            }),
            'total': forms.HiddenInput(),
        }

    def clean_ca(self):
        ca = self.cleaned_data.get('ca') or 0
        if ca < 0:
            raise forms.ValidationError("CA cannot be negative.")
        if ca > 40:
            raise forms.ValidationError("CA cannot exceed 40.")
        return ca

    def clean_exam(self):
        exam = self.cleaned_data.get('exam') or 0
        if exam < 0:
            raise forms.ValidationError("Exam cannot be negative.")
        if exam > 60:
            raise forms.ValidationError("Exam cannot exceed 60.")
        return exam



from django import forms
from django.forms import ModelForm
from django.apps import apps

Psychomotor = apps.get_model('results', 'Psychomotor')
Affective = apps.get_model('results', 'Affective')


class PsychomotorForm(ModelForm):
    class Meta:
        model = Psychomotor
        fields = ['student', 'neatness', 'agility', 'creativity', 'sports', 'handwriting']
        widgets = {
            'student': forms.HiddenInput(),
            'neatness': forms.HiddenInput(),
            'agility': forms.HiddenInput(),
            'creativity': forms.HiddenInput(),
            'sports': forms.HiddenInput(),
            'handwriting': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        from students.models import Student
        super().__init__(*args, **kwargs)    

    def clean_neatness(self):
        v = int(self.cleaned_data.get('neatness') or 1)
        if not 1 <= v <= 5:
            raise forms.ValidationError("Neatness must be 1–5")
        return v

    def clean_agility(self):
        v = int(self.cleaned_data.get('agility') or 1)
        if not 1 <= v <= 5:
            raise forms.ValidationError("Agility must be 1–5")
        return v

    def clean_creativity(self):
        v = int(self.cleaned_data.get('creativity') or 1)
        if not 1 <= v <= 5:
            raise forms.ValidationError("Creativity must be 1–5")
        return v

    def clean_sports(self):
        v = int(self.cleaned_data.get('sports') or 1)
        if not 1 <= v <= 5:
            raise forms.ValidationError("Sports must be 1–5")
        return v

    def clean_handwriting(self):
        v = int(self.cleaned_data.get('handwriting') or 1)
        if not 1 <= v <= 5:
            raise forms.ValidationError("Handwriting must be 1–5")
        return v


class AffectiveForm(ModelForm):
    class Meta:
        model = Affective
        fields = ['student', 'punctuality', 'cooperation', 'behavior', 'attentiveness', 'perseverance']
        widgets = {
            'student': forms.HiddenInput(),
            'punctuality': forms.HiddenInput(),
            'cooperation': forms.HiddenInput(),
            'behavior': forms.HiddenInput(),
            'attentiveness': forms.HiddenInput(),
            'perseverance': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        from students.models import Student
        super().__init__(*args, **kwargs)    

    def clean_punctuality(self):
        v = int(self.cleaned_data.get('punctuality') or 1)
        if not 1 <= v <= 5:
            raise forms.ValidationError("Punctuality must be 1–5")
        return v

    def clean_cooperation(self):
        v = int(self.cleaned_data.get('cooperation') or 1)
        if not 1 <= v <= 5:
            raise forms.ValidationError("Cooperation must be 1–5")
        return v

    def clean_behavior(self):
        v = int(self.cleaned_data.get('behavior') or 1)
        if not 1 <= v <= 5:
            raise forms.ValidationError("Behavior must be 1–5")
        return v

    def clean_attentiveness(self):
        v = int(self.cleaned_data.get('attentiveness') or 1)
        if not 1 <= v <= 5:
            raise forms.ValidationError("Attentiveness must be 1–5")
        return v

    def clean_perseverance(self):
        v = int(self.cleaned_data.get('perseverance') or 1)
        if not 1 <= v <= 5:
            raise forms.ValidationError("Perseverance must be 1–5")
        return v

from django import forms
from .models import GradeSetting
import json



from django import forms
from .models import GradeSetting

from django import forms
from .models import GradeSetting, SchoolClass

class GradeSettingForm(forms.ModelForm):
    class Meta:
        model = GradeSetting
        fields = ['SchoolClass', 'grade', 'min_score', 'interpretation']

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)

        # 🔥 CRITICAL FIX
        self.empty_permitted = True

        if school:
            self.fields['SchoolClass'].queryset = SchoolClass.objects.filter(school=school)
            self.fields['SchoolClass'].empty_label = "Select Class"

    def clean(self):
        cleaned_data = super().clean()

        # 🔥 SKIP validation if marked for deletion
        if cleaned_data.get("DELETE"):
            return cleaned_data

        return cleaned_data