"""Zibal IPG gateway (Iran, under Shaparak).

Docs: https://help.zibal.ir/ipg/

Flow: request -> start (redirect) -> callback -> verify. A payment that is paid
but never verified is *reversed back to the customer's card*, so verify is not
optional bookkeeping — skipping it loses the sale. When a callback never arrives
(closed tab, our server down), :meth:`inquiry` recovers the transaction.

Amounts are in **Rial**, like Zarinpal. Money in this project is stored in Toman;
``order.amount_rial`` does the conversion.

Zibal publishes a shared test merchant, ``zibal``, that exercises the real
endpoints without credentials — set ``ZIBAL_MERCHANT=zibal`` to try the flow
before a real merchant id exists.
"""
import logging

import requests
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .base import (
    CallbackResult,
    InitResponse,
    PaymentError,
    PaymentGateway,
    TransactionDetails,
)

logger = logging.getLogger(__name__)

BASE = "https://gateway.zibal.ir"
START_URL = f"{BASE}/start/{{track_id}}"
TIMEOUT = 15

TEST_MERCHANT = "zibal"

# --- Transaction status (جدول وضعیت‌ها) ---
STATUS_PAID_VERIFIED = 1     # پرداخت شده — تأییدشده
STATUS_PAID_UNVERIFIED = 2   # پرداخت شده — تأییدنشده (money taken, awaiting our verify)
STATUS_AWAITING_PAYMENT = -1

STATUS_LABELS = {
    -2: "خطای داخلی",
    -1: "در انتظار پرداخت",
    1: "پرداخت شده — تأییدشده",
    2: "پرداخت شده — تأییدنشده",
    3: "لغو شده توسط کاربر",
    4: "شماره کارت نامعتبر است",
    5: "موجودی حساب کافی نیست",
    6: "رمز واردشده اشتباه است",
    7: "تعداد درخواست‌ها بیش از حد مجاز است",
    8: "تعداد پرداخت اینترنتی روزانه بیش از حد مجاز است",
    9: "مبلغ پرداخت اینترنتی روزانه بیش از حد مجاز است",
    10: "صادرکننده‌ی کارت نامعتبر است",
    11: "خطای سوییچ",
    12: "کارت قابل دسترسی نیست",
    15: "تراکنش استرداد شده",
    16: "تراکنش در حال استرداد",
    18: "تراکنش ریورس شده",
    21: "پذیرنده نامعتبر است",
}

# The customer's money reached us in both of these; only the finalisation differs.
PAID_STATUSES = (STATUS_PAID_VERIFIED, STATUS_PAID_UNVERIFIED)

# --- Result codes (جدول کدهای نتیجه) ---
RESULT_OK = 100
RESULT_ALREADY_VERIFIED = 201  # verify called twice — idempotent success, not an error

REQUEST_RESULT_LABELS = {
    100: "با موفقیت تأیید شد",
    102: "merchant یافت نشد",
    103: "merchant غیرفعال است",
    104: "merchant نامعتبر است",
    105: "مبلغ باید بیشتر از ۱٬۰۰۰ ریال باشد",
    106: "callbackUrl نامعتبر است (باید با http یا https شروع شود)",
    107: "percentMode نامعتبر است",
    108: "یک یا چند ذی‌نفع در multiplexingInfos نامعتبر است",
    109: "یک یا چند ذی‌نفع در multiplexingInfos غیرفعال است",
    110: "id = self در multiplexingInfos وجود ندارد",
    111: "مبلغ با مجموع سهم‌های multiplexingInfos برابر نیست",
    112: "موجودی کیف پول کارمزد کافی نیست",
    113: "مبلغ تراکنش از سقف مجاز بیشتر است",
    114: "کد ملی ارسالی نامعتبر است",
    115: "IP سرور شما در پنل کاربری زیبال ثبت نشده است",
}

VERIFY_RESULT_LABELS = {
    100: "با موفقیت تأیید شد",
    102: "merchant یافت نشد",
    103: "merchant غیرفعال است",
    104: "merchant نامعتبر است",
    201: "قبلاً تأیید شده است",
    202: "سفارش پرداخت نشده یا ناموفق بوده است",
    203: "trackId نامعتبر است",
}


