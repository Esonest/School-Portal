from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .decorators import website_admin_required

from django.shortcuts import render, redirect
from django.contrib import messages

from .models import SchoolWebsite
from .forms import SchoolWebsiteForm
from django.urls import reverse

from .decorators import website_admin_required
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from .utils import send_admission_email, send_admission_whatsapp



@login_required
@website_admin_required
def website_dashboard(request):

    return render(
        request,
        "tis_website/admin/dashboard.html"
    )




@login_required
@website_admin_required
def website_profile(request):

    website, created = SchoolWebsite.objects.get_or_create(

        school=request.user.school

    )


    if request.method == "POST":


        form = SchoolWebsiteForm(

            request.POST,

            request.FILES,

            instance=website

        )


        if form.is_valid():

            form.save()


            messages.success(
                request,
                "Website profile updated successfully."
            )


            return redirect(
                "tis_website_admin:profile"
            )


    else:


        form = SchoolWebsiteForm(
            instance=website
        )



    return render(

        request,

        "tis_website/admin/profile.html",

        {

            "form": form,

            "website": website

        }

    )


from .models import HomepageContent
from .forms import HomepageContentForm



@login_required
@website_admin_required
def homepage_settings(request):

    homepage, created = HomepageContent.objects.get_or_create(

        school=request.user.school

    )


    if request.method == "POST":


        form = HomepageContentForm(

            request.POST,

            request.FILES,

            instance=homepage

        )


        if form.is_valid():

            form.save()


            messages.success(
                request,
                "Homepage updated successfully."
            )


            return redirect(
                "tis_website_admin:homepage"
            )


    else:

        form = HomepageContentForm(
            instance=homepage
        )


    return render(

        request,

        "tis_website/admin/homepage.html",

        {
            "form":form
        }
    )


from django.shortcuts import render, redirect, get_object_or_404

from .models import NewsEvent

from .forms import NewsEventForm

from accounts.models import School



def news_list(request):

    school = request.user.school


    news = NewsEvent.objects.filter(
        school=school
    )


    return render(

        request,

        "tis_website/admin/news_list.html",

        {
            "news":news
        }

    )






def news_create(request):

    school = request.user.school



    if request.method == "POST":


        form = NewsEventForm(
            request.POST,
            request.FILES
        )


        if form.is_valid():

            news = form.save(
                commit=False
            )


            news.school = school


            news.save()


            return redirect(
                "tis_website_admin:news_list"
            )



    else:

        form = NewsEventForm()



    return render(

        request,

        "tis_website/admin/news_form.html",

        {
            "form":form
        }

    )







def news_update(request, pk):


    school = request.user.school


    news = get_object_or_404(

        NewsEvent,

        id=pk,

        school=school

    )



    form = NewsEventForm(

        request.POST or None,

        request.FILES or None,

        instance=news

    )



    if form.is_valid():

        form.save()


        return redirect(
            "tis_website_admin:news_list"
        )




    return render(

        request,

        "tis_website/admin/news_form.html",

        {
            "form":form
        }

    )









def news_delete(request, pk):


    school=request.user.school


    news=get_object_or_404(

        NewsEvent,

        id=pk,

        school=school

    )


    news.delete()


    return redirect(

        "tis_website_admin:news_list"

    )


from .models import Gallery

from .forms import GalleryForm




def gallery_list(request):

    school = request.user.school


    gallery = Gallery.objects.filter(
        school=school
    )


    return render(

        request,

        "tis_website/admin/gallery_list.html",

        {
            "gallery":gallery
        }

    )







def gallery_create(request):

    school = request.user.school


    if request.method == "POST":


        form = GalleryForm(

            request.POST,

            request.FILES

        )


        if form.is_valid():


            item=form.save(
                commit=False
            )


            item.school=school


            item.save()



            return redirect(
                "tis_website_admin:gallery_list"
            )



    else:

        form=GalleryForm()



    return render(

        request,

        "tis_website/admin/gallery_form.html",

        {
            "form":form
        }

    )









