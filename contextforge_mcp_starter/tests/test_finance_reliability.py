"""Controlled provider errors/timing; these are not live Yahoo results."""

import asyncio
from threading import Event, Lock
import unittest

from finance import FinanceTools
from test_finance import FixtureSource


class ReliabilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_cache_preserves_original_retrieval_time_and_expires(self):
        clock = [100.0]
        source = FixtureSource()
        tools = FinanceTools(source, cache_ttl_seconds=30, clock=lambda: clock[0])
        first = await tools.get_stock_quote("FIXTURE.TEST")
        source.info["regularMarketPrice"] = 99.0
        clock[0] = 110.0
        cached = await tools.get_stock_quote("fixture.test")
        self.assertEqual(cached.data["price"], 42.5)
        self.assertTrue(cached.cached)
        self.assertEqual(cached.cache_age_seconds, 10)
        self.assertEqual(cached.retrieved_at, first.retrieved_at)
        clock[0] = 131.0
        refreshed = await tools.get_stock_quote("FIXTURE.TEST")
        self.assertEqual(refreshed.data["price"], 99.0)
        self.assertFalse(refreshed.cached)

    async def test_cache_copies_prevent_a_caller_from_modifying_later_results(self):
        tools = FinanceTools(FixtureSource())
        first = await tools.get_stock_quote("FIXTURE.TEST")
        first.data["price"] = -100
        later = await tools.get_stock_quote("FIXTURE.TEST")
        self.assertEqual(later.data["price"], 42.5)
        self.assertTrue(later.cached)

    async def test_success_cache_is_bounded_and_evicts_the_oldest_entry(self):
        source = FixtureSource()
        tools = FinanceTools(source, clock=lambda: 100.0)
        for index in range(129):
            await tools.get_stock_quote("FIXTURE" + str(index))
        source.info["regularMarketPrice"] = 99.0
        evicted = await tools.get_stock_quote("FIXTURE0")
        retained = await tools.get_stock_quote("FIXTURE128")
        self.assertEqual(evicted.data["price"], 99.0)
        self.assertFalse(evicted.cached)
        self.assertEqual(retained.data["price"], 42.5)
        self.assertTrue(retained.cached)

    async def test_a_permanent_transport_failure_stops_after_two_attempts(self):
        source = FixtureSource()
        attempts = []

        def unavailable(symbol):
            attempts.append(symbol)
            raise ConnectionError("private-network-details")

        source.get_info = unavailable
        result = await FinanceTools(source, retry_delay_seconds=0).get_stock_quote("FIXTURE.TEST")
        self.assertEqual(result.status, "upstream_error")
        self.assertEqual(len(attempts), 2)
        self.assertNotIn("private-network-details", result.model_dump_json())

    async def test_failure_is_not_cached_and_next_call_can_recover(self):
        source = FixtureSource(error=RuntimeError("private-message"))
        tools = FinanceTools(source)
        first = await tools.get_stock_quote("FIXTURE.TEST")
        self.assertEqual(first.status, "upstream_error")
        source.error = None
        recovered = await tools.get_stock_quote("FIXTURE.TEST")
        self.assertEqual(recovered.status, "ok")
        self.assertFalse(recovered.cached)

    async def test_transient_transport_failure_gets_one_bounded_retry(self):
        source = FixtureSource()
        attempts = []

        def fetch(symbol):
            attempts.append(symbol)
            if len(attempts) == 1:
                raise ConnectionError("private-network-message")
            return source.info

        source.get_info = fetch
        result = await FinanceTools(source, retry_delay_seconds=0).get_stock_quote("FIXTURE.TEST")
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data["price"], 42.5)
        self.assertEqual(len(attempts), 2)

    async def test_rate_limits_are_not_retried_immediately_or_disguised_as_no_data(self):
        source = FixtureSource()
        attempts = []
        rate_limit = type("YFRateLimitError", (Exception,), {})

        def fetch(symbol):
            attempts.append(symbol)
            raise rate_limit("private-rate-limit-message")

        source.get_info = fetch
        result = await FinanceTools(source, retry_delay_seconds=0).get_stock_quote("FIXTURE.TEST")
        self.assertEqual(result.status, "rate_limited")
        self.assertEqual(len(attempts), 1)
        self.assertEqual(result.retry_after_seconds, 60)
        self.assertNotIn("private-rate-limit-message", result.model_dump_json())

    async def test_timed_out_workers_remain_bounded_and_service_can_recover(self):
        source = FixtureSource()
        release, finished, lock = Event(), Event(), Lock()
        active, maximum = [0], [0]

        def blocking_fetch(symbol):
            with lock:
                active[0] += 1
                maximum[0] = max(maximum[0], active[0])
            try:
                release.wait(2)
                return source.info
            finally:
                with lock:
                    active[0] -= 1
                    if active[0] == 0:
                        finished.set()

        source.get_info = blocking_fetch
        tools = FinanceTools(source, request_timeout_seconds=0.05, cache_ttl_seconds=0,
                             retry_delay_seconds=0)
        try:
            results = await asyncio.gather(*(tools.get_stock_quote("FIXTURE.TEST") for _ in range(5)))
            self.assertTrue(all(result.status == "upstream_error" for result in results))
            self.assertTrue(all(result.data is None for result in results))
            self.assertLessEqual(maximum[0], 2)
            self.assertLessEqual(active[0], 2)
        finally:
            release.set()
            await asyncio.to_thread(finished.wait, 2)
        recovered = await tools.get_stock_quote("FIXTURE.TEST")
        self.assertEqual(recovered.status, "ok")


if __name__ == "__main__":
    unittest.main()