class ZibalGateway(PaymentGateway):
    name = "zibal"

    def __init__(self, merchant):
        self.merchant = merchant

    # --- 1. درخواست پرداخت ---
    def request(self, order, callback_url):
        payload = self._post("/v1/request", {
            "merchant": self.merchant,
            "amount": order.amount_rial,
            "callbackUrl": callback_url,
            "description": f"سفارش #{order.code}",
            "orderId": order.code,
            "mobile": order.phone,
        })
        result = payload.get("result")
        track_id = payload.get("trackId")
        if result != RESULT_OK or not track_id:
            raise PaymentError(
                f"خطای زیبال در ایجاد تراکنش: {self._label(REQUEST_RESULT_LABELS, result, payload)}"
            )
        return InitResponse(
            authority=str(track_id),
            redirect_url=START_URL.format(track_id=track_id),
            raw=payload,
        )

    # --- 3. بازگشت از درگاه (Callback) ---
    def parse_callback(self, params):
        """Zibal returns ?success=1|0&trackId=..&orderId=..&status=..

        ``success`` is only a hint — the money is not ours until verify succeeds.
        """
        return CallbackResult(
            authority=str(params.get("trackId", "")),
            success=str(params.get("success", "")) == "1",
            # only present in lazy mode, but free to keep when it is
            card_hash=str(params.get("hashedCardNumber", "")),
            raw=dict(params.items()),
        )

    # --- 3. تأیید پرداخت ---
    def verify(self, authority, amount_rial):
        payload = self._post("/v1/verify", {
            "merchant": self.merchant,
            "trackId": int(authority),
        })
        result = payload.get("result")
        # 201 ("already verified") is a success: a duplicate callback, not a failure.
        ok = result in (RESULT_OK, RESULT_ALREADY_VERIFIED)
        details = self._details(payload, VERIFY_RESULT_LABELS)
        details.verified = ok
        details.success = ok and self._amount_matches(details, amount_rial, authority)
        if not details.success:
            details.verified = False
        return details

    # --- 4. استعلام پرداخت ---
    def inquiry(self, authority, amount_rial=None):
        payload = self._post("/v1/inquiry", {
            "merchant": self.merchant,
            "trackId": int(authority),
        })
        details = self._details(payload, VERIFY_RESULT_LABELS)
        if payload.get("result") != RESULT_OK:
            raise PaymentError(f"خطای زیبال در استعلام تراکنش: {details.message}")
        details.verified = details.status == STATUS_PAID_VERIFIED
        # For an inquiry, "success" means: the customer really paid this order, for
        # the right amount. Whether it still needs a verify call is `verified`.
        details.success = details.paid and (
            amount_rial is None or self._amount_matches(details, amount_rial, authority)
        )
        return details

    # --- helpers ---
    def _post(self, path, body):
        try:
            resp = requests.post(f"{BASE}{path}", json=body, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            raise PaymentError(f"عدم دسترسی به درگاه زیبال: {exc}") from exc
        except ValueError as exc:  # non-JSON body
            raise PaymentError("پاسخ نامعتبر از درگاه زیبال دریافت شد.") from exc

    def _details(self, payload, labels):
        status = payload.get("status")
        result = payload.get("result")
        if status is None:
            status_label = ""
        else:
            status_label = STATUS_LABELS.get(status, f"وضعیت ناشناخته ({status})")
        return TransactionDetails(
            paid=status in PAID_STATUSES,
            ref_id=str(payload.get("refNumber") or ""),
            card_number=str(payload.get("cardNumber") or ""),
            amount_rial=payload.get("amount"),
            paid_at=self._parse_dt(payload.get("paidAt")),
            verified_at=self._parse_dt(payload.get("verifiedAt")),
            status=status,
            status_label=status_label,
            code=str(result or ""),
            message=self._label(labels, result, payload),
            raw=payload,
        )

    def _amount_matches(self, details, expected_rial, authority):
        """Refuse to settle an order whose amount doesn't match what was paid."""
        if details.amount_rial is None or int(details.amount_rial) == int(expected_rial):
            return True
        logger.error(
            "ZIBAL AMOUNT MISMATCH on trackId %s: paid %s Rial, order expects %s Rial",
            authority, details.amount_rial, expected_rial,
        )
        details.message = "مبلغ پرداخت‌شده با مبلغ سفارش مطابقت ندارد."
        return False

    @staticmethod
    def _label(labels, result, payload):
        return labels.get(result) or payload.get("message") or f"کد نتیجه: {result}"

    @staticmethod
    def _parse_dt(value):
        """Zibal sends naive ISO timestamps in Tehran local time."""
        if not value:
            return None
        dt = parse_datetime(value)
        if dt and timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt
