"""Zibal gateway tests. Zibal's HTTP calls are stubbed; no network here."""
from datetime import timedelta
from unittest.mock import patch

import pytest
import requests
from django.utils import timezone

from apps.orders.models import Order
from apps.payments.gateways import PaymentError
from apps.payments.gateways.zibal import ZibalGateway
from apps.payments.models import Payment
from apps.payments.services import reconcile, reconcile_stale

pytestmark = pytest.mark.django_db

MERCHANT = "653a8f1b2c3d4e5f60718293"
TRACK_ID = 15966442233311

# 437,400 Toman == 4,374,000 Rial (the pending_order fixture)
ORDER_RIAL = 4374000

PAID_PAYLOAD = {
    "result": 100,
    "message": "success",
    "status": 1,
    "amount": ORDER_RIAL,
    "refNumber": 12312,
    "cardNumber": "62741****44",
    "paidAt": "2026-07-14T14:18:21.742000",
    "verifiedAt": "2026-07-14T14:18:25.742000",
    "orderId": "10001",
}


@pytest.fixture
def zibal(settings):
    settings.ZIBAL_MERCHANT = MERCHANT
    return ZibalGateway(merchant=MERCHANT)


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def stub(payload):
    return patch("apps.payments.gateways.zibal.requests.post",
                 return_value=FakeResponse(payload))


# --- 1. درخواست پرداخت ---

def test_request_returns_start_url(zibal, pending_order):
    with stub({"result": 100, "trackId": TRACK_ID, "message": "success"}) as post:
        init = zibal.request(pending_order, "https://komaj.ir/payment/verify/")

    assert init.authority == str(TRACK_ID)
    assert init.redirect_url == f"https://gateway.zibal.ir/start/{TRACK_ID}"

    body = post.call_args.kwargs["json"]
    assert body["merchant"] == MERCHANT
    assert body["amount"] == ORDER_RIAL      # Rial, not Toman
    assert body["callbackUrl"] == "https://komaj.ir/payment/verify/"
    assert body["orderId"] == pending_order.code
    assert body["mobile"] == pending_order.phone


def test_request_raises_with_persian_message_on_error_code(zibal, pending_order):
    # 105 = amount must be > 1,000 Rial
    with stub({"result": 105, "message": "invalid amount"}):
        with pytest.raises(PaymentError, match="۱٬۰۰۰ ریال"):
            zibal.request(pending_order, "https://komaj.ir/cb/")


def test_request_raises_when_zibal_unreachable(zibal, pending_order):
    with patch("apps.payments.gateways.zibal.requests.post",
               side_effect=requests.ConnectionError("boom")):
        with pytest.raises(PaymentError, match="عدم دسترسی"):
            zibal.request(pending_order, "https://komaj.ir/cb/")


# --- 2. بازگشت از درگاه ---

def test_parse_callback():
    gw = ZibalGateway(merchant=MERCHANT)
    ok = gw.parse_callback({"success": "1", "trackId": str(TRACK_ID), "status": "2"})
    assert ok.authority == str(TRACK_ID)
    assert ok.success is True

    cancelled = gw.parse_callback({"success": "0", "trackId": str(TRACK_ID), "status": "3"})
    assert cancelled.success is False


# --- 3. تأیید پرداخت ---

def test_verify_success_captures_transaction_details(zibal):
    with stub(PAID_PAYLOAD):
        details = zibal.verify(str(TRACK_ID), ORDER_RIAL)

    assert details.success and details.paid and details.verified
    assert details.ref_id == "12312"
    assert details.card_number == "62741****44"
    assert details.paid_at is not None
    assert details.verified_at is not None
    assert details.status == 1
    assert details.status_label == "پرداخت شده — تأییدشده"


def test_verify_treats_already_verified_as_success(zibal):
    """result 201 means a duplicate verify — the money is ours, not an error."""
    with stub({**PAID_PAYLOAD, "result": 201}):
        details = zibal.verify(str(TRACK_ID), ORDER_RIAL)
    assert details.success is True


