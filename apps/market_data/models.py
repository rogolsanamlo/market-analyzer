"""Database tables.

Asset        - something we track (BTC, USD, ...)
PriceRecord  - one price of one asset at one moment
"""
from django.db import models

DEMO_SOURCE = "demo"
# If an asset has at least this many real points, demo points are hidden.
MIN_REAL_POINTS = 5


class Asset(models.Model):
    SOURCE_COINGECKO = "coingecko"
    SOURCE_TGJU = "tgju"

    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20)  # crypto / currency / gold
    unit = models.CharField(max_length=20)      # USD / تومان
    source = models.CharField(max_length=20)    # coingecko -> API, tgju -> scraper
    source_id = models.CharField(max_length=100)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.symbol} ({self.name})"


class PriceRecord(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="prices")
    price = models.FloatField()
    recorded_at = models.DateTimeField()
    source = models.CharField(max_length=20)

    class Meta:
        ordering = ["recorded_at"]
        constraints = [
            models.UniqueConstraint(fields=["asset", "recorded_at"], name="unique_price_per_time"),
        ]
        indexes = [
            models.Index(fields=["asset", "recorded_at"], name="price_asset_time_idx"),
        ]

    def __str__(self):
        return f"{self.asset.symbol} {self.price} @ {self.recorded_at:%Y-%m-%d %H:%M}"
