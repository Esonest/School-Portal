# utils.py
import requests
from django.conf import settings

HMS_API_KEY = settings.HMS_API_KEY
HMS_API_SECRET = settings.HMS_API_SECRET

def create_100ms_room(title):
    url = "https://api.100ms.live/v2/rooms"
    response = requests.post(
        url,
        auth=(HMS_API_KEY, HMS_API_SECRET),
        json={
            "name": title,
            "template_id": settings.HMS_TEMPLATE_ID
        }
    )
    return response.json()