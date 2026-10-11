# Yahoo Finance MCP for DevRev Computer

The current priority is a read-only Yahoo Finance connector in DevRev Computer. ContextForge development and AWS deployment are paused; its code and validation history remain available.

**Current Computer connector: yFinance Mac** (`_custom__yfinance-mac`), with 11 discovered tools and Always ask preferences. All nine finance tools passed fresh Computer calls on October 11, 2026. The expired older yFinance binding has been removed from the personal agent. See [the recovery record and verified Tesla CSV](FINANCE_RECOVERY.md).

## Tool contract

| MCP tool | Inputs | Result |
| --- | --- | --- |
| `search_finance_symbols` | Company name or ticker query; limit 1–10 | Matching symbols, names, exchanges, and instrument types |
| `get_stock_quote` | One Yahoo Finance symbol | Latest available market price, currency, previous close, and market timestamp |
| `get_company_profile` | One symbol | Company name, sector, industry, country, website, and summary |
| `get_price_history` | Symbol, period, interval, limit 1–366 (default 366) | Unadjusted OHLCV and separate adjusted close, trading dates/timezone, actual coverage, and truncation |
| `get_financial_statement` | Symbol, statement, frequency, periods 1–4 | Income statement, balance sheet, or cash flow; bounded metrics and reporting periods |
| `get_finance_news` | Symbol; limit 1–10 | Headlines, publishers, publication dates, and article links |
| `get_price_history_range` | Symbol, start/end dates, interval, limit 1–366 | History with inclusive start, exclusive end, and a maximum 366-day span |
| `get_price_history_batch` | 1–5 symbols; period or both dates; interval/limit | Normalized, deduplicated symbols and per-symbol outcomes; successful data remains available when others fail |
| `export_price_history_csv` | Same selection as batch history | UTF-8 CSV content, filename, manifest, row count, coverage, byte count, and SHA-256 |

The original `ping` and `inspect_demo_capability` remain available. `finance_server.py` runs an isolated **Yahoo Finance Mac** server on `127.0.0.1:8003/mcp`, with workflow generation disabled. The existing ContextForge server on port 8000 and its connector configuration are preserved. Combined finance registration in `server.py` is still opt-in through `CONTEXTFORGE_ENABLE_FINANCE=1`.

## Data and error handling

Tool results contain `status`, `data`, `provider`, `retrieved_at`, and `source_refs`, plus cache and retry metadata. Provider data is read-only and treated as untrusted input. Empty data, upstream errors, and rate limits are explicit statuses; the connector supplies no invented fallback records. `partial` means some batch/export tickers succeeded; inspect `data.results` for each outcome. Retrieval time is separate from the provider's market timestamp. Quotes are the latest available provider values, with no real-time guarantee.

Symbols are bounded identifiers such as `AAPL`, `MSFT`, `BTC-USD`, or `^GSPC`. Callers cannot choose a source URL or execute code. History accepts periods `5d`, `1mo`, `3mo`, `6mo`, or `1y`, with intervals `1d`, `1wk`, or `1mo`. Financial statements accept `income`, `balance_sheet`, or `cash_flow` and `yearly` or `quarterly` frequency. No trading operations are exposed.

Range dates must be real `YYYY-MM-DD` dates. The end is exclusive: September 2026 is `start_date="2026-09-01", end_date="2026-10-01"`. Batches and exports accept either a period or both dates; omit both to use `1mo`. Smaller row limits retain the newest rows and set `truncated=true`. Daily crypto history can exceed the stock market's roughly 252 annual sessions, so the default allows 366 rows. Weekends with no stock trading return `no_data` without fabricated prices. UTC `time` and exchange-local `trading_date` are separate fields.

CSV has 13 fixed columns: `symbol,trading_date,time,open,high,low,close,adjusted_close,volume,currency,exchange_timezone,retrieved_at,source_url`. Rows sort by trading date, symbol, and time. Nulls are blank, provider float precision is preserved, and unsafe text cells are escaped for spreadsheet use. Content is bounded to 512 KiB. The tool returns `data.csv`; it does not write arbitrary Mac files or host public downloads. Ask Computer to save that content verbatim in Canvas and verify the reported SHA-256. An entirely unsuccessful request has no CSV; a partial export identifies omitted symbols in its manifest.

Successful results are cached for 30 seconds, with at most 128 entries. Cache hits preserve their original `retrieved_at` and expose `cached`/`cache_age_seconds`; batch/export manifests contain this metadata per symbol. Requests have a 30-second deadline and at most two actual provider workers, including after a caller times out. Transient transport errors get one retry. Rate limits have a 60-second advisory retry delay and are not immediately retried or cached.

## Setup

From the backend directory:

```zsh
cd /Applications/Projects/Hackmidwest/contextforge_mcp_starter
.venv/bin/python -m pip install -r requirements-finance.txt
.venv/bin/python -m pip check
```

Keep the working ContextForge server and its tunnel running. Do not restart it or change its DevRev connector during finance readiness checks. Finance tools need neither AWS credentials nor the synthetic API.

Run the real provider check in a normal Terminal:

```zsh
.venv/bin/python check_finance.py
.venv/bin/python check_finance.py --scenarios
```

The default exercises bearer authentication, MCP discovery, and all nine finance tools against Yahoo Finance using an in-process ASGI transport. `--scenarios` adds stocks, ETF weekly history, full-year crypto, Tokyo trading dates, a currency pair, stock/crypto weekends, partial batches/exports, and a cache hit. It opens no listening port and changes no running service. A temporary token stays in memory. The private, Git-ignored receipt is saved under `../validation_logs/finance-readiness-*.json`; the command exits unsuccessfully if any check fails. `--tool get_stock_quote` checks only that tool and cannot establish complete readiness.

## Host on your Mac and connect DevRev

After a complete provider readiness PASS, start the Mac services:

```zsh
cd /Applications/Projects/Hackmidwest/contextforge_mcp_starter
.venv/bin/python mac_host.py start
.venv/bin/python mac_host.py status
.venv/bin/python mac_host.py doctor
```

This installs two per-user LaunchAgents: `ai.contextforge.finance-mcp` and `ai.contextforge.finance-tunnel`. They run in the background, restart after crashes, and start at login. The server listens only on loopback; a separate Cloudflare HTTPS tunnel forwards requests with the exact allowed Host header. No router port forwarding is needed. The finance bearer secret is generated once in `state/mac-finance/mcp.token` with mode 600; it is neither printed nor embedded in the service plists. Logs are private under `state/mac-finance/`.

`doctor` separately checks token-file safety, local transport/authentication/initialize/discovery/ping, a real Yahoo AAPL quote, and public transport/authentication/MCP. It exits nonzero when any stage fails and never prints the token or raw provider exceptions. `status` returns `public_endpoint=null` and `tunnel_status="expired"` when the latest Quick Tunnel has been lost, even if its process is still running. A public-transport failure is distinct from a token rejection.

After validated finance code changes, reload only its MCP process:

```zsh
.venv/bin/python mac_host.py reload
# Allow the local process to finish startup before probing.
.venv/bin/python mac_host.py doctor
```

`reload` preserves the tunnel process and hostname; it does not repair an expired tunnel. No token rotation or fresh PAT entry is needed for tool additions. Resync the current yFinance Mac connector with its saved finance connection after checking public HTTPS.

Use the **current** `public_endpoint` printed by `status`, including `/mcp`, in **Settings → My Computer → Connectors → Add custom connector**:

| Field | Value |
| --- | --- |
| Server name | yFinance Mac |
| Server URL | The current HTTPS `public_endpoint` from `mac_host.py status` |
| Server slug | `yfinance-mac` |
| Service | Personal access token (PAT) |
| Connection | Your existing saved finance PAT connection, or a new private connection on first setup |

If no saved finance connection exists, copy the server token privately, then paste it only into the connector's PAT field, without a `Bearer` prefix:

```zsh
.venv/bin/python mac_host.py copy-token
```

Finish **Next → Set up** and verify the actual discovered tools. Clear the clipboard afterward with `pbcopy < /dev/null`. The token is this server's secret, not a DevRev account PAT. Do not reuse the original ContextForge token or replace its connector.

If connecting still reports a sync failure after entering the correct token, open the server's **View details → menu → Resync tools**. Select the saved finance-token connection there and click **Next**. Server discovery has its own saved-connection binding; entering a new personal PAT does not replace an older connection selected for resync. After resync completes, finish the personal **Connect** flow.

