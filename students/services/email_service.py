import requests
from django.conf import settings
from .branding import get_sender_name
from students.models import GlobalCommunicationSetting


def send_brevo_email(
    to_email,
    to_name,
    subject,
    html_content,
    school=None  # kept for compatibility, but NOT used for config
):
    # ✅ GLOBAL CONFIG (ONE FOR ALL SCHOOLS)
    comm = GlobalCommunicationSetting.objects.filter(is_active=True).first()

    if not comm:
        return False, "Global Brevo configuration not found"

    if not comm.brevo_api_key:
        return False, "Brevo API key missing in global settings"

    if not comm.smtp_sender_email:
        return False, "Sender email missing in global settings"

    url = "https://api.brevo.com/v3/smtp/email"

    payload = {
        "sender": {
            "name": comm.smtp_sender_name or get_sender_name(school),
            "email": comm.smtp_sender_email
        },
        "to": [
            {
                "email": to_email,
                "name": to_name
            }
        ],
        "subject": subject,
        "htmlContent": html_content
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": comm.brevo_api_key
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code in [200, 201]:
            return True, response.json()

        return False, response.text

    except Exception as e:
        return False, str(e)