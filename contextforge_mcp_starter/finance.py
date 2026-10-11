"""Read-only Yahoo Finance tools; provider failures never produce sample data."""

import asyncio
from collections import OrderedDict
from datetime import date, datetime, timezone
import json
import math
from pathlib import Path
import re
import time
from typing import Annotated, Literal
from urllib.parse import quote, urlsplit
from zoneinfo import ZoneInfo

import anyio
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from finance_export import render_history_csv
from finance_execution import ProviderExecutor


SYMBOL_PATTERN = r"^[A-Za-z0-9^][A-Za-z0-9.^=_-]{0,19}$"
Symbol = Annotated[str, Field(pattern=SYMBOL_PATTERN, strict=True)]
Query = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80, strict=True)]
SmallLimit = Annotated[int, Field(ge=1, le=10, strict=True)]
HistoryLimit = Annotated[int, Field(ge=1, le=366, strict=True)]
DateText = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$", strict=True)]
Symbols = Annotated[list[Symbol], Field(min_length=1, max_length=5, strict=True)]
StatementPeriods = Annotated[int, Field(ge=1, le=4, strict=True)]
Period = Literal["5d", "1mo", "3mo", "6mo", "1y"]
Interval = Literal["1d", "1wk", "1mo"]
Statement = Literal["income", "balance_sheet", "cash_flow"]
Frequency = Literal["yearly", "quarterly"]
FINANCE_TOOL_NAMES = ("get_stock_quote", "get_company_profile", "search_finance_symbols", "get_finance_news",
                      "get_price_history", "get_financial_statement", "get_price_history_range",
                      "get_price_history_batch", "export_price_history_csv")


class FinanceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["ok", "partial", "no_data", "rate_limited", "upstream_error"]
    data: dict | list | None
    provider: Literal["Yahoo Finance via yfinance"] = "Yahoo Finance via yfinance"
    retrieved_at: str
    source_refs: list[str]
    message: str | None = None
    cached: bool = False
    cache_age_seconds: float | None = None
    retry_after_seconds: int | None = None


