"""
PayHere integration helper.

PayHere's standard checkout flow needs an MD5 "hash" generated from your
merchant secret so the checkout page can be trusted client-side. This
module builds that payload. The actual redirect to PayHere is done by
the Flutter app (or a WebView) using the fields returned here, posted to:

    sandbox:    https://sandbox.payhere.lk/pay/checkout
    production: https://www.payhere.lk/pay/checkout

All secrets are read from .env - never hard-code PAYHERE_MERCHANT_SECRET.
"""
import hashlib
import uuid

from app.config import settings
from app import models


PLAN_PRICES = {
    models.PlanType.pro_500: lambda: settings.PRO_PLAN_PRICE_LKR,
    models.PlanType.unlimited: lambda: settings.UNLIMITED_PLAN_PRICE_LKR,
}


def _format_amount(amount: float) -> str:
    return f"{amount:.2f}"


def build_payhere_hash(order_id: str, amount: str, currency: str = "LKR") -> str:
    merchant_id = settings.PAYHERE_MERCHANT_ID
    merchant_secret_hash = hashlib.md5(
        settings.PAYHERE_MERCHANT_SECRET.encode("utf-8")
    ).hexdigest().upper()

    raw = (
        f"{merchant_id}{order_id}{amount}{currency}{merchant_secret_hash}"
    )
    return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()


def create_payhere_order(user: models.User, plan: models.PlanType) -> dict:
    if plan not in PLAN_PRICES:
        raise ValueError("Free plan does not require payment")

    amount_value = PLAN_PRICES[plan]()
    amount_str = _format_amount(amount_value)
    order_id = f"NWA-{user.id}-{uuid.uuid4().hex[:8].upper()}"
    generated_hash = build_payhere_hash(order_id, amount_str)

    checkout_action_url = (
        "https://sandbox.payhere.lk/pay/checkout"
        if settings.PAYHERE_MODE == "sandbox"
        else "https://www.payhere.lk/pay/checkout"
    )

    return {
        "merchant_id": settings.PAYHERE_MERCHANT_ID,
        "order_id": order_id,
        "amount": amount_str,
        "currency": "LKR",
        "hash": generated_hash,
        "return_url": settings.PAYHERE_RETURN_URL,
        "cancel_url": settings.PAYHERE_CANCEL_URL,
        "notify_url": settings.PAYHERE_NOTIFY_URL,
        "checkout_action_url": checkout_action_url,
    }


def verify_payhere_notify_signature(
    merchant_id: str,
    order_id: str,
    amount: str,
    currency: str,
    status_code: str,
    md5sig: str,
) -> bool:
    """Verifies the md5sig PayHere sends to your notify_url webhook."""
    merchant_secret_hash = hashlib.md5(
        settings.PAYHERE_MERCHANT_SECRET.encode("utf-8")
    ).hexdigest().upper()
    local_sig = hashlib.md5(
        f"{merchant_id}{order_id}{amount}{currency}{status_code}{merchant_secret_hash}".encode("utf-8")
    ).hexdigest().upper()
    return local_sig == md5sig
