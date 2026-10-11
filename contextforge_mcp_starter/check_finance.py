"""Exercise authenticated MCP against real Yahoo Finance without opening a port."""

import argparse
import asyncio
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import secrets
from unittest.mock import patch

import httpx

from finance import FINANCE_TOOL_NAMES, FinanceTools, YahooFinanceSource
from server import create_app


TOOL_INPUTS = {
    "search_finance_symbols": {"query": "AAPL", "limit": 3},
    "get_stock_quote": {"symbol": "AAPL"},
    "get_company_profile": {"symbol": "AAPL"},
    "get_price_history": {"symbol": "AAPL", "period": "5d", "interval": "1d", "limit": 5},
    "get_financial_statement": {"symbol": "AAPL", "statement": "income", "frequency": "quarterly", "periods": 1},
    "get_finance_news": {"symbol": "AAPL", "limit": 2},
    "get_price_history_range": {"symbol": "AAPL", "start_date": "2026-09-01", "end_date": "2026-10-01"},
    "get_price_history_batch": {"symbols": ["AAPL", "MSFT"], "period": "5d"},
    "export_price_history_csv": {"symbols": ["AAPL", "MSFT", "NVDA"], "start_date": "2026-09-01", "end_date": "2026-10-01"},
}

SCENARIOS = {
    "stock_quarter_range": ("get_price_history_range", {"symbol": "AAPL", "start_date": "2026-01-01", "end_date": "2026-04-01"}, "ok"),
    "etf_weekly": ("get_price_history", {"symbol": "SPY", "period": "3mo", "interval": "1wk"}, "ok"),
    "crypto_full_year": ("get_price_history", {"symbol": "BTC-USD", "period": "1y"}, "ok"),
    "foreign_exchange_dates": ("get_price_history_range", {"symbol": "7203.T", "start_date": "2026-09-01", "end_date": "2026-10-01"}, "ok"),
    "currency_pair": ("get_price_history", {"symbol": "EURUSD=X", "period": "5d"}, "ok"),
    "stock_weekend_no_data": ("get_price_history_range", {"symbol": "AAPL", "start_date": "2026-09-12", "end_date": "2026-09-14"}, "no_data"),
    "crypto_weekend_trades": ("get_price_history_range", {"symbol": "BTC-USD", "start_date": "2026-09-12", "end_date": "2026-09-14"}, "ok"),
    "partial_batch": ("get_price_history_batch", {"symbols": ["AAPL", "ZZNOEXIST99", "MSFT"], "period": "5d"}, "partial"),
    "partial_csv": ("export_price_history_csv", {"symbols": ["AAPL", "ZZNOEXIST99"], "period": "5d"}, "partial"),
    "cached_quote": ("get_stock_quote", {"symbol": "AAPL"}, "ok"),
}


def verify_scenario(name, content, arguments, expected):
    if not isinstance(content, dict) or content.get("status") != expected:
        return False
    if expected == "no_data":
        return content["data"] is None
    data = content["data"]
    if name == "cached_quote":
        return content["cached"] and content["cache_age_seconds"] >= 0
    if "csv" in data:
        rows = list(csv.DictReader(io.StringIO(data["csv"])))
        return (len(rows) == data["row_count"] > 0 and not data["truncated"]
                and data["sha256"] == hashlib.sha256(data["csv"].encode()).hexdigest()
                and {row["symbol"] for row in rows} == {"AAPL"}
                and data["results"][1]["status"] == "no_data")
    if "results" in data:
        return ([item["status"] for item in data["results"]] == ["ok", "no_data", "ok"]
                and not data["truncated"] and data["row_count"] > 0)
    rows = data["rows"]
    dates = [row["trading_date"] for row in rows]
    if not rows or data["truncated"] or data["row_count"] != len(rows) or dates != sorted(set(dates)):
        return False
    if "start_date" in arguments and not all(arguments["start_date"] <= value < arguments["end_date"] for value in dates):
        return False
    if name == "crypto_full_year":
        return len(rows) > 252
    if name == "foreign_exchange_dates":
        return data["exchange_timezone"] == "Asia/Tokyo" and any(row["time"][:10] != row["trading_date"] for row in rows)
    if name == "crypto_weekend_trades":
        return dates == ["2026-09-12", "2026-09-13"]
    return True


def diagnose_news():
    """Capture provider response shapes only; never headers, cookies, or secrets."""
    source = YahooFinanceSource()
    receipt = {"checked_at": datetime.now(timezone.utc).isoformat(),
               "source": "real Yahoo Finance via yfinance", "devrev_call": False,
               "purpose": "news response-shape diagnosis, not MCP readiness", "checks": []}
    calls = {
        "ticker_news_2": lambda: source.yf.Ticker("AAPL").get_news(count=2),
        "ticker_news_10": lambda: source.yf.Ticker("AAPL").get_news(count=10),
        "search_news_2": lambda: source.yf.Search("AAPL", max_results=0, news_count=2,
            lists_count=0, recommended=0, include_cb=False, timeout=15).news,
    }
    for name, fetch in calls.items():
        try:
            records = fetch()
            shapes = []
            for item in records[:3]:
                content = item.get("content") if isinstance(item, dict) else None
                shapes.append({"record_type": type(item).__name__,
                    "keys": sorted(str(key)[:80] for key in item) if isinstance(item, dict) else [],
                    "content_type": type(content).__name__,
                    "content_keys": sorted(str(key)[:80] for key in content) if isinstance(content, dict) else [],
                    "has_flat_title": isinstance(item, dict) and bool(item.get("title")),
                    "has_nested_title": isinstance(content, dict) and bool(content.get("title"))})
            receipt["checks"].append({"name": name, "completed": True,
                                      "raw_count": len(records), "shapes": shapes})
            print(name + ": returned " + str(len(records)) + " raw records", flush=True)
        except Exception as error:
            receipt["checks"].append({"name": name, "completed": False,
                                      "error_type": type(error).__name__})
            print(name + ": " + type(error).__name__, flush=True)
    receipt["status"] = "COMPLETE" if all(c["completed"] for c in receipt["checks"]) else "FAIL"
    return receipt


