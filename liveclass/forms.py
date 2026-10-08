from django import forms
from django.apps import apps
from .models import LiveClass

# Lazy-load models once
Subject = apps.get_model("results", "Subject")
SchoolClass = apps.get_model("students", "SchoolClass")
Teacher = apps.get_model("accounts", "Teacher")

class LiveClassForm(forms.ModelForm):

    subject = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        required=True,
        widget=forms.CheckboxSelectMultiple()
    )

    class_room = forms.ModelMultipleChoiceField(
        queryset=SchoolClass.objects.none(),
        required=True,
        widget=forms.CheckboxSelectMultiple()
    )

    teacher = forms.ModelMultipleChoiceField(
        queryset=Teacher.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    class Meta:
        model = LiveClass

        fields = [
            "subject",
            "class_room",
            "teacher",
            "title",
            "description",
            "start_time",
            "end_time",
        ]

        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
            "end_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
        }

    def __init__(self, *args, **kwargs):

        school = kwargs.pop("school", None)
        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        self._user = user

        # ======================================================
        # FILTER BY SCHOOL
        # ======================================================

        if school:

            self.fields["subject"].queryset = (
                Subject.objects.filter(
                    school=school
                )
            )

            self.fields["class_room"].queryset = (
                SchoolClass.objects.filter(
                    school=school
                )
            )

            self.fields["teacher"].queryset = (
                Teacher.objects.filter(
                    school=school
                )
            )

        # ======================================================
        # TEACHER USER
        # ======================================================

        if user and getattr(
            user,
            "is_teacher_user",
            False
        ):

            teacher_profile = getattr(
                user,
                "teacher_profile",
                None
            )

            if teacher_profile:

                self.fields["teacher"].queryset = (
                    self.fields["teacher"].queryset.filter(
                        pk=teacher_profile.pk
                    )
                )

                self.fields["teacher"].initial = [
                    teacher_profile.pk
                ]

                self.fields["teacher"].widget = (
                    forms.MultipleHiddenInput()
                )

        # ======================================================
        # EDITING
        # ======================================================

        if self.instance.pk:

            self.fields["subject"].initial = (
                self.instance.subject.all()
            )

            self.fields["class_room"].initial = (
                self.instance.class_room.all()
            )

            self.fields["teacher"].initial = (
                self.instance.teacher.all()
            )

        self.apply_tailwind()

    # ==========================================================
    # TEACHER SECURITY VALIDATION
    # ==========================================================

    def clean_teacher(self):

        teachers = self.cleaned_data.get(
            "teacher"
        )

        user = getattr(
            self,
            "_user",
            None
        )

        if user and getattr(
            user,
            "is_teacher_user",
            False
        ):

            teacher_profile = getattr(
                user,
                "teacher_profile",
                None
            )

            if teacher_profile:

                if set(
                    teachers.values_list(
                        "id",
                        flat=True
                    )
                ) != {teacher_profile.id}:

                    raise forms.ValidationError(
                        "You can only assign yourself as the teacher."
                    )

        return teachers

    # ==========================================================
    # TAILWIND
    # ==========================================================

    def apply_tailwind(self):

        normal_class = (
            "w-full border border-gray-300 rounded-xl "
            "p-3 bg-white "
            "focus:ring-2 focus:ring-blue-400 "
            "focus:border-blue-400 outline-none"
        )

        multiple_class = (
            "w-full border border-gray-200 rounded-2xl "
            "p-4 bg-gray-50 "
            "focus:ring-2 focus:ring-blue-400"
        )

        for name, field in self.fields.items():

            if isinstance(
                field.widget,
                (
                    forms.CheckboxSelectMultiple,
                    forms.MultipleHiddenInput,
                )
            ):

                field.widget.attrs.update({
                    "class": multiple_class
                })

            else:

                field.widget.attrs.update({
                    "class": normal_class
                })

    def save(
        self,
        commit=True
    ):

        instance = super().save(
            commit=commit
        )

        return instance



# ==========================================================
# PUBLIC EVENT FORM
# ==========================================================

from django import forms
from django.utils import timezone

from .models import LiveClass


class PublicEventForm(forms.ModelForm):

    subject = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    class_room = forms.ModelMultipleChoiceField(
        queryset=SchoolClass.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    class Meta:
        model = LiveClass

        fields = [
            "title",
            "event_description",
            "subject",
            "class_room",
            "start_time",
            "end_time",
            "guest_max_count",
            "record_public_event",
        ]

        widgets = {

            "title": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border-gray-300",
                    "placeholder": "Event title",
                }
            ),

            "event_description": forms.Textarea(
                attrs={
                    "class": "w-full rounded-lg border-gray-300",
                    "rows": 4,
                    "placeholder": "Describe the event",
                }
            ),

            "start_time": forms.DateTimeInput(
                attrs={
                    "class": "w-full rounded-lg border-gray-300",
                    "type": "datetime-local",
                }
            ),

            "end_time": forms.DateTimeInput(
                attrs={
                    "class": "w-full rounded-lg border-gray-300",
                    "type": "datetime-local",
                }
            ),

            "guest_max_count": forms.NumberInput(
                attrs={
                    "class": "w-full rounded-lg border-gray-300",
                    "min": "1",
                    "placeholder": "Leave blank for unlimited",
                }
            ),

            "record_public_event": forms.CheckboxInput(
                attrs={
                    "class": "rounded",
                }
            ),
        }

    def __init__(
        self,
        *args,
        school=None,
        user=None,
        **kwargs
    ):

        super().__init__(*args, **kwargs)

        self.school = school
        self.user = user

        # ------------------------------------------------------
        # LIMIT TO THIS SCHOOL
        # ------------------------------------------------------

        if school is not None:

            self.fields["class_room"].queryset = (
                SchoolClass.objects.filter(
                    school=school
                )
            )

            self.fields["subject"].queryset = (
                Subject.objects.filter(
                    school=school
                )
            )

        # ------------------------------------------------------
        # EDITING
        # ------------------------------------------------------

        if self.instance.pk:

            self.fields["subject"].initial = (
                self.instance.subject.all()
            )

            self.fields["class_room"].initial = (
                self.instance.class_room.all()
            )