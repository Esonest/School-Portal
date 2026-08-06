from students.services.whatsapp_service import send_whatsapp_message
from students.services.email_service import send_brevo_email



def send_student_login_details(application):


    student = application.student_name


    portal_link = (
        "https://techcenter-p2au.onrender.com/login/"
    )


    message = f"""

Dear {application.parent_name},


Congratulations!


Your child's admission payment has been confirmed.


Student Name:

{student}


School:

{application.school.name}



Student Portal Login Details:


Username:

{application.student_username}


Password:

{application.student_password}



Portal Link:

{portal_link}






Thank you.

{application.school.name}

"""


    # ==========================
    # WHATSAPP
    # ==========================

    try:

        send_whatsapp_message(
            application.parent_phone,
            message=message
        )

        print(
            "Student WhatsApp sent"
        )


    except Exception as e:

        print(
            "WhatsApp error:",
            e
        )



    # ==========================
    # EMAIL
    # ==========================


    html = message.replace(
        "\n",
        "<br>"
    )


    try:

        send_brevo_email(

            to_email=application.parent_email,

            to_name=application.parent_name,

            subject="Student Portal Login Details",

            html_content=html,

            school=application.school

        )


        print(
            "Student email sent"
        )


    except Exception as e:

        print(
            "Email error:",
            e
        )