def _number(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return value
    return None


def _text(value, limit=250):
    return value[:limit] if isinstance(value, str) and value.strip() else None


def _timestamp(value):
    try:
        return datetime.fromtimestamp(value, timezone.utc).isoformat() if _number(value) is not None else None
    except (ValueError, OverflowError, OSError):
        return None


def _safe_url(value):
    if not isinstance(value, str) or len(value) > 2000:
        return None
    try:
        url = urlsplit(value)
        return value if url.scheme in ("https", "http") and url.hostname and not (url.username or url.password) else None
    except ValueError:
        return None


def _date(value):
    if not isinstance(value, str) or len(value) > 50:
        raise ValueError("Provider returned an invalid date")
    datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value


def _calendar_date(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() == value:
            return parsed
    except (ValueError, TypeError):
        pass
    raise ValueError("Dates must be real calendar dates in YYYY-MM-DD format.")


def _validate_range(start_date: str, end_date: str) -> None:
    span = (_calendar_date(end_date) - _calendar_date(start_date)).days
    if not 1 <= span <= 366:
        raise ValueError("The end date must be after the start date, with a maximum span of 366 days.")


def _history_data(raw, symbol, interval, limit, *, period=None, start_date=None, end_date=None):
    if not raw or not raw["rows"]:
        return None
    exchange_timezone = _text(raw.get("exchange_timezone"))
    zone = ZoneInfo(exchange_timezone) if exchange_timezone else None
    rows, seen_dates = [], set()
    for item in raw["rows"]:
        time = _date(item.get("Date") or item.get("Datetime"))
        timestamp = datetime.fromisoformat(time.replace("Z", "+00:00"))
        if zone and timestamp.tzinfo is not None:
            timestamp = timestamp.astimezone(zone)
        trading_date = item.get("TradingDate") or timestamp.date().isoformat()
        _calendar_date(trading_date)
        if start_date and not start_date <= trading_date < end_date:
            continue
        if trading_date in seen_dates:
            raise ValueError("Provider returned duplicate history dates.")
        seen_dates.add(trading_date)
        rows.append({"time": time, "trading_date": trading_date,
                     "open": _number(item.get("Open")), "high": _number(item.get("High")),
                     "low": _number(item.get("Low")), "close": _number(item.get("Close")),
                     "adjusted_close": _number(item.get("Adj Close")), "volume": _number(item.get("Volume"))})
    if not rows or not any(row[field] is not None for row in rows for field in ("open", "high", "low", "close")):
        return None
    rows.sort(key=lambda row: (row["trading_date"], row["time"]))
    truncated = raw.get("truncated") is True or len(rows) > limit
    rows = rows[-limit:]
    return {"symbol": symbol, "period": period, "interval": interval,
            "start_date": start_date, "end_date": end_date, "currency": _text(raw.get("currency")),
            "exchange_timezone": exchange_timezone, "rows": rows, "row_count": len(rows),
            "first_date": rows[0]["trading_date"], "last_date": rows[-1]["trading_date"],
            "truncated": truncated, "auto_adjust": False}


class YahooFinanceSource:
    def __init__(self):
        try:
            import yfinance
        except ImportError:
            raise RuntimeError("Install requirements-finance.txt before enabling finance tools.") from None
        self.yf = yfinance
        cache = Path(__file__).resolve().parent / "state" / "yfinance-cache"
        cache.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.yf.set_tz_cache_location(str(cache))

    def get_info(self, symbol):
        return self.yf.Ticker(symbol).get_info()

    def search_symbols(self, query, limit):
        return self.yf.Search(query, max_results=limit, news_count=0, lists_count=0,
                              recommended=0, include_cb=False, timeout=15).quotes

    def get_news(self, symbol, limit):
        # Ticker's news POST currently returns empty data. Search uses Yahoo's GET API.
        # Source: https://ranaroussi.github.io/yfinance/reference/api/yfinance.Search.html
        return self.yf.Search(symbol, max_results=0, news_count=limit, lists_count=0,
                              recommended=0, include_cb=False, timeout=15).news

    def price_history(self, symbol, period, interval, limit):
        return self._history(symbol, interval, limit, period=period)

    def price_history_range(self, symbol, start_date, end_date, interval, limit):
        return self._history(symbol, interval, limit, start=start_date, end=end_date)

    def _history(self, symbol, interval, limit, **window):
        ticker = self.yf.Ticker(symbol)
        try:
            frame = ticker.history(**window, interval=interval, auto_adjust=False, timeout=15, raise_errors=True)
        except Exception as error:
            if type(error).__name__ in {"YFPricesMissingError", "YFTzMissingError"}:
                return None
            raise
        if frame.empty:
            return None
        selected = frame.tail(limit)
        # Avoid DataFrame.to_json's default ten-decimal rounding of prices.
        rows = selected.to_dict(orient="records")
        for row, timestamp in zip(rows, selected.index, strict=True):
            normalized = timestamp.tz_convert("UTC") if timestamp.tzinfo is not None else timestamp
            row["Date"] = normalized.isoformat().replace("+00:00", "Z")
            row["TradingDate"] = timestamp.date().isoformat()
        metadata = ticker.get_history_metadata()
        exchange_timezone = str(frame.index.tz) if frame.index.tz else metadata.get("exchangeTimezoneName")
        return {"rows": rows, "currency": metadata.get("currency"),
                "exchange_timezone": exchange_timezone, "truncated": len(frame) > limit}

    def financial_statement(self, symbol, statement, frequency, periods):
        ticker = self.yf.Ticker(symbol)
        methods = {"income": ticker.get_income_stmt, "balance_sheet": ticker.get_balance_sheet,
                   "cash_flow": ticker.get_cash_flow}
        frame = methods[statement](freq=frequency)
        if frame.empty:
            return None
        data = json.loads(frame.iloc[:60, :periods].to_json(orient="split", date_format="iso", date_unit="s"))
        return {**data, "truncated": frame.shape[0] > 60 or frame.shape[1] > periods}


class FinanceTools:
    def __init__(self, source=None, *, cache_ttl_seconds=30, request_timeout_seconds=30,
                 retry_delay_seconds=0.25, clock=time.monotonic):
        self.source = source if source is not None else YahooFinanceSource()
        self._executor = ProviderExecutor()
        self._cache = OrderedDict()
        self._cache_ttl = cache_ttl_seconds
        self._request_timeout = request_timeout_seconds
        self._retry_delay = retry_delay_seconds
        self._clock = clock

    async def _run(self, fetch, symbol, *, reference=None, cache_key=None):
        now = self._clock()
        if cache_key in self._cache:
            created, result = self._cache[cache_key]
            if now - created < self._cache_ttl:
                self._cache.move_to_end(cache_key)
                return result.model_copy(deep=True, update={"cached": True, "cache_age_seconds": round(now - created, 3)})
            del self._cache[cache_key]
        refs = [reference or "https://finance.yahoo.com/quote/" + quote(symbol.upper(), safe="") + "/"]
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._request_timeout
        retry_after = None
        for attempt in range(2):
            try:
                data = await self._executor.run(fetch, deadline - loop.time())
                status, message = ("ok", None) if data else ("no_data", "Yahoo Finance returned no usable data.")
                if data and "articles" in data:
                    refs.extend(article["url"] for article in data["articles"] if article["url"])
                break
            except Exception as error:
                data = None
                transient = isinstance(error, (TimeoutError, ConnectionError)) or (
                    type(error).__module__.startswith(("curl_cffi.", "httpx")) and
                    type(error).__name__ in {"ConnectionError", "ConnectError", "Timeout", "TimeoutException", "ReadTimeout", "ConnectTimeout"})
                if attempt == 0 and transient and loop.time() + self._retry_delay < deadline:
                    await anyio.sleep(self._retry_delay)
                    continue
                if type(error).__name__ == "YFRateLimitError":
                    status, message = "rate_limited", "Yahoo Finance rate-limited the request. Try again later."
                    retry_after = 60
                elif isinstance(error, TimeoutError):
                    status, message = "upstream_error", "Yahoo Finance request timed out. Try again later."
                else:
                    status, message = "upstream_error", "Yahoo Finance could not complete the request."
                break
        result = FinanceResult(status=status, data=data, source_refs=refs, message=message,
                               retry_after_seconds=retry_after, retrieved_at=datetime.now(timezone.utc).isoformat())
        if status == "ok" and cache_key is not None and self._cache_ttl > 0:
            self._cache[cache_key] = (self._clock(), result.model_copy(deep=True))
            self._cache.move_to_end(cache_key)
            while len(self._cache) > 128:
                self._cache.popitem(last=False)
        return result

    async def get_stock_quote(self, symbol: Symbol) -> FinanceResult:
        """Get the latest available Yahoo Finance quote. Market time differs from retrieval time; prices may be delayed."""
        symbol = symbol.upper()

        def fetch():
            info = self.source.get_info(symbol)
            price = _number(info.get("regularMarketPrice"))
            if price is None:
                return None
            return {"symbol": symbol, "price": price, "currency": _text(info.get("currency")),
                    "previous_close": _number(info.get("regularMarketPreviousClose")),
                    "market_time": _timestamp(info.get("regularMarketTime")),
                    "exchange": _text(info.get("exchange"))}

        return await self._run(fetch, symbol, cache_key=("quote", symbol))

    async def get_company_profile(self, symbol: Symbol) -> FinanceResult:
        """Read a company's name, sector, industry, country, website, and business summary from Yahoo Finance."""
        symbol = symbol.upper()

        def fetch():
            info = self.source.get_info(symbol)
            name = _text(info.get("longName")) or _text(info.get("shortName"))
            if not name:
                return None
            return {"symbol": symbol, "name": name, "sector": _text(info.get("sector")),
                    "industry": _text(info.get("industry")), "country": _text(info.get("country")),
                    "website": _safe_url(info.get("website")), "summary": _text(info.get("longBusinessSummary"), 2000)}

        return await self._run(fetch, symbol, cache_key=("profile", symbol))

    async def search_finance_symbols(self, query: Query, limit: SmallLimit = 5) -> FinanceResult:
        """Search Yahoo Finance for a company name or ticker; return at most ten matching symbols."""
        query = query.strip()

        def fetch():
            matches = []
            for item in self.source.search_symbols(query, limit)[:limit]:
                symbol = item.get("symbol") if isinstance(item, dict) else None
                if not isinstance(symbol, str) or not re.fullmatch(SYMBOL_PATTERN, symbol):
                    continue
                matches.append({"symbol": symbol.upper(), "name": _text(item.get("longname")) or _text(item.get("shortname")),
                                "exchange": _text(item.get("exchange")), "type": _text(item.get("quoteType"))})
            return {"query": query, "symbols": matches} if matches else None

        return await self._run(fetch, query, reference="https://finance.yahoo.com/lookup/?s=" + quote(query, safe=""),
                               cache_key=("search", query, limit))

    async def get_finance_news(self, symbol: Symbol, limit: SmallLimit = 5) -> FinanceResult:
        """Read up to ten recent Yahoo Finance headlines with publishers, publication times, and article links."""
        symbol = symbol.upper()

        def fetch():
            articles = []
            for item in self.source.get_news(symbol, limit)[:limit]:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                content = content if isinstance(content, dict) else item
                title = _text(content.get("title"), 500)
                if not title:
                    continue
                provider, link = content.get("provider", {}), content.get("canonicalUrl", {})
                publisher = provider.get("displayName") if isinstance(provider, dict) else None
                url = link.get("url") if isinstance(link, dict) else None
                articles.append({"title": title, "publisher": _text(publisher) or _text(content.get("publisher")),
                                 "published_at": _text(content.get("pubDate")) or _timestamp(content.get("providerPublishTime")),
                                 "url": _safe_url(url) or _safe_url(content.get("link"))})
            return {"symbol": symbol, "articles": articles} if articles else None

        return await self._run(fetch, symbol, cache_key=("news", symbol, limit))

    async def get_price_history(self, symbol: Symbol, period: Period = "1mo", interval: Interval = "1d",
                                limit: HistoryLimit = 366) -> FinanceResult:
        """Read up to one year and 366 OHLCV rows (default 366). OHLC is unadjusted; adjusted_close is separate. Smaller limits keep newest rows and report truncation."""
        symbol = symbol.upper()

        def fetch():
            raw = self.source.price_history(symbol, period, interval, limit)
            return _history_data(raw, symbol, interval, limit, period=period)

        return await self._run(fetch, symbol, cache_key=("history", symbol, period, interval, limit))

    async def get_price_history_range(self, symbol: Symbol, start_date: DateText, end_date: DateText,
                                      interval: Interval = "1d", limit: HistoryLimit = 366) -> FinanceResult:
        """Read OHLCV for YYYY-MM-DD dates: start inclusive, end exclusive, maximum span 366 days. Includes exchange trading dates/timezone; no rows are invented for non-trading days."""
        _validate_range(start_date, end_date)
        symbol = symbol.upper()

        def fetch():
            raw = self.source.price_history_range(symbol, start_date, end_date, interval, limit)
            return _history_data(raw, symbol, interval, limit, start_date=start_date, end_date=end_date)

        return await self._run(fetch, symbol, cache_key=("range", symbol, start_date, end_date, interval, limit))

    async def get_price_history_batch(self, symbols: Symbols, period: Period | None = None,
                                      start_date: DateText | None = None, end_date: DateText | None = None,
                                      interval: Interval = "1d", limit: HistoryLimit = 366) -> FinanceResult:
        """Read 1–5 tickers with per-symbol outcomes. Choose period OR both YYYY-MM-DD dates (start inclusive, end exclusive; span ≤366 days). Default 1mo. Deduplicates symbols; partial means some tickers failed."""
        if start_date is not None or end_date is not None:
            if start_date is None or end_date is None or period is not None:
                raise ValueError("Choose either period or both start_date and end_date, never both modes.")
            _validate_range(start_date, end_date)
        else:
            period = period or "1mo"
        symbols = list(dict.fromkeys(symbol.upper() for symbol in symbols))
        results = [None] * len(symbols)

        async def fetch_one(index, symbol):
            result = (await self.get_price_history_range(symbol, start_date, end_date, interval, limit)
                      if start_date is not None else await self.get_price_history(symbol, period, interval, limit))
            results[index] = {"symbol": symbol, **result.model_dump()}

        async with anyio.create_task_group() as group:
            for index, symbol in enumerate(symbols):
                group.start_soon(fetch_one, index, symbol)
        statuses = [result["status"] for result in results]
        successful = statuses.count("ok")
        if successful == len(results):
            status, message = "ok", None
        elif successful:
            status, message = "partial", "Some tickers returned no usable data; see per-symbol results."
        else:
            status = "rate_limited" if "rate_limited" in statuses else "upstream_error" if "upstream_error" in statuses else "no_data"
            message = "No requested ticker returned usable data; see per-symbol results."
        histories = [result["data"] for result in results if result["status"] == "ok"]
        data = {"symbols": symbols, "period": period, "start_date": start_date, "end_date": end_date,
                "interval": interval, "results": results, "row_count": sum(item["row_count"] for item in histories),
                "truncated": any(item["truncated"] for item in histories)}
        refs = list(dict.fromkeys(reference for result in results for reference in result["source_refs"]))
        return FinanceResult(status=status, data=data, message=message, source_refs=refs,
                             retrieved_at=datetime.now(timezone.utc).isoformat())

    async def export_price_history_csv(self, symbols: Symbols, period: Period | None = None,
                                       start_date: DateText | None = None, end_date: DateText | None = None,
                                       interval: Interval = "1d", limit: HistoryLimit = 366) -> FinanceResult:
        """Export 1–5 tickers as exact UTF-8 CSV content with filename, SHA-256 and per-symbol manifest. Choose period OR start/end dates (end exclusive, ≤366-day span). Default 1mo. Save data.csv verbatim in Canvas; no server file path is returned. Partial exports identify missing tickers; nulls are blank and OHLC is unadjusted."""
        result = await self.get_price_history_batch(symbols, period, start_date, end_date, interval, limit)
        return result.model_copy(update={"data": render_history_csv(result.data)})

    async def get_financial_statement(self, symbol: Symbol, statement: Statement = "income",
                                      frequency: Frequency = "quarterly", periods: StatementPeriods = 4) -> FinanceResult:
        """Read an income statement, balance sheet, or cash flow; at most four periods and sixty metrics. Currency is unreported."""
        symbol = symbol.upper()

        def fetch():
            raw = self.source.financial_statement(symbol, statement, frequency, periods)
            if not raw or not raw["index"] or not raw["columns"]:
                return None
            columns = [_date(value) for value in raw["columns"][:periods]]
            metrics = [{"name": _text(name), "values": [_number(value) for value in values[:periods]]}
                       for name, values in zip(raw["index"][:60], raw["data"][:60], strict=True)]
            if any(len(metric["values"]) != len(columns) for metric in metrics):
                raise ValueError("Provider returned inconsistent statement columns")
            return {"symbol": symbol, "statement": statement, "frequency": frequency, "currency": None,
                    "periods": columns, "metrics": metrics,
                    "truncated": raw.get("truncated") is True or len(raw["index"]) > 60 or len(raw["columns"]) > periods}

        return await self._run(fetch, symbol, cache_key=("statement", symbol, statement, frequency, periods))

    def register(self, server):
        for name in FINANCE_TOOL_NAMES:
            server.add_tool(getattr(self, name), annotations=ToolAnnotations(
                readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True))
