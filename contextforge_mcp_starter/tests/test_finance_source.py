"""SDK-boundary checks using real pandas frames and invented test values."""

import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pandas as pd

from finance import FinanceTools, YahooFinanceSource


class FinanceSourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_news_preserves_flat_provider_headlines_and_times(self):
        source = YahooFinanceSource()
        records = [{"title": "Invented search headline", "publisher": "Fixture publisher",
                    "link": "https://example.com/search-news", "providerPublishTime": 1720000000}]
        with patch.object(source.yf, "Search", return_value=SimpleNamespace(news=records)), \
                patch.object(source.yf, "Ticker", return_value=SimpleNamespace(get_news=lambda **kwargs: [])):
            result = await FinanceTools(source).get_finance_news("FIXTURE.TEST", limit=1)
        self.assertEqual(result.status, "ok")
        article = result.data["articles"][0]
        self.assertEqual(article["title"], "Invented search headline")
        self.assertEqual(article["publisher"], "Fixture publisher")
        self.assertEqual(article["published_at"], "2024-07-03T09:46:40+00:00")
        self.assertIn(article["url"], result.source_refs)

    async def test_empty_search_news_stays_explicitly_unavailable(self):
        source = YahooFinanceSource()
        with patch.object(source.yf, "Search", return_value=SimpleNamespace(news=[])), \
                patch.object(source.yf, "Ticker", return_value=SimpleNamespace(get_news=lambda **kwargs: [])):
            result = await FinanceTools(source).get_finance_news("FIXTURE.TEST")
        self.assertEqual(result.status, "no_data")
        self.assertIsNone(result.data)

    async def test_news_skips_malformed_records_without_losing_valid_articles(self):
        source = SimpleNamespace(get_news=lambda symbol, limit: [
            {"content": None}, {"content": {"title": "Invented nullable headline", "provider": None,
                                           "canonicalUrl": None}},
            {"title": "Invented flat headline", "publisher": "Fixture publisher",
             "link": "javascript:alert(1)", "providerPublishTime": "bad-timestamp"},
        ])
        result = await FinanceTools(source).get_finance_news("FIXTURE.TEST", limit=3)
        self.assertEqual(result.status, "ok")
        self.assertEqual(len(result.data["articles"]), 2)
        self.assertIsNone(result.data["articles"][0]["publisher"])
        self.assertIsNone(result.data["articles"][1]["published_at"])
        self.assertIsNone(result.data["articles"][1]["url"])
        self.assertNotIn("javascript:", result.model_dump_json())

    async def test_history_frame_preserves_dates_and_latest_rows(self):
        frame = pd.DataFrame({"Open": [40, 41, 42], "High": [42, 43, 44], "Low": [39, 40, 41],
                              "Close": [41, 42, 43], "Adj Close": [40.5, 41.5, 42.5], "Volume": [100, 110, 120]},
                             index=pd.date_range("2026-10-01", periods=3, tz="UTC", name="Date"))
        source = YahooFinanceSource()
        ticker = SimpleNamespace(history=lambda **kwargs: frame, get_history_metadata=lambda: {"currency": "USD"})
        with patch.object(source.yf, "Ticker", return_value=ticker):
            result = await FinanceTools(source).get_price_history("FIXTURE.TEST", limit=1)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data["rows"][0]["close"], 43)
        self.assertEqual(result.data["rows"][0]["adjusted_close"], 42.5)
        self.assertTrue(result.data["rows"][0]["time"].startswith("2026-10-03"))
        self.assertTrue(result.data["truncated"])

    async def test_empty_sdk_history_returns_no_data(self):
        source = YahooFinanceSource()
        ticker = SimpleNamespace(history=lambda **kwargs: pd.DataFrame())
        with patch.object(source.yf, "Ticker", return_value=ticker):
            result = await FinanceTools(source).get_price_history("FIXTURE.TEST")
        self.assertEqual(result.status, "no_data")
        self.assertIsNone(result.data)

    async def test_foreign_exchange_trading_date_survives_utc_conversion(self):
        frame = pd.DataFrame({"Close": [100, 101]},
            index=pd.date_range("2026-10-01", periods=2, tz="Asia/Tokyo", name="Date"))
        source = YahooFinanceSource()
        ticker = SimpleNamespace(history=lambda **kwargs: frame,
                                 get_history_metadata=lambda: {"currency": "JPY"})
        with patch.object(source.yf, "Ticker", return_value=ticker):
            result = await FinanceTools(source).get_price_history_range(
                "FIXTURE.TEST", "2026-10-01", "2026-10-03")
        self.assertEqual(result.data["exchange_timezone"], "Asia/Tokyo")
        self.assertEqual(result.data["rows"][0]["time"], "2026-09-30T15:00:00Z")
        self.assertEqual(result.data["rows"][0]["trading_date"], "2026-10-01")
        self.assertEqual(result.data["first_date"], "2026-10-01")

    async def test_history_serialization_does_not_round_provider_floats(self):
        price = 40.12345678912345
        frame = pd.DataFrame({"Close": [price], "Adj Close": [float("nan")], "Volume": [100]},
            index=pd.date_range("2026-10-01", periods=1, tz="UTC", name="Date"))
        source = YahooFinanceSource()
        ticker = SimpleNamespace(history=lambda **kwargs: frame,
                                 get_history_metadata=lambda: {"currency": "USD"})
        with patch.object(source.yf, "Ticker", return_value=ticker):
            result = await FinanceTools(source).get_price_history("FIXTURE.TEST")
        self.assertEqual(result.data["rows"][0]["close"], price)
        self.assertIsNone(result.data["rows"][0]["adjusted_close"])

    async def test_missing_prices_are_no_data_but_rate_limits_propagate(self):
        source = YahooFinanceSource()
        for error_name, expected in [("YFPricesMissingError", "no_data"), ("YFRateLimitError", "rate_limited")]:
            error = type(error_name, (Exception,), {})
            with patch.object(source.yf, "Ticker") as ticker:
                ticker.return_value.history.side_effect = error("private-upstream-details")
                result = await FinanceTools(source).get_price_history_range(
                    "FIXTURE.TEST", "2026-10-01", "2026-10-03")
            self.assertEqual(result.status, expected)
            self.assertNotIn("private-upstream-details", result.model_dump_json())

    async def test_statement_dates_and_missing_values_are_json_safe(self):
        frame = pd.DataFrame([[1000.0, 900.0], [float("nan"), 100.0]],
                             index=["Total Revenue", "Missing Fixture Metric"],
                             columns=pd.to_datetime(["2026-06-30", "2026-03-31"]))
        source = YahooFinanceSource()
        ticker = SimpleNamespace(get_income_stmt=lambda **kwargs: frame,
                                 get_balance_sheet=lambda **kwargs: frame, get_cash_flow=lambda **kwargs: frame)
        with patch.object(source.yf, "Ticker", return_value=ticker):
            result = await FinanceTools(source).get_financial_statement("FIXTURE.TEST", periods=1)
        self.assertEqual(result.status, "ok")
        self.assertTrue(result.data["periods"][0].startswith("2026-06-30"))
        self.assertEqual(result.data["metrics"][1]["values"], [None])
        self.assertTrue(result.data["truncated"])
        json.dumps(result.model_dump(), allow_nan=False)

    async def test_invalid_reporting_date_is_an_upstream_error(self):
        source = YahooFinanceSource()
        frame = pd.DataFrame([[1000.0]], index=["Fixture Revenue"], columns=["invalid-date"])
        ticker = SimpleNamespace(get_income_stmt=lambda **kwargs: frame,
                                 get_balance_sheet=lambda **kwargs: frame, get_cash_flow=lambda **kwargs: frame)
        with patch.object(source.yf, "Ticker", return_value=ticker):
            result = await FinanceTools(source).get_financial_statement("FIXTURE.TEST")
        self.assertEqual(result.status, "upstream_error")
        self.assertIsNone(result.data)


if __name__ == "__main__":
    unittest.main()
