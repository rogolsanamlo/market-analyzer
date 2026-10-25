"""JSON API used by the dashboard (all routes start with /api/)."""
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from apps.data_sources.services import fetch_all
from apps.market_data import queries
from apps.market_data.models import Asset

from . import services


def _days_param(request, default=30):
    try:
        days = int(request.GET.get("days", default))
    except ValueError:
        days = default
    return max(1, min(days, 365))


@require_GET
def assets(request):
    """Every asset with a 30-day summary."""
    items = []
    for asset in Asset.objects.all():
        points, is_demo = queries.get_history(asset, days=30)
        items.append({
            "symbol": asset.symbol,
            "name": asset.name,
            "category": asset.category,
            "unit": asset.unit,
            "summary": services.summarize([p for _, p in points]),
            "is_demo": is_demo,
        })
    return JsonResponse(items, safe=False)


@require_GET
def history(request, symbol):
    """Price history plus 7- and 21-point moving averages for one asset."""
    try:
        asset = Asset.objects.get(symbol=symbol.upper())
    except Asset.DoesNotExist:
        return JsonResponse({"error": "unknown symbol"}, status=404)

    points, is_demo = queries.get_history(asset, days=_days_param(request))
    prices = [p for _, p in points]
    return JsonResponse({
        "symbol": asset.symbol,
        "name": asset.name,
        "unit": asset.unit,
        "is_demo": is_demo,
        "labels": [t.isoformat() for t, _ in points],
        "prices": prices,
        "ma7": services.moving_average(prices, 7),
        "ma21": services.moving_average(prices, 21),
        "summary": services.summarize(prices),
    })


@require_POST
def refresh(request):
    """Download fresh prices from the sources (takes a few seconds)."""
    results = fetch_all(timeout=settings.REQUEST_TIMEOUT, backfill_days=settings.BACKFILL_DAYS)
    return JsonResponse({"results": results, "updated": sum(1 for r in results if r["ok"])})
