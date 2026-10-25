"""Demo data so the dashboard works offline (before any real fetch).

Prices are a made-up random walk - they are NOT real market data.
They are stored with source="demo" and hidden automatically once an asset
has enough real data points.
"""
import random
from datetime import datetime, timedelta, timezone

from apps.market_data import queries
from apps.market_data.models import DEMO_SOURCE, Asset

BASE_PRICES = {
    "BTC": 90_000, "ETH": 3_500, "USD": 268_000,
    "GOLD18": 26_500_000, "COIN": 260_000_000,
}
DAILY_VOLATILITY = {"crypto": 0.03, "currency": 0.008, "gold": 0.012}


def generate_demo_history(symbol, category, days=30):
    """A repeatable fake price curve: [(datetime, price), ...] oldest first."""
    rng = random.Random(symbol)  # same symbol -> same demo curve every time
    price = BASE_PRICES.get(symbol, 100.0)
    vol = DAILY_VOLATILITY.get(category, 0.01)
    today = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    points = []
    for i in range(days, -1, -1):
        price *= 1 + rng.gauss(0.001, vol)
        points.append((today - timedelta(days=i), round(price, 2)))
    return points


def seed_demo(days=30):
    """Add demo history for assets that have no prices yet. Returns the symbols seeded."""
    seeded = []
    for asset in Asset.objects.all():
        if queries.count_prices(asset) == 0:
            queries.add_prices(asset, generate_demo_history(asset.symbol, asset.category, days),
                               DEMO_SOURCE)
            seeded.append(asset.symbol)
    return seeded
