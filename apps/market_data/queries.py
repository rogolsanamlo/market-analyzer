"""Small helper functions for reading and saving prices."""
from datetime import timedelta

from django.utils import timezone

from .models import DEMO_SOURCE, MIN_REAL_POINTS, PriceRecord


def now_seconds():
    return timezone.now().replace(microsecond=0)


def add_prices(asset, points, source):
    """Save a list of (datetime, price). A duplicate (same asset+time) is ignored."""
    PriceRecord.objects.bulk_create(
        [PriceRecord(asset=asset, price=float(p), recorded_at=t, source=source) for t, p in points],
        ignore_conflicts=True,
    )


def add_price(asset, price, source, recorded_at=None):
    add_prices(asset, [(recorded_at or now_seconds(), price)], source)


def count_prices(asset, include_demo=True):
    qs = asset.prices.all()
    if not include_demo:
        qs = qs.exclude(source=DEMO_SOURCE)
    return qs.count()


def get_history(asset, days=30):
    """Return (points, is_demo). points = [(datetime, price), ...] oldest first.

    Real data is used once there are enough real points; until then the demo
    data is shown (and is_demo=True so the page can warn the user).
    """
    since = timezone.now() - timedelta(days=days)
    rows = list(
        asset.prices.filter(recorded_at__gte=since).values_list("recorded_at", "price", "source")
    )
    real = [r for r in rows if r[2] != DEMO_SOURCE]
    chosen = real if len(real) >= MIN_REAL_POINTS else rows
    is_demo = bool(chosen) and all(r[2] == DEMO_SOURCE for r in chosen)
    return [(r[0], r[1]) for r in chosen], is_demo
