from celery import shared_task
from students.models import Announcement
from .announcement_service import get_announcement_recipients
from .email_service import send_brevo_email
from .whatsapp_service import send_whatsapp_message




def process_announcement(announcement):

    students = get_announcement_recipients(announcement)

    for student in students:

        school_name = announcement.school.name

        message = f"""
{school_name}
via TECHCENTER School Portal

{announcement.message}

— School Management
"""

        subject = f"{school_name} Announcement"

        html_content = f"""
        <h2>{school_name}</h2>
        <p>via TECHCENTER School Portal</p>
        <hr>
        <p>{announcement.message}</p>
        """

        # EMAIL
        if announcement.send_email and student.parent_email:

            send_brevo_email(
                student.parent_email,
                student.parent_name or "Parent",
                subject,
                html_content,
                announcement.school
            )

        # WHATSAPP
        if announcement.send_whatsapp and student.parent_phone:

            send_whatsapp_message(
                student.parent_phone,
                message
            )    