"""History/export behavior with explicitly invented prices and tickers."""

import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import unittest

from finance import FinanceTools
from test_finance import FixtureSource


class RangeSource(FixtureSource):
    def price_history_range(self, symbol, start_date, end_date, interval, limit):
        if symbol == "MISSING.TEST":
            return None
        if symbol == "BROKEN.TEST":
            raise RuntimeError("private-provider-detail")
        return {"currency": "USD", "exchange_timezone": "UTC", "truncated": False,
                "rows": [
                    {"Date": "2026-10-01T00:00:00Z", "Open": 40.1234567891, "High": 43,
                     "Low": 39, "Close": 42, "Adj Close": 41.25, "Volume": 100},
                    {"Date": "2026-10-02T00:00:00Z", "Open": 42, "High": 44,
                     "Low": 41, "Close": 43, "Adj Close": None, "Volume": 120},
                    {"Date": "2026-10-03T00:00:00Z", "Open": 43, "High": 45,
                     "Low": 42, "Close": 44, "Adj Close": 43.25, "Volume": 140},
                ]}


class HistoryRangeTests(unittest.IsolatedAsyncioTestCase):
    async def test_duplicate_history_buckets_are_an_explicit_upstream_error(self):
        source = RangeSource()
        original = source.price_history_range

        def duplicate_bucket(*args):
            raw = original(*args)
            raw["rows"] = [raw["rows"][0], raw["rows"][0]]
            return raw

        source.price_history_range = duplicate_bucket
        result = await FinanceTools(source).get_price_history_range("FIXTURE.TEST", "2026-10-01", "2026-10-03")
        self.assertEqual(result.status, "upstream_error")
        self.assertIsNone(result.data)

    async def test_all_missing_prices_are_unavailable_instead_of_a_successful_history(self):
        source = FixtureSource()
        source.price_history = lambda *args: {"rows": [{"Date": "2026-10-01T00:00:00Z", "Volume": 0}], "truncated": False}
        result = await FinanceTools(source).get_price_history("FIXTURE.TEST")
        self.assertEqual(result.status, "no_data")
        self.assertIsNone(result.data)

    async def test_start_is_inclusive_and_end_is_exclusive(self):
        result = await FinanceTools(RangeSource()).get_price_history_range(
            "FIXTURE.TEST", "2026-10-01", "2026-10-03")
        self.assertEqual(result.status, "ok")
        self.assertEqual([row["trading_date"] for row in result.data["rows"]],
                         ["2026-10-01", "2026-10-02"])
        self.assertEqual(result.data["row_count"], 2)
        self.assertEqual(result.data["first_date"], "2026-10-01")
        self.assertEqual(result.data["last_date"], "2026-10-02")
        self.assertFalse(result.data["truncated"])

    async def test_default_limit_does_not_cut_a_calendar_year_to_100_rows(self):
        source = FixtureSource()
        start = datetime(2025, 10, 11, tzinfo=timezone.utc)
        source.price_history = lambda *args: {
            "rows": [{"Date": (start + timedelta(days=offset)).isoformat(),
                      "Close": offset + 1} for offset in range(365)], "truncated": False}
        result = await FinanceTools(source).get_price_history("FIXTURE.TEST", period="1y")
        self.assertEqual(result.data["row_count"], 365)
        self.assertFalse(result.data["truncated"])

    async def test_invalid_calendar_ranges_are_rejected_before_provider_access(self):
        tools = FinanceTools(RangeSource())
        for start, end in [("2026-02-30", "2026-03-01"), ("20261001", "2026-10-03"),
                           ("2026-10-03", "2026-10-03"), ("2026-10-04", "2026-10-03"),
                           ("2025-01-01", "2026-01-03")]:
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                await tools.get_price_history_range("FIXTURE.TEST", start, end)

    async def test_explicit_limit_keeps_latest_rows_and_reports_omission(self):
        result = await FinanceTools(RangeSource()).get_price_history_range(
            "FIXTURE.TEST", "2026-10-01", "2026-10-04", limit=1)
        self.assertEqual(result.data["rows"][0]["trading_date"], "2026-10-03")
        self.assertTrue(result.data["truncated"])


