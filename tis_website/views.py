from django.shortcuts import render, get_object_or_404
import uuid

from .models import (
    SchoolWebsite,
    HomepageContent,
    WhyChooseUs,
    SchoolStatistic
)

from finance.views import activate_student_after_admission_payment
from finance.models import Payment

from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .admin_views import compress_image_to_data_uri

from .models import AdmissionApplication
from students.models import Student
from accounts.models import User
from finance.models import Invoice, PaystackTransaction
from django.contrib.auth.hashers import make_password
import random
import string
from finance.utils import calculate_paystack_fee, send_school_payment_notification
from django.contrib import messages
import requests
from results.utils import portal_required



def get_website(slug):
    """
    Get school website profile using slug
    """

    return get_object_or_404(
        SchoolWebsite,
        slug=slug
    )



def home(request, school_slug):

    website = get_website(
        school_slug
    )

    school = website.school


    homepage = HomepageContent.objects.filter(
        school=school
    ).first()


    why_choose = WhyChooseUs.objects.filter(
        school=school
    )


    statistics = SchoolStatistic.objects.filter(
        school=school
    )


    return render(
        request,
        "tis_website/public/home.html",
        {
            "website": website,
            "homepage": homepage,
            "why_choose": why_choose,
            "statistics": statistics,
        }
    )




def about(request, school_slug):

    website = get_website(
        school_slug
    )


    return render(
        request,
        "tis_website/public/about.html",
        {
            "website": website,
        }
    )





def academics(request, school_slug):

    website = get_website(
        school_slug
    )


    return render(
        request,
        "tis_website/public/academics.html",
        {
            "website": website,
        }
    )





def admissions(request, school_slug):

    website = get_website(
        school_slug
    )


    return render(
        request,
        "tis_website/public/admissions.html",
        {
            "website": website,
        }
    )





def contact(request, school_slug):

    website = get_website(
        school_slug
    )


    return render(
        request,
        "tis_website/public/contact.html",
        {
            "website": website,
        }
    )


from .models import AdmissionApplication

from .forms import AdmissionApplicationForm




def admissions(request, school_slug):

    website = get_object_or_404(
        SchoolWebsite,
        slug=school_slug
    )

    school = website.school

    submitted = False

    application = None

    if request.method == "POST":

        form = AdmissionApplicationForm(
            request.POST,
            request.FILES,
            school=school
        )

        if form.is_valid():

            admission = form.save(
                commit=False
            )

            admission.school = school

            admission.save()

            application = admission

            submitted = True

    else:

        form = AdmissionApplicationForm(
            school=school
        )


    return render(
        request,
        "tis_website/public/admissions.html",
        {
            "form": form,
            "website": website,
            "submitted": submitted,
            "application": application,
        }
    )

from cbt.models import CBTExam, CBTQuestion, CBTSubmission
from django.utils import timezone
from django.http import Http404



from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from cbt.models import CBTSubmission
from .models import AdmissionApplication


def admission_exam_access(request, token):

    application = get_object_or_404(
        AdmissionApplication,
        admission_token=token
    )

    exam = application.admission_exam

    # No examination assigned yet
    if not exam:

        return render(
            request,
            "tis_website/public/exam_not_available.html",
            {
                "application": application,
                "exam": None,
            },
        )

    # Examination exists but is not currently available
    if not exam.is_active():

        return render(
            request,
            "tis_website/public/exam_not_available.html",
            {
                "application": application,
                "exam": exam,
            },
        )

    # Store applicant ID in session
    request.session["admission_application_id"] = application.id

    return redirect(
        "cbt:start_admission_exam",
        exam_id=exam.id
    )  

from django.shortcuts import render, get_object_or_404

from .models import AdmissionApplication

from django.shortcuts import get_object_or_404, render
from finance.models import Invoice
from tis_website.models import AdmissionApplication

def parent_admission_portal(request, token):

    application = get_object_or_404(
        AdmissionApplication,
        admission_token=token
    )


    # Only approved applicants can access portal
    if application.status != "approved":

        return render(
            request,
            "tis_website/public/admission_pending.html",
            {
                "application": application,
                "school": application.school,
            }
        )


    # Get admission invoice
    invoice = (
        Invoice.objects
        .filter(
            admission_application=application,
            is_admission_fee=True
        )
        .order_by("-created_at")
        .first()
    )


    admission_fee_paid = False


    if invoice:

        admission_fee_paid = (
            invoice.amount_paid >= invoice.total_amount
        )


    context = {

        "application": application,

        "school": application.school,

        "invoice": invoice,

        "admission_fee_paid": admission_fee_paid,

    }


    return render(
        request,
        "tis_website/public/admission_parent_portal.html",
        context
    )



from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from io import BytesIO

from xhtml2pdf import pisa

from .models import AdmissionApplication


def download_admission_letter(request, token):

    application = get_object_or_404(
        AdmissionApplication,
        admission_token=token,
        status="approved"
    )


    school = application.school


    # ============================================
    # COMPRESS SCHOOL LOGO
    # ============================================

    logo_data = None

    if school.logo:

        try:

            logo_data = compress_image_to_data_uri(
                school.logo.url,
                max_width=300,
                max_height=300,
                quality=60
            )

        except Exception as e:

            print(
                "PUBLIC LOGO ERROR:",
                e
            )


    # ============================================
    # COMPRESS PRINCIPAL SIGNATURE
    # ============================================

    signature_data = None

    if school.principal_signature:

        try:

            signature_data = compress_image_to_data_uri(
                school.principal_signature.url,
                max_width=400,
                max_height=150,
                quality=60
            )

        except Exception as e:

            print(
                "PUBLIC SIGNATURE ERROR:",
                e
            )


    # ============================================
    # RENDER HTML TEMPLATE
    # ============================================

    html = render_to_string(
        "tis_website/public/admission_letter.html",
        {
            "application": application,
            "school": school,

            "logo_data": logo_data,

            "signature_data": signature_data,
        }
    )


    # ============================================
    # CREATE PDF
    # ============================================

    response = HttpResponse(
        content_type="application/pdf"
    )


    filename = (
        f"{application.student_name}"
        f"_Admission_Letter.pdf"
    )


    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )


    pisa.CreatePDF(
        BytesIO(
            html.encode("UTF-8")
        ),
        dest=response
    )


    return response




from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
import random
import string

from students.models import Student
from finance.models import Invoice
from tis_website.models import AdmissionApplication
from accounts.models import SystemSetting   


User = get_user_model()



def accept_admission(request, token):

    application = get_object_or_404(
        AdmissionApplication,
        admission_token=token
    )


    if request.method == "POST":


        # =====================================
        # ACCEPT ADMISSION
        # =====================================

        application.accepted = True
        application.accepted_on = timezone.now()
        application.status = "approved"
        application.save()



        # =====================================
        # GET CURRENT SESSION AND TERM
        # =====================================

        setting = SystemSetting.objects.first()


        if setting:

            current_session = setting.current_session
            current_term = setting.current_term

        else:

            current_session = "2026/2027"
            current_term = "1"



        # =====================================
        # CREATE TEMPORARY STUDENT ACCOUNT
        # =====================================

        student = None

        username = application.student_username
        password = application.student_password



        if not application.student_created:


            username = application.application_number.lower()


            password = ''.join(
                random.choices(
                    string.ascii_uppercase +
                    string.digits,
                    k=10
                )
            )


            user = User.objects.create(
                username=username,
                first_name=application.student_name.split()[0],
                email=application.parent_email,
                password=make_password(password),
                role="student",
                school=application.school,
                is_active=False
            )


           # =====================================
# ENSURE CLASS EXISTS
# =====================================


            student = Student.objects.create(

                user=user,

                school=application.school,

                admission_no=application.application_number,

                # Temporary student
                # Class assigned after payment confirmation
                school_class=application.class_applying_for,

                dob=application.date_of_birth,

                gender=application.gender,

                parent_name=application.parent_name,

                parent_email=application.parent_email,

                parent_phone=application.parent_phone,

                session=current_session,

                term=current_term

            )


            application.student_created = True


            request.session["student_username"] = username

            request.session["student_password"] = password



        else:


            student = Student.objects.filter(
                admission_no=application.application_number
            ).first()



        # =====================================
        # CREATE ADMISSION FEE INVOICE
        # =====================================

        if not application.invoice_generated:


            Invoice.objects.get_or_create(

                student=student,

                admission_application=application,

                title="Admission Fees",

                defaults={

                    "school": application.school,

                    "school_class": application.class_applying_for,

                    "total_amount": application.school.admission_fee,

                    "amount_paid": 0,

                    "session":current_session,

                    "term":current_term,

        

                    "is_admission_fee":True,


                    "due_date": timezone.now().date(),

                }

            )


            application.invoice_generated = True



        # Save credentials
        if username and password:

            application.student_username = username

            application.student_password = password



        application.save()



        return redirect(
            "tis_website:acceptance_success",
            token=application.admission_token
        )



    return render(

        request,

        "tis_website/public/accept_admission.html",

        {
            "application": application
        }

    )


