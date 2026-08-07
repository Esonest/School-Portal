from django import forms

from .models import (
    SchoolWebsite,
    HomepageContent
)



# =====================================================
# SCHOOL WEBSITE PROFILE FORM
# =====================================================


class SchoolWebsiteForm(forms.ModelForm):


    class Meta:

        model = SchoolWebsite


        fields = [

            "motto",

            "vision",

            "mission",

            "history",

            "principal_name",

            "principal_photo",

            "principal_message",

            "address",

            "phone",

            "email",

            "facebook",

            "instagram",

            "whatsapp",

        ]



        widgets = {


            "motto": forms.TextInput(
                attrs={
                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",
                    "placeholder":
                    "Enter school motto"
                }
            ),



            "vision": forms.Textarea(
                attrs={
                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",
                    "rows":
                    5,
                    "placeholder":
                    "Write school vision statement"
                }
            ),



            "mission": forms.Textarea(
                attrs={
                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",
                    "rows":
                    5,
                    "placeholder":
                    "Write school mission statement"
                }
            ),



            "history": forms.Textarea(
                attrs={
                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",
                    "rows":
                    6,
                    "placeholder":
                    "Tell the story of your school"
                }
            ),




            "principal_name": forms.TextInput(
                attrs={
                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",
                    "placeholder":
                    "Principal name"
                }
            ),




            "principal_photo": forms.FileInput(
                attrs={
                    "class":
                    "w-full rounded-xl border border-gray-200 bg-gray-50 p-3"
                }
            ),





            "principal_message": forms.Textarea(
                attrs={
                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",
                    "rows":
                    7,
                    "placeholder":
                    "Principal welcome message"
                }
            ),





            "address": forms.Textarea(
                attrs={
                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",
                    "rows":
                    3,
                    "placeholder":
                    "School address"
                }
            ),





            "phone": forms.TextInput(
                attrs={
                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",
                    "placeholder":
                    "School phone number"
                }
            ),





            "email": forms.EmailInput(
                attrs={
                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",
                    "placeholder":
                    "School email address"
                }
            ),





            "facebook": forms.URLInput(
                attrs={
                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",
                    "placeholder":
                    "Facebook page URL"
                }
            ),





            "instagram": forms.URLInput(
                attrs={
                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",
                    "placeholder":
                    "Instagram page URL"
                }
            ),





            "whatsapp": forms.TextInput(
                attrs={
                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",
                    "placeholder":
                    "WhatsApp contact number"
                }
            ),

        }





# =====================================================
# HOMEPAGE CONTENT FORM
# =====================================================



class HomepageContentForm(forms.ModelForm):


    class Meta:


        model = HomepageContent



        fields = [

            "hero_title",

            "hero_subtitle",

            "hero_image",

            "primary_button_text",

            "primary_button_link",

            "secondary_button_text",

            "secondary_button_link",

        ]



        widgets = {



            "hero_title": forms.TextInput(

                attrs={

                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",

                    "placeholder":
                    "Main homepage heading"

                }

            ),





            "hero_subtitle": forms.Textarea(

                attrs={

                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",

                    "rows":
                    4,

                    "placeholder":
                    "Homepage introduction text"

                }

            ),





            "hero_image": forms.FileInput(

                attrs={

                    "class":
                    "w-full rounded-xl border border-gray-200 bg-gray-50 p-3"

                }

            ),





            "primary_button_text": forms.TextInput(

                attrs={

                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",

                    "placeholder":
                    "Example: Apply Now"

                }

            ),





            "primary_button_link": forms.TextInput(

                attrs={

                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",

                    "placeholder":
                    "Example: /admissions/"

                }

            ),





            "secondary_button_text": forms.TextInput(

                attrs={

                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",

                    "placeholder":
                    "Example: Learn More"

                }

            ),





            "secondary_button_link": forms.TextInput(

                attrs={

                    "class":
                    "w-full rounded-xl border-gray-200 bg-gray-50 p-3 focus:ring-2 focus:ring-blue-500",

                    "placeholder":
                    "Example: /about/"

                }

            ),



        }


from django import forms
from .models import NewsEvent



class NewsEventForm(forms.ModelForm):

    class Meta:

        model = NewsEvent

        fields = [

            "title",
            "image",
            "content",
            "event_date",
            "is_published",

        ]



        widgets = {


            "title": forms.TextInput(
                attrs={
                    "class":
                    "w-full rounded-xl border p-3"
                }
            ),


            "content": forms.Textarea(
                attrs={
                    "class":
                    "w-full rounded-xl border p-3",
                    "rows":8
                }
            ),


            "event_date": forms.DateInput(
                attrs={
                    "type":"date",
                    "class":
                    "w-full rounded-xl border p-3"
                }
            ),

            "image": forms.ClearableFileInput(
                attrs={
                    "class":
                    "w-full border rounded-xl p-3 bg-gray-50"
                }
            ),


        }        


from .models import Gallery



class GalleryForm(forms.ModelForm):


    class Meta:

        model = Gallery


        fields = [

            "title",
            "image",
            "description",
            "is_published",

        ]



        widgets = {


            "title": forms.TextInput(
                attrs={
                    "class":
                    "w-full border rounded-xl p-3",
                    "placeholder":
                    "Gallery title"
                }
            ),



            "description": forms.Textarea(
                attrs={
                    "class":
                    "w-full border rounded-xl p-3",
                    "rows":5,
                    "placeholder":
                    "Image description"
                }
            ),



            "image": forms.ClearableFileInput(
                attrs={
                    "class":
                    "w-full border rounded-xl p-3 bg-gray-50"
                }
            )

        }  




