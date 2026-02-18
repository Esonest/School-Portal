from django import forms
from django.apps import apps
from .models import LiveClass

# Lazy-load models once
Subject = apps.get_model("results", "Subject")
SchoolClass = apps.get_model("students", "SchoolClass")
Teacher = apps.get_model("accounts", "Teacher")


class LiveClassForm(forms.ModelForm):
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.none(),
        required=False
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
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        school = kwargs.pop("school", None)
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filter queryset by school
        if school:
            self.fields["subject"].queryset = Subject.objects.filter(school=school)
            self.fields["class_room"].queryset = SchoolClass.objects.filter(school=school)
            self.fields["teacher"].queryset = Teacher.objects.filter(school=school)

        # If user is a teacher, auto-assign them
        if user and getattr(user, "is_teacher_user", False):
            # Hide the field
            self.fields["teacher"].widget = forms.HiddenInput()
            self.fields["teacher"].required = False

            # If creating a new instance, set teacher automatically
            if not self.instance.pk:
                teacher_profile = getattr(user, "teacher_profile", None)
                if teacher_profile:
                    self.instance.teacher = teacher_profile

        # Apply Tailwind styling to remaining fields
        self.apply_tailwind()

    def apply_tailwind(self):
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "w-full border rounded-lg p-2 focus:ring-2 focus:ring-blue-400"
            })
