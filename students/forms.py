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


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = [
            "title",
            "message",
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