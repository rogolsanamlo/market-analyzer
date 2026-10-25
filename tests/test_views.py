"""Tests that need Django (run with: python manage.py test)."""
from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.data_sources import services as source_services
from apps.data_sources.sample_data import seed_demo
from apps.market_data import queries
from apps.market_data.assets import sync_assets
from apps.market_data.models import Asset


class DashboardApiTests(TestCase):
    def setUp(self):
        sync_assets()
        seed_demo()

    def test_dashboard_page(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "تحلیلگر بازار")

    def test_assets_endpoint(self):
        data = self.client.get(reverse("analysis:assets")).json()
        self.assertEqual({a["symbol"] for a in data}, {"BTC", "ETH", "USD", "GOLD18", "COIN"})
        self.assertTrue(all(a["is_demo"] for a in data))
        self.assertIsNotNone(data[0]["summary"]["latest"])

    def test_history_endpoint(self):
        data = self.client.get(reverse("analysis:history", args=["btc"]), {"days": 30}).json()
        n = len(data["prices"])
        self.assertGreater(n, 10)
        self.assertEqual(len(data["ma7"]), n)
        self.assertEqual(len(data["labels"]), n)
        self.assertIsNone(data["ma7"][0])
        self.assertIsNotNone(data["ma7"][-1])

    def test_history_unknown_symbol(self):
        response = self.client.get(reverse("analysis:history", args=["NOPE"]))
        self.assertEqual(response.status_code, 404)

    def test_history_bad_days_does_not_crash(self):
        response = self.client.get(reverse("analysis:history", args=["BTC"]), {"days": "abc"})
        self.assertEqual(response.status_code, 200)

    def test_seed_is_idempotent(self):
        self.assertEqual(seed_demo(), [])

    def test_real_data_replaces_demo(self):
        btc = Asset.objects.get(symbol="BTC")
        now = timezone.now()
        points = [(now - timedelta(hours=i), 100 + i) for i in range(1, 8)]
        queries.add_prices(btc, points, "coingecko")
        history, is_demo = queries.get_history(btc, days=30)
        self.assertFalse(is_demo)
        self.assertEqual(len(history), 7)

    def test_duplicate_timestamp_is_ignored(self):
        btc = Asset.objects.get(symbol="BTC")
        moment = timezone.now().replace(microsecond=0)
        queries.add_price(btc, 1, "coingecko", moment)
        queries.add_price(btc, 2, "coingecko", moment)
        self.assertEqual(btc.prices.filter(recorded_at=moment).count(), 1)

    def test_refresh_requires_post(self):
        self.assertEqual(self.client.get(reverse("analysis:refresh")).status_code, 405)

    def test_refresh_reports_failures_without_crashing(self):
        with mock.patch.object(source_services.coingecko_client, "get_current_prices",
                               side_effect=source_services.CoinGeckoError("offline")), \
             mock.patch.object(source_services.tgju_scraper, "get_price_toman",
                               side_effect=source_services.TgjuScraperError("offline")):
            data = self.client.post(reverse("analysis:refresh")).json()
        self.assertEqual(data["updated"], 0)
        self.assertEqual(len(data["results"]), 5)
        self.assertFalse(any(r["ok"] for r in data["results"]))

    def test_refresh_saves_prices(self):
        with mock.patch.object(source_services.coingecko_client, "get_current_prices",
                               return_value={"bitcoin": 70000.0, "ethereum": 3500.0}), \
             mock.patch.object(source_services.coingecko_client, "get_history", return_value=[]), \
             mock.patch.object(source_services.tgju_scraper, "get_price_toman", return_value=270000.0):
            data = self.client.post(reverse("analysis:refresh")).json()
        self.assertEqual(data["updated"], 5)
        usd = Asset.objects.get(symbol="USD")
        self.assertEqual(queries.count_prices(usd, include_demo=False), 1)
