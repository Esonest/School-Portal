from students.services.email_service import send_brevo_email


def send_demo_notification(
    school_name,
    contact_person,
    email,
    phone,
    population,
    message
):

    html = f"""
    <h2>New Demo Booking</h2>

    <p><strong>School:</strong> {school_name}</p>
    <p><strong>Contact:</strong> {contact_person}</p>
    <p><strong>Email:</strong> {email}</p>
    <p><strong>Phone:</strong> {phone}</p>
    <p><strong>Population:</strong> {population}</p>

    <hr>

    <p>{message}</p>
    """

    return send_brevo_email(
        to_email="techcenter652@gmail.com",
        to_name="TECHCENTER",
        subject="New Demo Booking",
        html_content=html
    )