Keep the Mac awake and connected to the internet while using the connector. User agents stop at logout; they start again at login. A Quick Tunnel hostname changes when its process restarts, including after reboot. In the observed Computer UI, an existing custom server's URL is read-only: a changed hostname requires a replacement custom connector using the same saved finance connection. Verify its tools and permission preferences before removing the expired binding from the agent. Quick Tunnels have no uptime guarantee and do not support SSE; this server uses stateless Streamable HTTP with JSON responses. A stable URL requires a named tunnel and a domain you control. See [Cloudflare's documented limitations](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/) and [Apple's LaunchAgent lifecycle](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html).

If `status` reports `tunnel_status="expired"`, retries and PAT re-entry cannot restore that hostname. Restart only the finance tunnel, then inspect the new endpoint and require a complete doctor PASS:

```zsh
launchctl kickstart -k "gui/$(id -u)/ai.contextforge.finance-tunnel"
.venv/bin/python mac_host.py status
.venv/bin/python mac_host.py doctor
```

This changes the temporary finance hostname. Use the current endpoint in a replacement custom connector, reuse the saved finance PAT, and verify a live Ping before extraction. Select **Always ask** for both tool groups to retain the current preferences. After successful verification, use **Remove from agent** on the expired connector; its registered server and saved connection can remain. The October 11 repair required no token rotation or finance-server restart.

To stop only these finance services and disable their login launch:

```zsh
.venv/bin/python mac_host.py stop
```

`start` enables them again and preserves the token. Calling `start` on loaded services leaves their processes and current tunnel intact.

## DevRev acceptance checks

1. Inspect a complete real-provider receipt: authentication and discovery must pass, and each of the nine finance tools must return usable data and source references. An offline fixture test does not meet this gate.
2. Start the isolated finance-only process and HTTPS tunnel with `mac_host.py start`. Leave ContextForge on port 8000, its source, approval ledger, and current tunnel untouched.
3. Add **yFinance Mac** with the saved finance connection or a private first-time connection in Computer as described above.
4. In a fresh Computer session, verify 11 discovered tools (nine finance tools plus the two original tools). Call search, quote, profile, period/range history, batch history, statement, news, and CSV export. Include partial missing-symbol results and stock/crypto weekend windows. Save the CSV verbatim in Canvas and verify its checksum, row count, dates, and symbols. Record actual responses, provider timestamps, source references, and errors.
5. Confirm an invalid symbol URL and out-of-range limit are rejected. Recheck the existing ContextForge connector independently. Stop only the new finance process/tunnel if testing fails.

Only executed DevRev calls establish Computer integration. A successful ASGI readiness receipt alone does not.

## Demo

Ask Computer to call `get_stock_quote` for AAPL, retrieve its last month's daily price history, and show three recent news headlines with source links. The response must reflect actual tool results, including an upstream failure if Yahoo Finance is unavailable.

For extraction, ask: **“Use yFinance Mac to export daily AAPL, MSFT, and NVDA prices from September 1, 2026 through September 30, 2026. Call ExportPriceHistoryCsv with start_date 2026-09-01 and end_date 2026-10-01, save data.csv verbatim in Canvas, and report the per-symbol status, row count, date coverage, truncation, and SHA-256.”**

## Refinement validation — October 11, 2026

- **PASS:** all 69 executed offline tests, including real MCP HTTP validation, CSV precision/nulls/formula protection, exchange dates, range bounds, cache expiry, transient retries, rate limits, and bounded workers after timeouts.
- **PASS:** 23 authenticated in-process readiness checks across all nine tools and ten additional real-provider scenarios. Receipt: `finance-readiness-20261011T095943300761Z.json`.
- **PASS:** 32 network checks through the running Mac service and MCP Python SDK, including all nine tools, market/date scenarios, and eight rejected inputs. The September AAPL/MSFT/NVDA CSV contains 63 rows, with byte count and SHA-256 verified. Receipt: `finance-refined-loopback-20261011T102738278509Z.json`.
- **PASS:** finance-only reload preserved the tunnel process and original ContextForge process. The running local server accepts the existing secret, exposes 11 tools, and returns an AAPL quote. Receipt: `state/mac-finance/refinement-baseline/doctor-live-after-startup.json`.
- **Resolved transport failure:** Cloudflare's log first reported `Tunnel not found` at 08:05:05 UTC, before the 10:00:47 UTC finance reload. After the reported Tesla failure, only the finance tunnel was replaced. The existing PAT works; the finance MCP process and original ContextForge process were unchanged.
- **PASS:** all eight doctor stages and 32 real public HTTPS/MCP SDK checks, including authentication, exact 11-tool discovery, all nine finance tools, provider scenarios, and eight rejected inputs. Receipt: `finance-refined-https-20261011T134634033120Z.json`.
- **DevRev live acceptance PASS:** replacement **yFinance Mac** reuses the saved finance connection and has 11 tools with Always ask preferences. Ping and all nine finance tools returned actual results. The exact Tesla month request produced 22 rows; September TSLA/AAPL/MSFT export produced 63 rows and its saved Canvas bytes matched the MCP SHA-256. Weekend, partial-symbol, invalid-input, and sequential cache tests passed. The old binding was removed from the personal agent. Receipt: `finance-devrev-recovery-20261011.json`.

See [the refinement contract](FINANCE_REFINEMENTS.md), [the recovery record](FINANCE_RECOVERY.md), and [VALIDATION.md](VALIDATION.md) for scope and receipts.

## Initial validation — October 11, 2026, before refinements

- **PASS:** 33 executed offline tests cover the six tools, MCP HTTP calls, input bounds, explicit provider failures, workflow coexistence, isolated port/Host validation, flat and nested news records, and private token-file restrictions. Test provider values are invented fixtures.
- **PASS:** installed `yfinance==1.7.0`, MCP 1.30.0, and Strands 1.59.0; `pip check` reports no dependency conflicts.
- **Root cause verified:** live Ticker news returned zero records; Search news returned two flat records. News now uses the documented Search GET API and preserves publication timestamps and source URLs. Earlier DNS and empty-news failures remain historical evidence in `VALIDATION.md`.
- **PASS:** all six tools returned real provider data through authenticated in-process MCP; receipts `finance-readiness-20261011T061655574467Z.json` and `finance-readiness-20261011T062239123456Z.json`. The first six response hashes were verified; the second records the current build hashes and explicitly identifies a complete six-tool check.
- **PASS:** the running Mac server passed 13 real HTTPS/MCP SDK checks: missing/incorrect token rejection, initialize, discovery, ping, all six finance tools, and two rejected inputs. Receipt: `finance-mac-https-20261011T062132784881Z.json`.
- **PASS:** both finance LaunchAgents are running; repeated `start` preserves their processes. The original ContextForge server still returns a local MCP ping. Its separate final Computer connector ping failed with `TypeError: fetch failed`; its server, tunnel, and connector configuration were not changed.
- **DevRev resync PASS:** earlier retries returned HTTP 401 despite correct Bearer formatting. The resync dialog still selected the old October 10 connection. Selecting the saved October 11, 2:02 AM finance connection fixed discovery: real DevRev requests at 07:06:57 UTC matched the server secret and returned HTTP 200/202, including tool-list requests. The owner clarified that Terminal had no error; the failure occurred in Computer. No authentication requirement was relaxed. Receipt: `finance-devrev-resync-20261011T070657Z.json`.
- **DevRev live acceptance PASS:** Computer shows **yFinance connected!** and eight discovered tools. A fresh session executed ping and all six AAPL finance calls at 07:11:25–30 UTC; each returned usable results with retrieval times and source references. An invalid symbol URL and news limit 11 reached the server and were rejected by argument validation at 07:12:40–41 UTC. Receipt: `finance-devrev-live-20261011T071130Z.json`.
- **Cleanup PASS:** temporary metadata-only diagnostics were removed. Authenticated HTTPS initialize, exact tool discovery, ping, missing/incorrect-token rejection, and all 33 offline tests still pass. A final live Computer finance ping also passed. The generated secret is absent from publication candidates. Receipt: `finance-mac-final-20261011.json`.

Full results are recorded in [VALIDATION.md](VALIDATION.md). Run the offline suite from the backend directory with `.venv/bin/python -m unittest discover -s tests -v`.

## Provider references

The implementation uses the maintainer's [Ticker API](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html) and [Search API](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Search.html). The [yfinance project](https://github.com/ranaroussi/yfinance) describes the library as a research and educational tool and points to Yahoo's terms governing downloaded data. This connector is a research demo; data redistribution rights require separate review before a public product launch.
