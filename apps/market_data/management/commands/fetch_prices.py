from django.conf import settings
from django.core.management.base import BaseCommand

from apps.data_sources.services import fetch_all
from apps.market_data.assets import sync_assets


class Command(BaseCommand):
    help = "Download current prices from CoinGecko (API) and TGJU (scraper) and save them."

    def handle(self, *args, **options):
        sync_assets()
        results = fetch_all(timeout=settings.REQUEST_TIMEOUT, backfill_days=settings.BACKFILL_DAYS)
        for r in results:
            if r["ok"]:
                self.stdout.write(self.style.SUCCESS(f"{r['symbol']:8} OK  {r['price']:,.2f}"))
            else:
                self.stdout.write(self.style.ERROR(f"{r['symbol']:8} FAILED  {r['error']}"))
        ok = sum(1 for r in results if r["ok"])
        self.stdout.write(f"{ok}/{len(results)} assets updated.")
