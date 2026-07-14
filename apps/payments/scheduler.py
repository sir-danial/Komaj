"""In-process scheduler for payment reconciliation.

Phase 1 has no Celery/Redis (MVP: ~10 orders/week), so the periodic "did anyone
pay without us noticing?" sweep runs on a daemon thread inside the web container.
Enable it with PAYMENTS_RECONCILE_INTERVAL_MINUTES; 0/unset = off.

Safe to run more than once concurrently (two workers, an overlapping manual run):
``reconcile`` takes a row lock and settles each order exactly once.

If this ever outgrows a thread — more workers, more volume — move it to a real
Darkube CronJob running ``python manage.py reconcile_payments`` and set the
interval back to 0. Nothing else has to change.
"""
import logging
import os
import sys
import threading
import time
from pathlib import Path

from django.db import connections

logger = logging.getLogger(__name__)

# Let the app finish booting (and let an in-flight callback land) before sweeping.
FIRST_RUN_DELAY_SECONDS = 120

_started = threading.Lock()
_running = False


def should_run():
    """Only sweep from a process that is actually serving the site.

    Management commands (migrate, collectstatic, seed_catalog, shell) and the test
    suite must not spawn a background thread that hits the payment provider.
    """
    if "pytest" in sys.modules:
        return False

    argv = sys.argv or []
    program = Path(argv[0]).name if argv else ""

    if program.startswith("gunicorn"):
        return True

    if "runserver" in argv:
        # Under the autoreloader, ready() fires in both the parent watcher and the
        # child; only the child (RUN_MAIN) actually serves requests.
        return os.environ.get("RUN_MAIN") == "true"

    return False


def start(interval_minutes):
    global _running
    with _started:
        if _running:
            return
        _running = True

    thread = threading.Thread(
        target=_loop, args=(interval_minutes,),
        name="reconcile-payments", daemon=True,
    )
    thread.start()
    logger.info("payment reconciliation scheduler started (every %s min)", interval_minutes)


def _loop(interval_minutes):
    from .services import reconcile_stale

    time.sleep(FIRST_RUN_DELAY_SECONDS)
    interval_seconds = interval_minutes * 60

    while True:
        try:
            settled, unchanged, errored = reconcile_stale()
            if settled or errored:
                logger.info(
                    "reconcile sweep: settled=%s unchanged=%s errored=%s",
                    settled, unchanged, errored,
                )
        except Exception:
            # A failed sweep must never kill the thread — the next one retries.
            logger.exception("payment reconciliation sweep failed")
        finally:
            # Long-lived thread: don't hold a DB connection open between sweeps.
            connections.close_all()

        time.sleep(interval_seconds)
