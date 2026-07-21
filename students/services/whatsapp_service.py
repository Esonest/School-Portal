import re
import requests

from students.models import GlobalCommunicationSetting


GRAPH_API_VERSION = "v22.0"


def format_phone(phone):
    """
    Converts Nigerian numbers into WhatsApp format.

    08031234567      -> 2348031234567
    +2348031234567   -> 2348031234567
    2348031234567    -> 2348031234567
    """

    phone = re.sub(r"\D", "", str(phone))

    if phone.startswith("234"):
        return phone

    if phone.startswith("0"):
        return "234" + phone[1:]

    return phone


def _get_config():

    comm = GlobalCommunicationSetting.objects.filter(
        is_active=True
    ).first()

    if not comm:
        return None, "Global WhatsApp configuration not found"

    if not comm.whatsapp_token:
        return None, "WhatsApp token missing"

    if not comm.whatsapp_phone_id:
        return None, "WhatsApp Phone Number ID missing"

    return comm, None


def send_whatsapp_message(
    phone,
    *,
    message=None,
    template_name=None,
    template_parameters=None,
    language="en",
):
    """
    Sends either

    1. Template Message (conversation initiation)

    OR

    2. Plain Text Message (24-hour window)

    Examples

    send_whatsapp_message(
        phone="08031234567",
        template_name="techcenter_notification",
        template_parameters=[
            "TECHCENTER International School",
            "Announcement",
            "School resumes Monday."
        ]
    )

    send_whatsapp_message(
        phone="08031234567",
        message="Thank you for contacting us."
    )
    """

    comm, error = _get_config()

    if error:
        return False, error

    phone = format_phone(phone)

    url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_API_VERSION}/"
        f"{comm.whatsapp_phone_id}/messages"
    )

    headers = {
        "Authorization": f"Bearer {comm.whatsapp_token}",
        "Content-Type": "application/json",
    }

    # -----------------------------
    # TEMPLATE MESSAGE
    # -----------------------------
    if template_name:

        parameters = []

        for value in template_parameters or []:

            parameters.append(
                {
                    "type": "text",
                    "text": str(value),
                }
            )

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": parameters
                    }
                ]
            }
        }

    # -----------------------------
    # NORMAL TEXT MESSAGE
    # -----------------------------
    else:

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {
                "body": message
            }
        }

    try:

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=15
        )

        print("=" * 60)
        print("WHATSAPP REQUEST")
        print(payload)
        print("=" * 60)

        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)

        if response.ok:
            return True, response.json()

        return False, response.text

    except Exception as e:
        return False, str(e)