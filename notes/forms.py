
from django import forms
from django.core.exceptions import ValidationError

from .models import LessonNote
from students.models import SchoolClass
from results.models import Subject
from results.utils import SESSION_LIST



class LessonNoteForm(forms.ModelForm):

    class Meta:

        model = LessonNote

        fields = (
            'title',
            'subject',
            'content',
            'file',
            'session',
            'term',
            'visibility',
            'classes',
            'publish_date',
            'expiry_date',
            'is_active',
        )


        widgets = {

            'publish_date': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),


            'expiry_date': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),


            'classes': forms.SelectMultiple(
                attrs={
                    'size': 8
                }
            ),


            'is_active': forms.CheckboxInput(
                attrs={
                    'class': 'h-5 w-5 rounded text-indigo-600'
                }
            ),

        }



    def __init__(self, *args, **kwargs):

        teacher = kwargs.pop(
            'teacher',
            None
        )

        user = kwargs.pop(
            'user',
            None
        )


        super().__init__(*args, **kwargs)



        # ==========================
        # SESSION DROPDOWN
        # ==========================

        session_choices = []


        for item in SESSION_LIST:

            if isinstance(item, (list, tuple)) and len(item) >= 2:

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

            choices=session_choices,

            required=False,

            widget=forms.Select(
                attrs={
                    "class":
                    "w-full border border-gray-300 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500"
                }
            )
        )



        # ==========================
        # SECURITY DEFAULT
        # ==========================

        self.fields['classes'].queryset = (
            SchoolClass.objects.none()
        )


        self.fields['subject'].queryset = (
            Subject.objects.none()
        )



        # ==========================
        # COMMON FIELD STYLING
        # ==========================

        for name, field in self.fields.items():

            field.widget.attrs.update({

                "class":
                "w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"

            })



        # ==========================
        # CONTENT FIELD
        # ==========================

        self.fields['content'].widget.attrs.update({

            "class":
            "w-full border border-gray-300 rounded-xl p-4 min-h-[250px] focus:ring-2 focus:ring-indigo-500"

        })



        # ==========================
        # MULTIPLE CLASSES FIELD
        # ==========================

        self.fields['classes'].widget.attrs.update({

            "class":
            "w-full border border-gray-300 rounded-xl p-3 focus:ring-2 focus:ring-indigo-500",

            "size": 8

        })



        # ==========================
        # FILE FIELD
        # ==========================

        self.fields['file'].widget.attrs.update({

            "class":
            "w-full border border-dashed border-indigo-400 rounded-xl p-4 bg-indigo-50 cursor-pointer"

        })



        # ==========================
        # SCHOOL ADMIN ACCESS
        # ==========================

        if user and getattr(user, 'school', None) and not teacher:


            self.fields['classes'].queryset = (
                SchoolClass.objects.filter(
                    school=user.school
                )
            )


            self.fields['subject'].queryset = (
                Subject.objects.filter(
                    school=user.school
                )
            )



        # ==========================
        # TEACHER ACCESS
        # ==========================

        elif teacher:


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



    # ==========================
    # FORM VALIDATION
    # ==========================

    def clean(self):

        cleaned_data = super().clean()


        publish_date = cleaned_data.get(
            "publish_date"
        )


        expiry_date = cleaned_data.get(
            "expiry_date"
        )


        if expiry_date and publish_date:

            if expiry_date < publish_date:

                raise ValidationError(
                    "Expiry date cannot be before publish date."
                )


        return cleaned_data