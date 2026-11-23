from django import forms
from .models import Student


MAX_STUDENT_PHOTO_SIZE = 1 * 1024 * 1024  # 1 MB


def validate_student_photo_size(uploaded_file):
    if uploaded_file and uploaded_file.size > MAX_STUDENT_PHOTO_SIZE:
        raise forms.ValidationError(
            "Photo size must not exceed 1 MB. "
            "Please resize or compress the image and try again."
        )


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('dob', 'photo', 'gender')
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make photo optional
        self.fields['photo'].required = False

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        uploaded_photo = self.files.get(self.add_prefix("photo"))

        if uploaded_photo:
            validate_student_photo_size(uploaded_photo)

        return photo



from django import forms
from .models import Announcement


from django import forms
from .models import Announcement
from students.models import SchoolClass, Student


from django import forms


class AnnouncementForm(forms.ModelForm):

    targets = forms.MultipleChoiceField(
        choices=Announcement.TARGET_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    send_channels = forms.MultipleChoiceField(
        choices=Announcement.CHANNEL_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    school_classes = forms.ModelMultipleChoiceField(
        queryset=SchoolClass.objects.none(),
        required=False,
        widget=forms.SelectMultiple
    )

    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.none(),
        required=False,
        widget=forms.SelectMultiple
    )

    class Meta:
        model = Announcement
        fields = [
            "title",
            "message",
            "targets",
            "school_classes",
            "students",
            "send_channels",
            "publish_date",
            "expiry_date",
            "is_active",
        ]

        widgets = {
            "publish_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
            "expiry_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
        }

    def __init__(self,*args,**kwargs):

        school = kwargs.pop("school", None)

        super().__init__(*args, **kwargs)

        if school:
            self.fields["school_classes"].queryset = (
                SchoolClass.objects.filter(school=school)
            )

            self.fields["students"].queryset = (
                Student.objects.filter(
                    school=school
                ).select_related("user")
            )