"""Bound provider work even when callers stop waiting for a synchronous SDK."""

import asyncio
from concurrent.futures import ThreadPoolExecutor


class ProviderExecutor:
    def __init__(self):
        self._workers = ThreadPoolExecutor(max_workers=2, thread_name_prefix="yfinance")
        self._slots = asyncio.BoundedSemaphore(2)

    async def run(self, fetch, timeout: float):
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        await asyncio.wait_for(self._slots.acquire(), timeout=timeout)
        try:
            future = self._workers.submit(fetch)
        except BaseException:
            self._slots.release()
            raise

        def finished(_):
            # Keep the slot occupied until the actual worker finishes, even after
            # timeout/cancellation. The event loop may already be shutting down.
            try:
                loop.call_soon_threadsafe(self._slots.release)
            except RuntimeError:
                pass

        future.add_done_callback(finished)
        waiting = asyncio.wrap_future(future)
        waiting.add_done_callback(lambda done: None if done.cancelled() else done.exception())
        return await asyncio.wait_for(asyncio.shield(waiting), timeout=max(0, deadline - loop.time()))
