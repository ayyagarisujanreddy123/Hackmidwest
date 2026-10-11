# Yahoo Finance MCP refinements

## Objective and authorized scope

Extend the working Mac-hosted yFinance connector so DevRev Computer can retrieve complete bounded history, request exact dates, and export several tickers directly to CSV. The user approved implementation and additional use-case tests on October 11, 2026, and chose to retain the current tunnel URL. Existing authentication, the token, the tunnel, and the original ContextForge process stay in place.

## Contracts and build order

| Module | Responsibility | Depends on |
|---|---|---|
| history | Existing period history plus validated date ranges and exchange trading dates | Yahoo Finance SDK |
| export | Bounded multi-symbol history and deterministic CSV content | history |
| reliability | Small success cache, bounded provider concurrency/deadlines and transient retries | finance tools |
| diagnostics | Read-only local/public authenticated MCP and provider checks | finance tools |

Build order: history → export → reliability → diagnostics → live DevRev verification.

- Preserve existing tool names and period/interval choices. Increase history's default and maximum to 366 rows so a calendar year of daily crypto data also fits. Explicit smaller limits retain newest rows and report truncation.
- Add `get_price_history_range(symbol, start_date, end_date, interval="1d", limit=366)`. Dates are real `YYYY-MM-DD` dates; start is inclusive, end exclusive; the span must be 1–366 days.
- Add `get_price_history_batch` and `export_price_history_csv`. Accept 1–5 strict symbols, normalize case, deduplicate, and use either a supported period or both dates. With neither, use `1mo`. Reject ambiguous or incomplete date selection.
- Return per-symbol results; top-level `partial` means some symbols succeeded. Missing data and provider errors never become invented rows. Report row counts, actual date coverage and truncation.
- CSV uses fixed columns, chronological trading-date/symbol order, blank nulls, provider precision, exchange timezone, retrieval time and source URL. Return UTF-8 `csv` content, a generated filename, MIME type, byte count and SHA-256, without public file hosting or arbitrary Mac filesystem writes. Escape unsafe text cells for spreadsheet consumers.
- Cache only successful bounded results, keep original retrieval timestamps and expose cache age. Retain at most 128 entries. Use a short default TTL and a maximum of two actual provider workers, including after a caller times out. Retry transient transport failures once; do not immediately retry rate limits or bad provider data.
- Add `mac_host.py doctor`: check the private token file, local authentication/initialize/ping/discovery, current public tunnel, and a real Yahoo quote. Report sanitized stage-specific failures and exit nonzero on failure. Do not print credentials or provider exceptions.

## Implementation and commands

Python uses four spaces, descriptive snake_case names and typed MCP inputs/outputs. The implementation stays in `contextforge_mcp_starter/finance.py`, focused export/execution helpers where useful, and `mac_host.py`; tests stay under `tests/`. No new dependency or database is needed.

```python
result = await tools.get_price_history_range(
    "AAPL", start_date="2026-01-01", end_date="2026-04-01"
)
```

Run commands from `contextforge_mcp_starter`:

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_finance*.py' -v
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check
.venv/bin/python check_finance.py
.venv/bin/python check_finance.py --scenarios
.venv/bin/python mac_host.py doctor
```

## Acceptance and checkpoints

- [x] Period and range history preserve values, adjusted-close semantics, exchange dates and missing fields; full-year defaults are complete.
- [x] CSV and batches cover multiple symbols, deduplication, missing symbols, partial failures, no-data windows, quoted text and null values.
- [x] Invalid dates, excessive spans, URLs as symbols, invalid limits and ambiguous selections are rejected through actual MCP HTTP calls.
- [x] Cache timestamps/expiry, transient retries, rate limits, timeouts and concurrent provider limits are proved with controlled fixtures.
- [x] Doctor separates credential, local service, public tunnel and upstream provider problems with no secret exposure.
- [x] Existing authentication, host restrictions and workflow approval tests pass.
- [ ] Real public HTTPS calls cover stocks, an ETF, crypto, a foreign exchange timezone and a holiday/weekend window.
- [ ] DevRev resync discovers the new tools and actual Computer calls exercise range and CSV extraction.
- [x] Sanitized receipts record timestamps, build hashes and observed outcomes; original service and tunnel continuity is checked independently.

The repository already has substantial uncommitted work. Private file snapshots provide rollback checkpoints without staging unrelated changes. Restart only the separate finance process after offline and real-provider checks pass; leave the tunnel process running to retain its hostname.

Checkpoint: 69 offline tests, 23 real-provider ASGI checks, and 32 network checks through the running local Mac service/MCP SDK pass. A verified three-stock September CSV has 63 rows. Finance reload preserved the existing tunnel process, but Cloudflare had independently expired its temporary URL from 08:05:05 UTC. Local authentication, 11-tool discovery, and Yahoo provider checks pass. Public HTTPS and DevRev acceptance remain pending the owner's decision about replacing the expired URL; do not mark them PASS from local evidence.

## Sources

Date and adjustment semantics follow the maintainer's [yfinance history/download documentation](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html). CSV uses [Python's standard CSV API](https://docs.python.org/3.12/library/csv.html). MCP responses follow the [tools specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools).