class BatchExportTests(unittest.IsolatedAsyncioTestCase):
    async def test_csv_escapes_untrusted_formula_text_but_preserves_numeric_values(self):
        source = RangeSource()
        original = source.price_history_range

        def unsafe_currency(*args):
            data = original(*args)
            data["currency"] = "=HYPERLINK(\"https://example.com\",\"Fixture\")"
            data["rows"][0]["Open"] = -1.25
            return data

        source.price_history_range = unsafe_currency
        result = await FinanceTools(source).export_price_history_csv(
            ["FIXTURE.TEST"], start_date="2026-10-01", end_date="2026-10-03")
        rows = list(csv.DictReader(io.StringIO(result.data["csv"])))
        self.assertTrue(rows[0]["currency"].startswith("'="))
        self.assertEqual(rows[0]["open"], "-1.25")

    async def test_batch_normalizes_and_deduplicates_symbols(self):
        result = await FinanceTools(RangeSource()).get_price_history_batch(
            ["fixture.test", "FIXTURE.TEST", "SECOND.TEST"],
            start_date="2026-10-01", end_date="2026-10-03")
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data["symbols"], ["FIXTURE.TEST", "SECOND.TEST"])
        self.assertEqual(result.data["row_count"], 4)
        self.assertEqual(len(result.data["results"]), 2)

    async def test_partial_failure_preserves_successful_ticker_and_explains_failures(self):
        result = await FinanceTools(RangeSource()).get_price_history_batch(
            ["FIXTURE.TEST", "MISSING.TEST", "BROKEN.TEST"],
            start_date="2026-10-01", end_date="2026-10-03")
        self.assertEqual(result.status, "partial")
        self.assertEqual([item["status"] for item in result.data["results"]],
                         ["ok", "no_data", "upstream_error"])
        self.assertEqual(result.data["row_count"], 2)
        self.assertNotIn("private-provider-detail", result.model_dump_json())

    async def test_csv_is_exact_chronological_and_keeps_missing_adjusted_close_blank(self):
        result = await FinanceTools(RangeSource()).export_price_history_csv(
            ["SECOND.TEST", "FIXTURE.TEST"], start_date="2026-10-01", end_date="2026-10-03")
        self.assertEqual(result.status, "ok")
        export = result.data
        rows = list(csv.DictReader(io.StringIO(export["csv"])))
        self.assertEqual(export["mime_type"], "text/csv")
        self.assertEqual(len(rows), export["row_count"])
        self.assertEqual(len(rows), 4)
        self.assertEqual([(row["trading_date"], row["symbol"]) for row in rows],
                         sorted((row["trading_date"], row["symbol"]) for row in rows))
        self.assertEqual(rows[0]["open"], "40.1234567891")
        self.assertEqual(rows[0]["adjusted_close"], "41.25")
        self.assertEqual(rows[-1]["adjusted_close"], "")
        self.assertEqual(export["sha256"], hashlib.sha256(export["csv"].encode()).hexdigest())
        self.assertEqual(export["byte_count"], len(export["csv"].encode()))
        self.assertEqual(export["first_date"], "2026-10-01")
        self.assertEqual(export["last_date"], "2026-10-02")
        self.assertTrue(export["filename"].endswith(".csv"))

    async def test_no_data_does_not_create_a_fake_or_empty_successful_csv(self):
        result = await FinanceTools(RangeSource()).export_price_history_csv(
            ["MISSING.TEST"], start_date="2026-10-01", end_date="2026-10-03")
        self.assertEqual(result.status, "no_data")
        self.assertEqual(result.data["row_count"], 0)
        self.assertIsNone(result.data["csv"])

    async def test_partial_csv_identifies_missing_symbols_and_contains_only_real_rows(self):
        result = await FinanceTools(RangeSource()).export_price_history_csv(
            ["FIXTURE.TEST", "MISSING.TEST"], start_date="2026-10-01", end_date="2026-10-03")
        self.assertEqual(result.status, "partial")
        rows = list(csv.DictReader(io.StringIO(result.data["csv"])))
        self.assertEqual({row["symbol"] for row in rows}, {"FIXTURE.TEST"})
        self.assertEqual(result.data["results"][1]["status"], "no_data")
        self.assertEqual(result.data["results"][1]["row_count"], 0)

    async def test_period_and_dates_cannot_be_combined_or_half_specified(self):
        tools = FinanceTools(RangeSource())
        for arguments in [{"period": "1mo", "start_date": "2026-10-01", "end_date": "2026-10-03"},
                          {"start_date": "2026-10-01"}, {"end_date": "2026-10-03"}]:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                await tools.export_price_history_csv(["FIXTURE.TEST"], **arguments)


if __name__ == "__main__":
    unittest.main()