def gallery_update(request,pk):


    school=request.user.school



    item=get_object_or_404(

        Gallery,

        id=pk,

        school=school

    )




    form=GalleryForm(

        request.POST or None,

        request.FILES or None,

        instance=item

    )




    if form.is_valid():

        form.save()


        return redirect(
            "tis_website_admin:gallery_list"
        )





    return render(

        request,

        "tis_website/admin/gallery_form.html",

        {
            "form":form
        }

    )









def gallery_delete(request,pk):


    school=request.user.school



    item=get_object_or_404(

        Gallery,

        id=pk,

        school=school

    )


    item.delete()



    return redirect(

        "tis_website_admin:gallery_list"

    )


from .models import AdmissionApplication




def admission_list(request):


    school=request.user.school



    applications = AdmissionApplication.objects.filter(

        school=school

    )



    return render(

        request,

        "tis_website/admin/admission_list.html",

        {

            "applications":applications

        }

    )






from django.utils import timezone


from django.utils import timezone
from django.urls import reverse
from django.core.mail import EmailMessage
from django.conf import settings

from .utils import generate_admission_letter_pdf

def admission_update_status(request, pk, status):

    allowed_status = [
        "approved",
        "rejected",
    ]

    if status not in allowed_status:
        return redirect(
            "tis_website_admin:admission_list"
        )


    school = request.user.school


    application = get_object_or_404(
        AdmissionApplication,
        id=pk,
        school=school
    )


    application.status = status


    # ======================================
    # APPROVAL PROCESS
    # ======================================

    if status == "approved":

        from django.utils import timezone

        application.approved_on = timezone.now()

        application.admission_letter_generated = True


        # Generate acceptance link
        acceptance_link = request.build_absolute_uri(
            reverse(
                "tis_website:accept_admission",
                args=[
                    application.admission_token
                ]
            )
        )


        message = f"""

Dear {application.parent_name},

Congratulations!

Your child {application.student_name}
has been offered admission into:

{application.school.name}


Class:
{application.class_applying_for}


To continue the admission process, please accept your admission offer using the link below:

{acceptance_link}


Application Number:

{application.application_number}


Thank you.

{application.school.name}

"""


        # WhatsApp

        try:

            from students.services.whatsapp_service import send_whatsapp_message


            send_whatsapp_message(
                application.parent_phone,
                message=message
            )


        except Exception as e:

            print("WhatsApp approval error:", e)



        # Email

        try:

            from students.services.email_service import send_brevo_email


            send_brevo_email(

                to_email=application.parent_email,

                to_name=application.parent_name,

                subject="Admission Offer Accepted",

                html_content=message.replace(
                    "\n",
                    "<br>"
                ),

                school=application.school

            )


        except Exception as e:

            print("Email approval error:", e)



    application.save()


    return redirect(
        "tis_website_admin:admission_list"
    )


from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)


from .models import AdmissionApplication

from .forms import AdmissionExamAssignmentForm




