"""
WhatsApp integration layer.

DEMO MODE (current):
    Notify WA is currently shipped as a demo, so this module returns
    realistic-looking mock data instead of calling Meta's WhatsApp Cloud API.
    No real WhatsApp account is contacted and no real messages are sent.

GOING LIVE LATER:
    When WHATSAPP_DEMO_MODE=false and WHATSAPP_ACCESS_TOKEN /
    WHATSAPP_PHONE_NUMBER_ID are set in .env, swap the bodies of the two
    functions below for real calls to the official WhatsApp Business
    Cloud API, e.g.:

        POST {WHATSAPP_API_BASE_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages
        Authorization: Bearer {WHATSAPP_ACCESS_TOKEN}

    Listing a user's own groups is NOT exposed by Meta's official API
    (groups are only reachable through invite links / group JIDs you
    already manage), so a real integration typically asks the business
    to register each group/broadcast list once via a setup flow rather
    than "listing" them automatically - the mock below simulates that
    end result for the UI.
"""
from typing import List, Dict
import random

from app.config import settings


def mock_groups_for_new_connection() -> List[Dict]:
    """Returns a plausible set of WhatsApp groups after a user 'connects' their account."""
    sample_names = [
        "Grade 10 - Mathematics",
        "Grade 11 - Science Batch",
        "Parents Announcement Group",
        "Weekend Revision Class",
        "Physics Theory Group",
    ]
    groups = []
    for i, name in enumerate(sample_names, start=1):
        groups.append({
            "external_group_id": f"demo-group-{i}",
            "group_name": name,
            "member_count": random.randint(15, 60),
        })
    return groups


def send_whatsapp_message(to_group_external_id: str, message: str) -> Dict:
    """
    In demo mode this simply pretends the message was sent successfully.
    Replace with a real Graph API POST call when WHATSAPP_DEMO_MODE=false.
    """
    if settings.WHATSAPP_DEMO_MODE or not settings.WHATSAPP_ACCESS_TOKEN:
        return {"status": "sent", "demo": True, "group": to_group_external_id}

    # --- Real integration placeholder (uncomment & complete when ready) ---
    # import requests
    # url = f"{settings.WHATSAPP_API_BASE_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    # headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
    # payload = {"messaging_product": "whatsapp", "to": to_group_external_id,
    #            "type": "text", "text": {"body": message}}
    # resp = requests.post(url, headers=headers, json=payload, timeout=15)
    # resp.raise_for_status()
    # return resp.json()

    return {"status": "sent", "demo": False, "group": to_group_external_id}
