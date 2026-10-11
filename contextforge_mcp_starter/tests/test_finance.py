"""Offline finance checks. FIXTURE.TEST is invented data, never a live quote."""

import json
import unittest

from finance import FinanceTools


class FixtureSource:
    def __init__(self, info=None, error=None):
        self.info = info if info is not None else {
            "symbol": "FIXTURE.TEST", "regularMarketPrice": 42.5,
            "regularMarketPreviousClose": 41.0, "currency": "USD",
            "regularMarketTime": 1720000000, "longName": "Fixture Company",
            "sector": "Fixture sector", "longBusinessSummary": "Invented test company.",
        }
        self.error = error

    def get_info(self, symbol):
        if self.error:
            raise self.error
        return self.info

    def search_symbols(self, query, limit):
        return [{"symbol": "FIXTURE.TEST", "longname": "Fixture Company", "exchange": "TEST", "quoteType": "EQUITY"}]

    def price_history(self, symbol, period, interval, limit):
        return {"currency": "USD", "truncated": False, "rows": [
            {"Date": "2026-10-01T00:00:00Z", "Open": 40, "High": 43, "Low": 39, "Close": 42, "Volume": 100},
            {"Date": "2026-10-02T00:00:00Z", "Open": 42, "High": 44, "Low": 41, "Close": 43, "Volume": 120},
        ]}

    def financial_statement(self, symbol, statement, frequency, periods):
        return {"columns": ["2026-06-30T00:00:00Z"], "index": ["Total Revenue", "Missing Fixture Metric"],
                "data": [[1000.0], [float("nan")]], "truncated": False}

    def price_history_range(self, symbol, start_date, end_date, interval, limit):
        return self.price_history(symbol, None, interval, limit)

    def get_news(self, symbol, limit):
        return [{"content": {"title": "Invented fixture headline", "provider": {"displayName": "Fixture publisher"},
                 "pubDate": "2026-10-01T00:00:00Z", "canonicalUrl": {"url": "https://example.com/fixture-news"}}}]


class FinanceResultTests(unittest.IsolatedAsyncioTestCase):
    async def test_quote_preserves_provider_price_and_market_time(self):
        result = await FinanceTools(FixtureSource()).get_stock_quote("FIXTURE.TEST")
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data["price"], 42.5)
        self.assertEqual(result.data["currency"], "USD")
        self.assertNotEqual(result.data["market_time"], result.retrieved_at)
        self.assertEqual(result.source_refs, ["https://finance.yahoo.com/quote/FIXTURE.TEST/"])

    async def test_empty_provider_quote_is_explicitly_unavailable(self):
        result = await FinanceTools(FixtureSource(info={})).get_stock_quote("FIXTURE.TEST")
        self.assertEqual(result.status, "no_data")
        self.assertIsNone(result.data)

    async def test_nonfinite_price_is_never_reported_as_a_quote(self):
        result = await FinanceTools(FixtureSource(info={"regularMarketPrice": float("nan")})).get_stock_quote("FIXTURE.TEST")
        self.assertEqual(result.status, "no_data")
        json.dumps(result.model_dump(), allow_nan=False)

    async def test_upstream_error_does_not_leak_exception_details(self):
        result = await FinanceTools(FixtureSource(error=RuntimeError("private-upstream-message"))).get_stock_quote("FIXTURE.TEST")
        self.assertEqual(result.status, "upstream_error")
        self.assertNotIn("private-upstream-message", result.model_dump_json())

    async def test_rate_limit_has_a_distinct_result(self):
        rate_limit = type("YFRateLimitError", (Exception,), {})
        result = await FinanceTools(FixtureSource(error=rate_limit())).get_stock_quote("FIXTURE.TEST")
        self.assertEqual(result.status, "rate_limited")
        self.assertIsNone(result.data)

    async def test_profile_uses_only_available_company_fields(self):
        result = await FinanceTools(FixtureSource()).get_company_profile("FIXTURE.TEST")
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data["name"], "Fixture Company")
        self.assertEqual(result.data["summary"], "Invented test company.")
        self.assertIsNone(result.data["industry"])

    async def test_history_returns_newest_rows_and_marks_truncation(self):
        result = await FinanceTools(FixtureSource()).get_price_history("FIXTURE.TEST", limit=1)
        self.assertEqual(result.status, "ok")
        self.assertEqual(len(result.data["rows"]), 1)
        self.assertEqual(result.data["rows"][0]["close"], 43)
        self.assertTrue(result.data["truncated"])

    async def test_financial_statement_preserves_missing_values_as_null(self):
        result = await FinanceTools(FixtureSource()).get_financial_statement("FIXTURE.TEST")
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data["metrics"][0]["values"], [1000.0])
        self.assertEqual(result.data["metrics"][1]["values"], [None])
        json.dumps(result.model_dump(), allow_nan=False)

    async def test_search_returns_a_bounded_symbol_list(self):
        result = await FinanceTools(FixtureSource()).search_finance_symbols("Fixture", limit=1)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data["symbols"][0]["symbol"], "FIXTURE.TEST")
        self.assertEqual(len(result.data["symbols"]), 1)

    async def test_news_contains_publisher_links_and_source_references(self):
        result = await FinanceTools(FixtureSource()).get_finance_news("FIXTURE.TEST", limit=1)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data["articles"][0]["title"], "Invented fixture headline")
        self.assertIn("https://example.com/fixture-news", result.source_refs)

    async def test_unsafe_news_link_is_not_returned(self):
        source = FixtureSource()
        source.get_news = lambda symbol, limit: [{"content": {"title": "Unsafe fixture", "canonicalUrl": {"url": "javascript:alert(1)"}}}]
        result = await FinanceTools(source).get_finance_news("FIXTURE.TEST")
        self.assertNotIn("javascript:", result.model_dump_json())


if __name__ == "__main__":
    unittest.main()
