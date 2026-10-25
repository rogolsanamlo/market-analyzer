import unittest

from apps.data_sources.api_clients import coingecko_client as cg
from apps.data_sources.scrapers import tgju_scraper as tg


class CoinGeckoParsingTests(unittest.TestCase):
    def test_simple_price(self):
        data = {"bitcoin": {"usd": 65000.5}, "ethereum": {"usd": 3200}}
        self.assertEqual(cg.parse_simple_price(data, ["bitcoin", "ethereum", "dogecoin"]),
                         {"bitcoin": 65000.5, "ethereum": 3200.0})

    def test_market_chart(self):
        data = {"prices": [[1700000000000, 100.0], [1700086400000, 105.5]]}
        points = cg.parse_market_chart(data)
        self.assertEqual([p for _, p in points], [100.0, 105.5])
        first = points[0][0]
        self.assertEqual((first.year, first.month, first.day), (2023, 11, 14))
        self.assertIsNotNone(first.tzinfo)

    def test_bad_market_chart_raises(self):
        with self.assertRaises(cg.CoinGeckoError):
            cg.parse_market_chart({"oops": 1})


class TgjuParsingTests(unittest.TestCase):
    def test_parse_price_text_handles_persian_digits_and_separators(self):
        self.assertEqual(tg.parse_price_text("۲٬۶۸۸٬۲۰۰"), 2688200.0)
        self.assertEqual(tg.parse_price_text("2,688,200"), 2688200.0)

    def test_parse_price_text_without_number_raises(self):
        with self.assertRaises(tg.TgjuScraperError):
            tg.parse_price_text("---")

    def test_parse_price_from_html(self):
        html = '<div><span data-col="info.last_trade.PDrCotVal">2,688,200</span></div>'
        self.assertEqual(tg.parse_price_from_html(html), 2688200.0)

    def test_missing_element_raises(self):
        with self.assertRaises(tg.TgjuScraperError):
            tg.parse_price_from_html("<html><body>nothing here</body></html>")


if __name__ == "__main__":
    unittest.main()
