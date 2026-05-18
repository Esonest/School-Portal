import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings
from .branding import get_sender_name


def send_brevo_email(
    to_email,
    to_name,
    subject,
    html_content,
    school
):
    configuration = sib_api_v3_sdk.Configuration()

    configuration.api_key['api-key'] = settings.BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    sender = {
        "name": get_sender_name(school),
        "email": "techcenter652@gmail.com"
    }

    to = [{
        "email": to_email,
        "name": to_name
    }]

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        sender=sender,
        subject=subject,
        html_content=html_content
    )

    try:
        response = api_instance.send_transac_email(
            send_smtp_email
        )

        return True, str(response)

    except ApiException as e:
        return False, str(e)