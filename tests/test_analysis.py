import unittest

from apps.analysis import services


class AnalysisTests(unittest.TestCase):
    def test_moving_average_waits_for_enough_data(self):
        self.assertEqual(services.moving_average([1, 2, 3, 4], 3), [None, None, 2.0, 3.0])

    def test_percent_change(self):
        self.assertEqual(services.percent_change(100, 110), 10.0)
        self.assertEqual(services.percent_change(200, 100), -50.0)
        self.assertIsNone(services.percent_change(0, 5))

    def test_volatility_needs_data_and_is_zero_for_constant_growth(self):
        self.assertIsNone(services.volatility([1, 2]))
        self.assertEqual(services.volatility([100, 100, 100, 100]), 0.0)

    def test_trend(self):
        rising = list(range(100, 130))
        falling = list(range(130, 100, -1))
        self.assertEqual(services.detect_trend(rising), "up")
        self.assertEqual(services.detect_trend(falling), "down")
        self.assertEqual(services.detect_trend([50] * 30), "flat")
        self.assertEqual(services.detect_trend([5]), "flat")

    def test_summarize(self):
        s = services.summarize([10, 20, 30])
        self.assertEqual((s["min"], s["max"], s["latest"]), (10, 30, 30))
        self.assertEqual(s["average"], 20.0)
        self.assertEqual(s["change_percent"], 200.0)
        self.assertIsNone(services.summarize([]))


if __name__ == "__main__":
    unittest.main()
