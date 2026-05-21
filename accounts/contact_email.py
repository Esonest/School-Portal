from students.services.email_service import send_brevo_email


def send_contact_email(
    name,
    email,
    subject,
    message_text
):
    # Admin email
    admin_html = f"""
    <h2>New Contact Message</h2>

    <p><strong>Name:</strong> {name}</p>
    <p><strong>Email:</strong> {email}</p>
    <p><strong>Subject:</strong> {subject}</p>

    <hr>

    <p>{message_text}</p>
    """

    admin_success, admin_response = send_brevo_email(
        to_email="techcenter652@gmail.com",
        to_name="TECHCENTER Admin",
        subject=f"[TECHCENTER Contact] {subject}",
        html_content=admin_html,
        school=None
    )

    # Auto reply
    reply_html = f"""
    <h2>Thank You for Contacting TECHCENTER</h2>

    <p>Hi {name},</p>

    <p>
        We received your message and our team
        will get back to you shortly.
    </p>

    <br>

    <p>Regards,<br>TECHCENTER Team</p>
    """

    user_success, user_response = send_brevo_email(
        to_email=email,
        to_name=name,
        subject="Thank you for contacting TECHCENTER",
        html_content=reply_html,
        school=None
    )

    return (
        admin_success and user_success,
        {
            "admin": admin_response,
            "user": user_response
        }
    )