def test_verify_fails_on_unpaid_order(zibal):
    # 202 = سفارش پرداخت نشده یا ناموفق بوده است
    with stub({"result": 202, "status": 3, "message": "not paid"}):
        details = zibal.verify(str(TRACK_ID), ORDER_RIAL)
    assert details.success is False
    assert details.paid is False
    assert details.status_label == "لغو شده توسط کاربر"


def test_verify_rejects_amount_mismatch(zibal):
    """A paid-but-wrong amount must never settle the order."""
    with stub({**PAID_PAYLOAD, "amount": 1000}):
        details = zibal.verify(str(TRACK_ID), ORDER_RIAL)
    assert details.success is False
    assert "مبلغ" in details.message


# --- 4. استعلام پرداخت ---

def test_inquiry_reports_paid_but_unverified(zibal):
    with stub({**PAID_PAYLOAD, "status": 2, "verifiedAt": None}):
        details = zibal.inquiry(str(TRACK_ID), ORDER_RIAL)
    assert details.paid is True
    assert details.verified is False


def test_inquiry_raises_on_bad_track_id(zibal):
    with stub({"result": 203, "message": "invalid trackId"}):
        with pytest.raises(PaymentError, match="استعلام"):
            zibal.inquiry(str(TRACK_ID))


# --- reconciliation: the callback never arrived ---

def _age(payment, minutes):
    """Backdate created_at; auto_now_add ignores direct assignment."""
    Payment.objects.filter(pk=payment.pk).update(
        created_at=timezone.now() - timedelta(minutes=minutes)
    )
    payment.refresh_from_db()


def _pending_zibal_payment(order):
    return Payment.objects.create(
        order=order, gateway="zibal", amount=order.total, authority=str(TRACK_ID)
    )


def test_reconcile_settles_a_payment_whose_callback_was_lost(zibal, pending_order, variant):
    """Customer paid, we never got the callback. Inquiry says status 2 (paid,
    unverified) -> we verify and settle."""
    payment = _pending_zibal_payment(pending_order)

    inquiry_payload = {**PAID_PAYLOAD, "status": 2, "verifiedAt": None}
    with stub(inquiry_payload) as post:
        post.side_effect = [FakeResponse(inquiry_payload), FakeResponse(PAID_PAYLOAD)]
        summary = reconcile(payment)

    pending_order.refresh_from_db()
    variant.refresh_from_db()
    payment.refresh_from_db()

    assert pending_order.status == Order.PAID
    assert payment.status == Payment.PAID
    assert payment.ref_id == "12312"
    assert variant.stock_qty == 38  # stock decremented exactly once
    assert "تسویه" in summary


def test_reconcile_settles_when_provider_already_verified(zibal, pending_order, variant):
    """Verify succeeded at Zibal but our server died before saving. Inquiry says
    status 1 — settle locally, don't re-verify."""
    payment = _pending_zibal_payment(pending_order)

    with stub(PAID_PAYLOAD):  # status 1 = paid & verified
        summary = reconcile(payment)

    pending_order.refresh_from_db()
    variant.refresh_from_db()
    assert pending_order.status == Order.PAID
    assert Payment.objects.get(pk=payment.pk).status == Payment.PAID
    assert variant.stock_qty == 38
    assert "تسویه" in summary


def test_reconcile_leaves_unpaid_payment_pending(zibal, pending_order):
    """status -1 = still awaiting payment; the customer may yet pay."""
    payment = _pending_zibal_payment(pending_order)

    with stub({"result": 100, "status": -1, "amount": ORDER_RIAL, "message": "success"}):
        summary = reconcile(payment)

    payment.refresh_from_db()
    pending_order.refresh_from_db()
    assert payment.status == Payment.PENDING
    assert pending_order.status == Order.PENDING
    assert "هنوز پرداخت نشده" in summary