async def check(tools, *, scenarios=False):
    receipt = {"checked_at": datetime.now(timezone.utc).isoformat(), "transport": "in-process ASGI MCP HTTP",
               "source": "real Yahoo Finance via yfinance", "devrev_call": False, "checks": [],
               "complete_finance_tool_check": set(tools) == set(TOOL_INPUTS),
               "complete_six_tool_check": set(list(TOOL_INPUTS)[:6]) <= set(tools),
               "build_sha256": {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                for name in ["server.py", "finance.py", "finance_export.py", "finance_execution.py", "check_finance.py"]}}
    token = secrets.token_urlsafe(32)  # Temporary in-process authentication; never logged or saved.
    with patch.dict(os.environ, {"MCP_TOKEN": token, "CONTEXTFORGE_ENABLE_WORKFLOW": "0", "CONTEXTFORGE_ENABLE_FINANCE": "1"}):
        app = create_app(finance=FinanceTools())
        async with app.app.router.lifespan_context(app.app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8000",
                    headers={"Authorization": "Bearer " + token, "Accept": "application/json, text/event-stream"}) as client:
                async def rpc(method, params):
                    response = await client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
                    response.raise_for_status()
                    return response.json()

                for mode in ["missing", "incorrect"]:
                    request = client.build_request("POST", "/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
                    request.headers.pop("Authorization", None)
                    if mode == "incorrect":
                        request.headers["Authorization"] = "Bearer incorrect-readiness-token"
                    response = await client.send(request)
                    receipt["checks"].append({"name": "unauthorized_" + mode, "status": "PASS" if response.status_code == 401 else "FAIL",
                                               "http_status": response.status_code})

                initialized = await rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                         "clientInfo": {"name": "finance-readiness", "version": "1"}})
                receipt["checks"].append({"name": "authenticated_initialize", "status": "PASS" if "result" in initialized else "FAIL"})
                discovered = await rpc("tools/list", {})
                names = {item["name"] for item in discovered.get("result", {}).get("tools", [])}
                expected = set(FINANCE_TOOL_NAMES) | {"ping", "inspect_demo_capability"}
                receipt["checks"].append({"name": "tool_discovery", "status": "PASS" if names == expected else "FAIL", "tools": sorted(names)})

                for name in tools:
                    response = await rpc("tools/call", {"name": name, "arguments": TOOL_INPUTS[name]})
                    result = response.get("result", {})
                    content = result.get("structuredContent")
                    passed = (not result.get("isError") and isinstance(content, dict) and content.get("status") == "ok"
                              and bool(content.get("data")) and bool(content.get("source_refs")))
                    receipt["checks"].append({"name": name, "status": "PASS" if passed else "FAIL", "response": content,
                        "response_sha256": hashlib.sha256(json.dumps(content, sort_keys=True, allow_nan=False).encode()).hexdigest()})
                    print(name + ": " + ("PASS" if passed else "FAIL"), flush=True)
                if scenarios:
                    for name, (tool, arguments, expected_status) in SCENARIOS.items():
                        if name == "cached_quote":
                            await rpc("tools/call", {"name": tool, "arguments": arguments})
                        response = await rpc("tools/call", {"name": tool, "arguments": arguments})
                        result = response.get("result", {})
                        content = result.get("structuredContent")
                        passed = not result.get("isError") and verify_scenario(name, content, arguments, expected_status)
                        receipt["checks"].append({"name": name, "status": "PASS" if passed else "FAIL",
                            "expected_status": expected_status, "arguments": arguments, "response": content})
                        print(name + ": " + ("PASS" if passed else "FAIL"), flush=True)
    receipt["status"] = "PASS" if all(item["status"] == "PASS" for item in receipt["checks"]) else "FAIL"
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--tool", action="append", choices=sorted(TOOL_INPUTS), help="Check selected tools; default checks all nine")
    selection.add_argument("--diagnose-news", action="store_true", help="Save bounded provider news shapes; does not run MCP readiness")
    selection.add_argument("--scenarios", action="store_true", help="Check all tools plus stocks, ETF, crypto, currencies, weekends and partial exports")
    args = parser.parse_args()
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        receipt = diagnose_news() if args.diagnose_news else asyncio.run(check(list(dict.fromkeys(args.tool or TOOL_INPUTS)), scenarios=args.scenarios))
    except Exception as error:
        receipt = {"status": "FAIL", "source": "real Yahoo Finance via yfinance",
                   "devrev_call": False, "error_type": type(error).__name__, "checks": [],
                   "message": "Provider check failed before completion; verify dependencies and connectivity."}
        if not args.diagnose_news:
            receipt["transport"] = "in-process ASGI MCP HTTP"
    directory = Path(__file__).resolve().parent.parent / "validation_logs"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    prefix = "finance-news-diagnostic-" if args.diagnose_news else "finance-readiness-"
    filename = directory / (prefix + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    with filename.open("x") as output:
        os.chmod(filename, 0o600)
        json.dump(receipt, output, indent=2, allow_nan=False)
        output.write("\n")
    print(receipt["status"] + " — receipt: " + str(filename))
    return 0 if receipt["status"] in {"PASS", "COMPLETE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
