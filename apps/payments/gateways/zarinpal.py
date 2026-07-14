"""Zarinpal gateway (Iran, under Shaparak). API v4.

Amounts are sent in **Rial** (``currency: IRR``). Kept alongside Zibal so the
merchant can switch providers with an env var; see gateways/__init__.py.
"""
import requests
from django.utils import timezone

from .base import CallbackResult, InitResponse, PaymentError, PaymentGateway, VerifyResponse

PROD_BASE = "https://payment.zarinpal.com/pg/v4"
SANDBOX_BASE = "https://sandbox.zarinpal.com/pg/v4"
PROD_STARTPAY = "https://payment.zarinpal.com/pg/StartPay"
SANDBOX_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay"
TIMEOUT = 15


class ZarinpalGateway(PaymentGateway):
    name = "zarinpal"

    def __init__(self, merchant_id, sandbox=True):
        self.merchant_id = merchant_id
        self.base = SANDBOX_BASE if sandbox else PROD_BASE
        self.startpay = SANDBOX_STARTPAY if sandbox else PROD_STARTPAY

    def request(self, order, callback_url):
        resp = requests.post(
            f"{self.base}/payment/request.json",
            json={
                "merchant_id": self.merchant_id,
                "amount": order.amount_rial,
                "currency": "IRR",
                "description": f"سفارش #{order.code}",
                "callback_url": callback_url,
                "metadata": {"order": order.code, "mobile": order.phone, "email": order.email},
            },
            timeout=TIMEOUT,
        )
        payload = resp.json()
        data = payload.get("data") or {}
        authority = data.get("authority", "")
        if not authority:
            errors = payload.get("errors") or {}
            raise PaymentError(f"خطای زرین‌پال در ایجاد تراکنش: {errors}")
        return InitResponse(
            authority=authority,
            redirect_url=f"{self.startpay}/{authority}",
            raw=payload,
        )

    def parse_callback(self, params):
        """Zarinpal returns ?Authority=..&Status=OK|NOK"""
        return CallbackResult(
            authority=params.get("Authority") or params.get("authority", ""),
            success=(params.get("Status") or params.get("status", "")) == "OK",
            raw=dict(params.items()),
        )

    def verify(self, authority, amount_rial):
        resp = requests.post(
            f"{self.base}/payment/verify.json",
            json={"merchant_id": self.merchant_id, "amount": amount_rial, "authority": authority},
            timeout=TIMEOUT,
        )
        payload = resp.json()
        data = payload.get("data") or {}
        code = data.get("code")
        # 100 = verified now, 101 = already verified (idempotent success)
        success = code in (100, 101)
        return VerifyResponse(
            success=success,
            paid=success,
            verified=success,
            ref_id=str(data.get("ref_id", "")),
            card_number=str(data.get("card_pan") or ""),
            card_hash=str(data.get("card_hash") or ""),
            amount_rial=amount_rial if success else None,
            paid_at=timezone.now() if success else None,
            verified_at=timezone.now() if success else None,
            code=str(code),
            message=("پرداخت تأیید شد" if success else "تأیید پرداخت ناموفق بود"),
            raw=payload,
        )