def assign_admission_exam(request, pk):

    print("VIEW HIT")
    print("METHOD:", request.method)

    application = get_object_or_404(
        AdmissionApplication,
        id=pk,
        school=request.user.school
    )


    if request.method == "POST":

        print("POST:", request.POST)

        form = AdmissionExamAssignmentForm(
            request.POST,
            instance=application,
            school=request.user.school
        )


        print("VALID:", form.is_valid())


        if form.is_valid():

            admission = form.save(commit=False)

            print(
                "Exam selected:",
                admission.admission_exam
            )


            admission.status = "exam_assigned"

            admission.save()



            # ============================================
            # SEND CBT LINK TO PARENT
            # ============================================

            exam_link = request.build_absolute_uri(
                reverse(
                    "tis_website:admission_exam_access",
                    args=[admission.admission_token]
                )
            )


            tracking_link = request.build_absolute_uri(
                "/admission/track/"
            )



            whatsapp_message = f"""
Dear {admission.parent_name},

Your child {admission.student_name} has been scheduled for the Admission CBT Examination.

School:
{admission.school.name}

Examination:
{admission.admission_exam.title}

Duration:
{admission.admission_exam.duration_minutes} Minutes

Exam Link:
{exam_link}

Track your admission:
{tracking_link}

Application Number:
{admission.application_number}

Please save your application number for future reference.

Ensure you have a stable internet connection before starting the examination.

Thank you.

{admission.school.name}
"""



            html_message = f"""
<html>
<body style="font-family:Arial,sans-serif;line-height:1.7;">

<h2>
Admission CBT Examination
</h2>


<p>
Dear <strong>{admission.parent_name}</strong>,
</p>


<p>
Your child
<strong>{admission.student_name}</strong>
has been scheduled for the Admission CBT Examination.
</p>


<p>
<strong>School:</strong>
{admission.school.name}
</p>


<p>
<strong>Examination:</strong>
{admission.admission_exam.title}
</p>


<p>
<strong>Duration:</strong>
{admission.admission_exam.duration_minutes}
Minutes
</p>


<p>
<strong>Application Number:</strong>
{admission.application_number}
</p>


<p>
<a href="{exam_link}">
Start Admission Examination
</a>
</p>


<p>
Exam Link:
<br>
{exam_link}
</p>


<p>
Track Admission:
<br>
{tracking_link}
</p>


<p>
Thank you.
<br>
<strong>{admission.school.name}</strong>
</p>


</body>
</html>
"""



            # ============================================
            # WHATSAPP
            # ============================================

            try:

                from students.services.whatsapp_service import send_whatsapp_message


                success, response = send_whatsapp_message(
                    admission.parent_phone,
                    message=whatsapp_message
                )


                print(
                    "WHATSAPP SUCCESS:",
                    success
                )

                print(
                    "WHATSAPP RESPONSE:",
                    response
                )


            except Exception as e:

                print(
                    "WHATSAPP ERROR:",
                    e
                )



            # ============================================
            # EMAIL
            # ============================================

            try:

                from students.services.email_service import send_brevo_email


                success, response = send_brevo_email(

                    to_email=admission.parent_email,

                    to_name=admission.parent_name,

                    subject="Admission CBT Examination Link",

                    html_content=html_message,

                    school=admission.school

                )


                print(
                    "EMAIL SUCCESS:",
                    success
                )


                print(
                    "EMAIL RESPONSE:",
                    response
                )



            except Exception as e:

                print(
                    "EMAIL ERROR:",
                    e
                )



            return redirect(
                "tis_website_admin:admission_list"
            )



        else:

            print(
                form.errors
            )



    else:


        form = AdmissionExamAssignmentForm(

            instance=application,

            school=request.user.school

        )



    return render(

        request,

        "tis_website/admin/assign_admission_exam.html",

        {

            "application": application,

            "form": form

        }

    )


@login_required
def admission_detail(request, pk):

    application = get_object_or_404(
        AdmissionApplication,
        id=pk,
        school=request.user.school
    )

    return render(
        request,
        "tis_website/admin/admission_detail.html",
        {
            "application": application,
        }
    )

from django.shortcuts import render, get_object_or_404
from .models import AdmissionApplication


def admission_track(request):

    application = None
    error = None


    if request.method == "POST":

        application_number = request.POST.get(
            "application_number"
        )


        try:

            application = AdmissionApplication.objects.get(
                application_number=application_number
            )


        except AdmissionApplication.DoesNotExist:

            error = "Invalid application number."


    exam_link = None


    if application and application.admission_exam:

        exam_link = request.build_absolute_uri(
            reverse(
                "tis_website:admission_exam_access",
                args=[
                    application.admission_token
                ]
            )
        )


    return render(
        request,
        "tis_website/admin/admission_track.html",
        {
            "application": application,
            "error": error,
            "exam_link": exam_link,
        }
    )


@login_required
def download_admission_letter(request, pk):

    application = get_object_or_404(
        AdmissionApplication,
        id=pk,
        school=request.user.school,
        status="approved"
    )


    template = get_template(
        "tis_website/admin/admission_letter.html"
    )


    html = template.render(
        {
            "application": application,
            "school": application.school,
        }
    )


    response = HttpResponse(
        content_type="application/pdf"
    )

    response[
        "Content-Disposition"
    ] = (
        f'attachment; filename="'
        f'{application.student_name}_Admission_Letter.pdf"'
    )


    pisa.CreatePDF(
        BytesIO(html.encode("UTF-8")),
        dest=response
    )


    return response