from django import forms
from .models import AdmissionApplication
from students.models import SchoolClass


class AdmissionApplicationForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):

        school = kwargs.pop("school", None)

        super().__init__(*args, **kwargs)


        if school:

            self.fields["class_applying_for"].queryset = SchoolClass.objects.filter(
                school=school
            )

        else:

            self.fields["class_applying_for"].queryset = SchoolClass.objects.none()

    class Meta:

        model = AdmissionApplication

        fields = [
            # ----------------------------
            # Student Information
            # ----------------------------
            "student_name",
            "student_email",
            "date_of_birth",
            "gender",
            "class_applying_for",

            # ----------------------------
            # Parent Information
            # ----------------------------
            "parent_name",
            "parent_phone",
            "parent_email",
            "address",

            # ----------------------------
            # Academic Information
            # ----------------------------
            "previous_school",

            # ----------------------------
            # Uploads
            # ----------------------------
            "passport",
            "document",
        ]

        widgets = {

            # -----------------------------------
            # STUDENT INFORMATION
            # -----------------------------------

            "student_name": forms.TextInput(
                attrs={
                    "class": "w-full border rounded-xl p-3",
                    "placeholder": "Enter student's full name"
                }
            ),

            "student_email": forms.EmailInput(
                attrs={
                    "class": "w-full border rounded-xl p-3",
                    "placeholder": "Student email (optional)"
                }
            ),

            "date_of_birth": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full border rounded-xl p-3"
                }
            ),

            "gender": forms.Select(
                attrs={
                    "class": "w-full border rounded-xl p-3"
                }
            ),

            "class_applying_for": forms.Select(
                attrs={
                    "class": "w-full border rounded-xl p-3"
                }
            ),

            # -----------------------------------
            # PARENT INFORMATION
            # -----------------------------------

            "parent_name": forms.TextInput(
                attrs={
                    "class": "w-full border rounded-xl p-3",
                    "placeholder": "Parent/Guardian Full Name"
                }
            ),

            "parent_phone": forms.TextInput(
                attrs={
                    "class": "w-full border rounded-xl p-3",
                    "placeholder": "WhatsApp / Mobile Number"
                }
            ),

            "parent_email": forms.EmailInput(
                attrs={
                    "class": "w-full border rounded-xl p-3",
                    "placeholder": "Parent Email Address"
                }
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "w-full border rounded-xl p-3",
                    "rows": 4,
                    "placeholder": "Residential Address"
                }
            ),

            # -----------------------------------
            # ACADEMIC INFORMATION
            # -----------------------------------

            "previous_school": forms.TextInput(
                attrs={
                    "class": "w-full border rounded-xl p-3",
                    "placeholder": "Previous School (if any)"
                }
            ),

            # -----------------------------------
            # UPLOADS
            # -----------------------------------

            "passport": forms.ClearableFileInput(
                attrs={
                    "class": "w-full border rounded-xl p-3"
                }
            ),

            "document": forms.ClearableFileInput(
                attrs={
                    "class": "w-full border rounded-xl p-3"
                }
            ),
        }

        labels = {

            "student_name": "Student Full Name",
            "student_email": "Student Email",
            "date_of_birth": "Date of Birth",
            "gender": "Gender",
            "class_applying_for": "Class Applying For",

            "parent_name": "Parent / Guardian Name",
            "parent_phone": "WhatsApp / Phone Number",
            "parent_email": "Parent Email",
            "address": "Home Address",

            "previous_school": "Previous School",

            "passport": "Passport Photograph",
            "document": "Birth Certificate / Previous Result (Optional)",
        }

        help_texts = {

            "parent_phone": "This number will receive admission updates via WhatsApp.",

            "parent_email": "Admission letters and student login credentials will be sent here.",

            "student_email": "Optional. Used for student notifications if available.",

            "passport": "Upload a recent passport photograph.",

            "document": "Upload birth certificate, previous result or any supporting document."
        }            


from cbt.models import CBTExam
from .models import AdmissionApplication


from django import forms
from cbt.models import CBTExam
from results.utils import SESSION_LIST
from .models import AdmissionApplication


class AdmissionExamAssignmentForm(forms.ModelForm):

    admission_exam = forms.ModelChoiceField(
        queryset=CBTExam.objects.none(),
        empty_label="Select Admission Exam",
        required=True,
        widget=forms.Select(
            attrs={
                "class": "w-full border rounded-xl p-3"
            }
        )
    )

    admission_session = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(
            attrs={
                "class": "w-full border rounded-xl p-3"
            }
        )
    )

    admission_term = forms.ChoiceField(
        required=True,
        choices=[
            ("1", "First Term"),
            ("2", "Second Term"),
            ("3", "Third Term"),
        ],
        widget=forms.Select(
            attrs={
                "class": "w-full border rounded-xl p-3"
            }
        )
    )

    resume_date = forms.DateField(
        required=True,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "w-full border rounded-xl p-3"
            }
        )
    )

    class Meta:
        model = AdmissionApplication
        fields = [
            "admission_exam",
            "admission_session",
            "admission_term",
            "resume_date",
        ]

    def __init__(self, *args, school=None, **kwargs):

        super().__init__(*args, **kwargs)

        # Admission examinations belonging to this school
        if school:
            self.fields["admission_exam"].queryset = CBTExam.objects.filter(
                school=school,
                exam_type="admission"
            )

        # Academic sessions
        self.fields["admission_session"].choices = [
            ("", "Select Academic Session")
        ] + [
            (session, session)
            for session in SESSION_LIST
        ]