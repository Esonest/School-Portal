import requests
from django.conf import settings




def format_phone(phone):

    phone = str(phone).strip()

    if phone.startswith("0"):
        phone = "234" + phone[1:]

    if phone.startswith("+"):
        phone = phone[1:]

    return phone


def send_whatsapp_message(
    phone,
    message,
    school
):

    comm = school.schoolcommunicationsetting

    phone = format_phone(phone)

    url = (
        f"https://graph.facebook.com/v22.0/"
        f"{comm.whatsapp_phone_id}/messages"
    )

    headers = {
        "Authorization":
            f"Bearer {comm.whatsapp_token}",

        "Content-Type":
            "application/json",
    }

    payload = {
        "messaging_product":
            "whatsapp",

        "to":
            phone,

        "type":
            "text",

        "text": {
            "body": message
        }
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers
    )

    print(
        "WHATSAPP STATUS:",
        response.status_code
    )

    print(
        "WHATSAPP RESPONSE:",
        response.text
    )

    if response.status_code == 200:
        return True, response.json()

    return False, response.text