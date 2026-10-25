"""The list of assets the project tracks.

To track something new, add one dict here and run `python manage.py migrate`
(or any management command) - it is copied into the database automatically.
  - source "coingecko": source_id is the CoinGecko coin id (e.g. "bitcoin")
  - source "tgju":      source_id is the page slug in https://www.tgju.org/profile/<slug>
"""

ASSETS = [
    {"symbol": "BTC", "name": "بیت‌کوین", "category": "crypto", "unit": "USD",
     "source": "coingecko", "source_id": "bitcoin"},
    {"symbol": "ETH", "name": "اتریوم", "category": "crypto", "unit": "USD",
     "source": "coingecko", "source_id": "ethereum"},
    {"symbol": "USD", "name": "دلار آزاد", "category": "currency", "unit": "تومان",
     "source": "tgju", "source_id": "price_dollar_rl"},
    {"symbol": "GOLD18", "name": "طلای ۱۸ عیار (گرم)", "category": "gold", "unit": "تومان",
     "source": "tgju", "source_id": "geram18"},
    {"symbol": "COIN", "name": "سکه امامی", "category": "gold", "unit": "تومان",
     "source": "tgju", "source_id": "sekee"},
]


def sync_assets():
    """Make sure every asset in ASSETS exists in the database (safe to call many times)."""
    from .models import Asset  # imported here so this module can load before Django is ready

    for item in ASSETS:
        Asset.objects.update_or_create(
            symbol=item["symbol"],
            defaults={k: v for k, v in item.items() if k != "symbol"},
        )


def sync_assets_after_migrate(sender, **kwargs):
    """post_migrate signal receiver (connected in apps.py)."""
    sync_assets()
