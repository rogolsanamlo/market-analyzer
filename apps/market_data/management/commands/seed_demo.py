from django.core.management.base import BaseCommand

from apps.data_sources.sample_data import seed_demo
from apps.market_data.assets import sync_assets
from apps.market_data.models import PriceRecord


class Command(BaseCommand):
    help = "Add made-up demo prices so the dashboard has something to show before the first real fetch."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="delete ALL saved prices first")

    def handle(self, *args, **options):
        sync_assets()
        if options["reset"]:
            deleted, _ = PriceRecord.objects.all().delete()
            self.stdout.write(f"Deleted {deleted} price rows.")
        seeded = seed_demo()
        if seeded:
            self.stdout.write(self.style.SUCCESS("Demo data added for: " + ", ".join(seeded)))
        else:
            self.stdout.write("Nothing to add (every asset already has data).")