def test_reconcile_marks_cancelled_payment_failed(zibal, pending_order):
    payment = _pending_zibal_payment(pending_order)

    with stub({"result": 100, "status": 3, "amount": ORDER_RIAL, "message": "success"}):
        summary = reconcile(payment)

    payment.refresh_from_db()
    assert payment.status == Payment.FAILED
    assert "لغو شده" in summary


def test_reconcile_refuses_to_settle_on_amount_mismatch(zibal, pending_order):
    payment = _pending_zibal_payment(pending_order)

    with stub({**PAID_PAYLOAD, "status": 2, "amount": 1000}):
        summary = reconcile(payment)

    payment.refresh_from_db()
    pending_order.refresh_from_db()
    assert pending_order.status == Order.PENDING   # NOT settled
    assert payment.status != Payment.PAID
    assert "مغایرت مبلغ" in summary


def test_reconcile_is_idempotent_on_settled_payment(zibal, pending_order, variant):
    payment = _pending_zibal_payment(pending_order)
    with stub(PAID_PAYLOAD):
        reconcile(payment)
        payment.refresh_from_db()
        reconcile(payment)  # run it twice, as a cron would

    variant.refresh_from_db()
    assert variant.stock_qty == 38  # still decremented exactly once


# --- the periodic sweep (scheduler / reconcile_payments) ---

def test_sweep_ignores_payments_too_young_to_have_lost_a_callback(zibal, pending_order):
    """The customer may still be on the bank's page — don't go behind their back."""
    _pending_zibal_payment(pending_order)  # created just now

    with stub(PAID_PAYLOAD) as post:
        settled, unchanged, errored = reconcile_stale()

    assert (settled, unchanged, errored) == (0, 0, 0)
    assert not post.called  # provider never contacted
    pending_order.refresh_from_db()
    assert pending_order.status == Order.PENDING


def test_sweep_settles_an_aged_lost_callback(zibal, pending_order, variant):
    payment = _pending_zibal_payment(pending_order)
    _age(payment, minutes=30)

    with stub(PAID_PAYLOAD):
        settled, unchanged, errored = reconcile_stale()

    assert (settled, unchanged, errored) == (1, 0, 0)
    pending_order.refresh_from_db()
    variant.refresh_from_db()
    assert pending_order.status == Order.PAID
    assert variant.stock_qty == 38


def test_sweep_skips_payments_past_the_max_age(zibal, pending_order):
    payment = _pending_zibal_payment(pending_order)
    _age(payment, minutes=60 * 96)  # 96h > 72h default

    with stub(PAID_PAYLOAD) as post:
        settled, unchanged, errored = reconcile_stale()

    assert (settled, unchanged, errored) == (0, 0, 0)
    assert not post.called


def test_sweep_survives_an_unreachable_provider(zibal, pending_order):
    """One dead payment must not abort the whole sweep."""
    payment = _pending_zibal_payment(pending_order)
    _age(payment, minutes=30)

    with patch("apps.payments.gateways.zibal.requests.post",
               side_effect=requests.ConnectionError("boom")):
        settled, unchanged, errored = reconcile_stale()

    assert (settled, unchanged, errored) == (0, 0, 1)
    payment.refresh_from_db()
    assert payment.status == Payment.PENDING  # left for the next sweep


def test_scheduler_does_not_run_in_management_commands_or_tests():
    """A background thread hitting Zibal must never start from migrate/collectstatic/pytest."""
    from apps.payments import scheduler

    assert scheduler.should_run() is False  # we are pytest

    with patch.object(scheduler.sys, "modules", {}):  # pretend we're not under pytest
        with patch.object(scheduler.sys, "argv", ["manage.py", "migrate"]):
            assert scheduler.should_run() is False
        with patch.object(scheduler.sys, "argv", ["manage.py", "collectstatic"]):
            assert scheduler.should_run() is False
        with patch.object(scheduler.sys, "argv", ["/usr/local/bin/gunicorn", "config.wsgi"]):
            assert scheduler.should_run() is True
