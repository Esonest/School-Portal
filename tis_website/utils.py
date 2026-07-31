from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO
from students.services.whatsapp_service import format_phone


def generate_admission_letter_pdf(application):

    html = render_to_string(
        "tis_website/pubblic/admission_letter.html",
        {
            "application": application,
            "school": application.school
        }
    )


    pdf_buffer = BytesIO()


    pisa.CreatePDF(
        html,
        dest=pdf_buffer
    )


    pdf_buffer.seek(0)


    return pdf_buffer

from django.core.mail import EmailMessage



def send_admission_email(
        application,
        portal_link
):


    pdf = generate_admission_letter_pdf(
        application
    )


    subject = (
        "Admission Offer - "
        f"{application.school.name}"
    )


    message = f"""

Dear {application.parent_name},


Congratulations!


Your child:

{application.student_name}


has been offered admission into:

{application.class_applying_for}



You can access your admission portal here:


{portal_link}



From the portal you can:

- Download admission letter
- View admission details
- Get further instructions



Thank you.



{application.school.name}

"""


    email = EmailMessage(

        subject,

        message,

        settings.DEFAULT_FROM_EMAIL,

        [
            application.parent_email
        ]

    )


    email.attach(

        f"{application.student_name}_Admission_Letter.pdf",

        pdf.read(),

        "application/pdf"

    )


    email.send(
        fail_silently=False
    )


import requests
from django.conf import settings



def send_admission_whatsapp(
        application,
        portal_link
):


    phone = application.parent_phone


    message = f"""

Congratulations {application.parent_name} 🎉


Your child {application.student_name}
has been offered admission into
{application.class_applying_for}.


View your admission portal here:


{portal_link}



Thank you.

{application.school.name}

"""


    url = (
        f"https://graph.facebook.com/"
        f"v22.0/"
        f"{settings.WHATSAPP_PHONE_ID}/messages"
    )


    headers = {

        "Authorization":
        f"Bearer {settings.WHATSAPP_TOKEN}",

        "Content-Type":
        "application/json"

    }


    payload = {

        "messaging_product":
        "whatsapp",


        "to":
        format_phone(phone),


        "type":
        "text",


        "text":
        {
            "body": message
        }

    }


    requests.post(
        url,
        headers=headers,
        json=payload
    )    