def acceptance_success(request, token):

    application = get_object_or_404(
        AdmissionApplication,
        admission_token=token
    )


    return render(
        request,
        "tis_website/public/acceptance_success.html",
        {
            "application": application,
            "school": application.school
        }
    )


from django.shortcuts import render, get_object_or_404

from decimal import Decimal
import requests

from django.shortcuts import (
    render,
    get_object_or_404,
    redirect
)
from django.contrib import messages
from django.urls import reverse

from finance.models import (
    Invoice,
    PaystackTransaction
)

from .models import AdmissionApplication



def admission_payment(request, token):

    application = get_object_or_404(
        AdmissionApplication,
        admission_token=token
    )


    invoice = get_object_or_404(
        Invoice,
        admission_application=application,
        is_admission_fee=True
    )


    if request.method == "POST":

        if invoice.status == "PAID":

            return redirect(
                "tis_website:parent_admission_portal",
                token=token
            )


        school = application.school


        email = (
            application.parent_email
            or "techcenter652@gmail.com"
        )


        amount = invoice.outstanding


        transaction = PaystackTransaction.objects.create(
            school=school,
            invoice=invoice,
            amount=amount,
            status="pending",
            paystack_reference=f"TEMP-{uuid.uuid4().hex}",
            metadata={
                "payment_type": "admission_fee",
                "application_id": application.id
            }
        )


        callback_url = request.build_absolute_uri(
            reverse(
                "tis_website:admission_payment_verify",
                args=[invoice.id]
            )
        )


        payload = {

            "email": email,

            "amount": int(amount * 100),

            "callback_url": callback_url,

            "metadata": {

                "invoice_id": invoice.id,

                "transaction_id": transaction.id,

                "school_id": school.id,

                "payment_type": "admission_fee",

            }

        }


        headers = {

            "Authorization":
            f"Bearer {school.paystack_secret_key}",

            "Content-Type":
            "application/json"

        }


        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers=headers
        )


        data = response.json()


        if data.get("status"):

            transaction.paystack_reference = (
                data["data"]["reference"]
            )

            transaction.save(
                update_fields=[
                    "paystack_reference"
                ]
            )


            return redirect(
                data["data"]["authorization_url"]
            )


        messages.error(
            request,
            "Unable to initialize payment."
        )


    return render(
        request,
        "tis_website/public/admission_payment.html",
        {
            "application":application,
            "invoice":invoice,
            "school":application.school
        }
    )





def admission_payment_verify(request, invoice_id):


    invoice = get_object_or_404(
        Invoice,
        id=invoice_id,
        is_admission_fee=True
    )


    reference = request.GET.get(
        "reference"
    )


    if not reference:

        messages.warning(
            request,
            "Payment reference missing."
        )

        return redirect(
            "tis_website:parent_admission_portal",
            token=invoice.admission_application.admission_token
        )



    transaction = get_object_or_404(
        PaystackTransaction,
        paystack_reference=reference,
        invoice=invoice
    )


    school = invoice.school



    response = requests.get(

        f"https://api.paystack.co/transaction/verify/{reference}",

        headers={
            "Authorization":
            f"Bearer {school.paystack_secret_key}"
        }

    )


    data = response.json()


    if data.get("status") and data["data"]["status"] == "success":


        transaction.status = "success"

        transaction.save(
            update_fields=[
                "status"
            ]
        )


        # Create student account after successful payment

        payment = Payment.objects.filter(
            invoice=invoice
        ).first()


        if payment:

            activate_student_after_admission_payment(payment)

        messages.success(
            request,
            "Payment successful. Student Account Created."
        )


    else:

        messages.warning(
            request,
            "Payment verification pending."
        )


    return redirect(

        "tis_website:parent_admission_portal",

        token=invoice.admission_application.admission_token

    )


from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import AdmissionApplication

from students.models import Student

def student_login_details(request, token):

    application = get_object_or_404(
        AdmissionApplication,
        admission_token=token
    )

    invoice = (
        Invoice.objects.filter(
            admission_application=application,
            is_admission_fee=True
        )
        .order_by("-created_at")
        .first()
    )

    if not invoice or invoice.amount_paid < invoice.total_amount:
        return HttpResponse(
            "Admission fee payment required before account creation."
        )

    student = Student.objects.filter(
        admission_no=application.application_number
    ).first()

    if not student:
        return HttpResponse(
            "Student account has not been created yet."
        )

    return render(
        request,
        "tis_website/public/student_login_details.html",
        {
            "application": application,
            "student": student,
            "school": application.school,
             "password": application.student_password,
        }
    )