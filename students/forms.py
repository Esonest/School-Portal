from django import forms
from .models import Student


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

    def __init__(self,*args,**kwargs):

        school = kwargs.pop(
            "school",
            None
        )

        super().__init__(
            *args,
            **kwargs
        )

        if school:

            self.fields[
                "school_classes"
            ].queryset = (
                SchoolClass.objects.filter(
                    school=school
                )
            )

            self.fields[
                "students"
            ].queryset = (
                Student.objects.filter(
                    school=school
                ).select_related("user")
            )