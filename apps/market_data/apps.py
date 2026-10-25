from django.apps import AppConfig


class MarketDataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.market_data"
    verbose_name = "داده بازار"

    def ready(self):
        from django.db.models.signals import post_migrate

        from .assets import sync_assets_after_migrate

        # After `migrate`, copy the ASSETS list into the database.
        post_migrate.connect(sync_assets_after_migrate, sender=self)
