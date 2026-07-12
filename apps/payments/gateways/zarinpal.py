"""Zarinpal gateway (Iran, under Shaparak). API v4.

Amounts are sent in **Rial** (``currency: IRR``). Selected automatically when
``ZARINPAL_MERCHANT_ID`` is configured; otherwise the app falls back to the mock
gateway so the flow is exercisable without credentials.
"""
import requests

from .base import InitResponse, PaymentGateway, VerifyResponse

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
            ref_id=str(data.get("ref_id", "")),
            code=str(code),
            message=("پرداخت تأیید شد" if success else "تأیید پرداخت ناموفق بود"),
            raw=payload,
        )


class PaymentError(Exception):
    pass
