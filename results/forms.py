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


class GradeSettingForm(forms.ModelForm):
    grades = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6}),
        help_text='Enter JSON like {"A": 90, "B": 80, "C": 70, "D": 60, "F": 0}'
    )
    grade_interpretations = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6}),
        required=False,
        help_text='Enter JSON for grade interpretations per grade like {"A": "Excellent", "B": "Very Good"}'
    )
    principal_comments = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6}),
        required=False,
        help_text='Enter JSON for principal comments per grade like {"A": "Excellent", "B": "Good"}'
    )
    teacher_comments = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6}),
        required=False,
        help_text='Enter JSON for teacher comments per grade like {"A": "Excellent", "B": "Good"}'
    )

    class Meta:
        model = GradeSetting
        fields = ["grades", "grade_interpretations", "principal_comments", "teacher_comments"]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        if instance:
            initial = kwargs.get("initial", {})
            initial["grades"] = json.dumps(instance.grades, indent=4)
            initial["grade_interpretations"] = json.dumps(getattr(instance, "grade_interpretations", {}), indent=4)
            initial["principal_comments"] = json.dumps(getattr(instance, "principal_comments", {}), indent=4)
            initial["teacher_comments"] = json.dumps(getattr(instance, "teacher_comments", {}), indent=4)
            kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def clean_grades(self):
        return self._clean_json_field("grades")

    def clean_grade_interpretations(self):
        return self._clean_json_field("grade_interpretations")

    def clean_principal_comments(self):
        return self._clean_json_field("principal_comments")

    def clean_teacher_comments(self):
        return self._clean_json_field("teacher_comments")

    def _clean_json_field(self, field_name):
        data = self.cleaned_data[field_name]
        try:
            parsed = json.loads(data)
            if not isinstance(parsed, dict):
                raise forms.ValidationError(f"{field_name} must be a JSON object")
        except json.JSONDecodeError:
            raise forms.ValidationError(f"Invalid JSON format for {field_name}")
        return parsed

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.grades = self.cleaned_data["grades"]
        instance.grade_interpretations = self.cleaned_data.get("grade_interpretations", {})
        instance.principal_comments = self.cleaned_data.get("principal_comments", {})
        instance.teacher_comments = self.cleaned_data.get("teacher_comments", {})
        if commit:
            instance.save()
        return instance
