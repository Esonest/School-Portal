from celery import shared_task

from students.models import Announcement, MessageLog

from .announcement_service import get_announcement_recipients
from .email_service import send_brevo_email
from .whatsapp_service import send_whatsapp_message


def process_announcement(announcement):
    print("🚀 PROCESS ANNOUNCEMENT STARTED")
    print("PROCESSING:", announcement.id)
    print("CHANNELS:", announcement.send_channels)

    students = get_announcement_recipients(announcement)

    for student in students:

        print("=" * 60)
        print("STUDENT:", student)
        print("EMAIL:", student.parent_email)
        print("PHONE:", student.parent_phone)
        print("=" * 60)

        school_name = announcement.school.name

        subject = f"{school_name} Announcement"

        html_content = f"""
        <h2>{school_name}</h2>
        <p>via TECHCENTER School Portal</p>
        <hr>
        <p>{announcement.message}</p>
        """

        # =====================================================
        # EMAIL
        # =====================================================

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
                announcement.school,
            )

            print("EMAIL:", success, response)

            MessageLog.objects.create(
                school=announcement.school,
                announcement=announcement,
                recipient=student.parent_email,
                channel="email",
                status="sent" if success else "failed",
                response=str(response),
            )

        # =====================================================
        # WHATSAPP
        # =====================================================

        if (
            "whatsapp" in announcement.send_channels
            and student.parent_phone
        ):

            success, response = send_whatsapp_message(
                phone=student.parent_phone,
                template_name="school_announcement",
                template_parameters=[
                    school_name,
                    "Announcement",
                    announcement.message,
                ],
            )

            print("WHATSAPP:", success, response)

            MessageLog.objects.create(
                school=announcement.school,
                announcement=announcement,
                recipient=student.parent_phone,
                channel="whatsapp",
                status="sent" if success else "failed",
                response=str(response),
            )