from celery import shared_task
from students.models import Announcement, MessageLog
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
        if (
            "email" in announcement.send_channels
            and student.parent_email
            and announcement.school.email_enabled
        ):

            success, response = send_brevo_email(
                student.parent_email,
                student.parent_name or "Parent",
                subject,
                html_content,
                announcement.school
            )

            print(
                "EMAIL:",
                success,
                response
            )
            MessageLog.objects.create(
                school=announcement.school,
                announcement=announcement,
                recipient=student.parent_email,
                channel="email",
                status="sent" if success else "failed",
                response=str(response)
            )

        # WHATSAPP
        if (
            "whatsapp" in announcement.send_channels
            and student.parent_phone
            and announcement.school.whatsapp_enabled
        ):

            success, response = send_whatsapp_message(
                student.parent_phone,
                message,
                announcement.school
            )

            print(
                "WHATSAPP:",
                success,
                response
            )
            MessageLog.objects.create(
                school=announcement.school,
                announcement=announcement,
                recipient=student.parent_email,
                channel="email",
                status="sent" if success else "failed",
                response=str(response)
            )    