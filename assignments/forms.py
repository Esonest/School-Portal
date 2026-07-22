from django import forms
from .models import Assignment, AssignmentSubmission, SubmissionFile

from django import forms
from .models import Assignment, SchoolClass, Subject
from django import forms
from django.core.exceptions import ValidationError
import os

from .models import Assignment, SchoolClass, Subject


from django import forms
from django.core.exceptions import ValidationError
import os

from .models import Assignment
from students.models import SchoolClass
from results.models import Subject
from results.utils import SESSION_LIST


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
            'expiry_date',
            'max_score',
            'file',
            'published',
            'is_active',
        )


        widgets = {

            'title': forms.TextInput(
                attrs={
                    'class':
                    'w-full border rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500'
                }
            ),


            'description': forms.Textarea(
                attrs={
                    'rows':4,
                    'class':
                    'w-full border rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500'
                }
            ),


            'session': forms.Select(
                attrs={
                    'class':
                    'w-full border rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500'
                }
            ),


            'term': forms.Select(
                attrs={
                    'class':
                    'w-full border rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500'
                }
            ),


            'classes': forms.SelectMultiple(
                attrs={
                    'size':8,
                    'class':
                    'w-full border rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500'
                }
            ),


            'due_date': forms.DateTimeInput(
                attrs={
                    'type':'datetime-local',
                    'class':
                    'w-full border rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500'
                }
            ),


            'expiry_date': forms.DateTimeInput(
                attrs={
                    'type':'datetime-local',
                    'class':
                    'w-full border rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500'
                }
            ),


            'max_score': forms.NumberInput(
                attrs={
                    'class':
                    'w-full border rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500'
                }
            ),


            'file': forms.ClearableFileInput(
                attrs={
                    'class':
                    'w-full border rounded-xl p-3'
                }
            ),


            'published': forms.CheckboxInput(
                attrs={
                    'class':
                    'h-5 w-5 text-indigo-600'
                }
            ),


            'is_active': forms.CheckboxInput(
                attrs={
                    'class':
                    'h-5 w-5 text-indigo-600'
                }
            ),

        }



    def __init__(self, *args, **kwargs):

        teacher = kwargs.pop(
            'teacher',
            None
        )

        school = kwargs.pop(
            'school',
            None
        )


        super().__init__(
            *args,
            **kwargs
        )



        # =====================================
        # SESSION DROPDOWN
        # =====================================

        session_choices = []


        for item in SESSION_LIST:

            if isinstance(item, (list, tuple)):

                session_choices.append(
                    (
                        item[0],
                        item[1]
                    )
                )

            else:

                session_choices.append(
                    (
                        item,
                        item
                    )
                )



        self.fields['session'] = forms.ChoiceField(
            choices=[
                ('', 'Select Session')
            ] + session_choices,
            required=False,
            widget=forms.Select(
                attrs={
                    'class':
                    'w-full border rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500'
                }
            )
        )



        # =====================================
        # DEFAULT SECURITY
        # =====================================

        self.fields['classes'].queryset = (
            SchoolClass.objects.none()
        )


        self.fields['subject'].queryset = (
            Subject.objects.none()
        )



        # =====================================
        # TEACHER FILTER
        # =====================================

        if teacher:


            self.fields['classes'].queryset = (
                teacher.classes
                .filter(
                    school=teacher.school
                )
                .distinct()
            )


            self.fields['subject'].queryset = (
                teacher.subjects
                .filter(
                    school=teacher.school
                )
                .distinct()
            )



        # =====================================
        # SCHOOL ADMIN FILTER
        # =====================================

        elif school:


            self.fields['classes'].queryset = (
                SchoolClass.objects.filter(
                    school=school
                )
            )


            self.fields['subject'].queryset = (
                Subject.objects.filter(
                    school=school
                )
            )



    # =====================================
    # VALIDATION
    # =====================================

    def clean(self):

        cleaned_data = super().clean()


        due_date = cleaned_data.get(
            "due_date"
        )

        expiry_date = cleaned_data.get(
            "expiry_date"
        )


        if due_date and expiry_date:

            if expiry_date < due_date:

                raise ValidationError(
                    "Expiry date cannot be before due date."
                )


        return cleaned_data



    # =====================================
    # FILE VALIDATION
    # =====================================

    def clean_file(self):

        file = self.cleaned_data.get(
            "file"
        )


        if not file:

            return file



        ext = os.path.splitext(
            file.name
        )[1].lower()



        allowed = [
            ".pdf",
            ".doc",
            ".docx",
            ".ppt",
            ".pptx",
            ".xls",
            ".xlsx",
            ".zip",
            ".rar",
            ".txt",
            ".jpg",
            ".jpeg",
            ".png",
        ]



        if ext not in allowed:

            raise ValidationError(
                "Unsupported file type."
            )


        return file

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
