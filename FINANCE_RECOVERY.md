# yFinance Mac recovery — October 11, 2026

The Tesla request now succeeds through DevRev Computer using **yFinance Mac** (`_custom__yfinance-mac`). All nine finance tools were executed successfully after recovery. The existing server PAT remains valid.

## Cause and repair

Cloudflare expired the old Quick Tunnel, first logging `Tunnel not found` at 08:05:05 UTC. The finance server remained running and authenticated local requests still succeeded. Re-entering the PAT could not repair the unavailable hostname.

Only `ai.contextforge.finance-tunnel` was restarted. Its process changed from 55599 to 75067; the finance MCP process remained 66829 and the original ContextForge listener remained 32614. The new endpoint observed during recovery is:

```text
https://sharing-port-assessed-southampton.trycloudflare.com/mcp
```

This is a temporary endpoint. Check `mac_host.py status` for the current URL; another tunnel restart or expiration can require another connector replacement.

Computer showed the existing custom server URL as read-only. A replacement **yFinance Mac** server was therefore created with the new URL and the existing saved finance connection from October 11, 2:02 AM. Its nine read-only tools and two original tools use **Always ask**. After live verification, the expired yFinance binding was removed from the personal agent. Its registered server and saved connection were retained.

## Executed results

| Check | Observed result |
| --- | --- |
| Mac doctor | PASS: token safety, local transport/auth/MCP, Yahoo provider, public transport/auth/MCP |
| Public HTTPS/MCP SDK | All 32 checks PASS, including exact 11-tool inventory, all nine finance tools, market/date scenarios, and eight rejected inputs |
| Computer Ping | `pong - ContextForge MCP tool is reachable` |
| `GetPriceHistory(TSLA, 1mo, 1d, 252)` | `ok`, 22 rows, September 10–October 9, no truncation |
| TSLA September range | `ok`, 21 rows, September 1–30, America/New_York |
| TSLA/AAPL/MSFT September batch | `ok`, 63 rows, 21 per symbol, no truncation |
| September CSV export | `ok`, 63 rows; actual Canvas bytes and SHA-256 match the MCP result |
| TSLA quote, symbol search, profile, quarterly income statement, news | Each `ok`; counts 1 quote, 3 symbols, 1 profile, 1 period/46 metrics, and 2 articles |
| AAPL September 12–14 range | `no_data`, with null data; no fabricated weekend prices |
| BTC-USD September 12–14 range | `ok`, September 12 and 13, UTC |
| AAPL / unknown symbol / MSFT five-day batch | `partial`, ten valid rows; unknown symbol `no_data` |
| February 30, URL as symbol, news limit 11 | Each rejected by validation |
| Two sequential TSLA quotes | Second response `cached=true`, age 3.153 seconds; original retrieval timestamp preserved |
| Existing AAPL month CSV | Repository and original Canvas bytes unchanged |

The income statement correctly reports `truncated=true` for the one requested period and preserves unreported currency and a missing metric as null. The first two quote requests were issued in parallel and both missed the cache; the sequential test established the intended cache behavior.

## Verified files

- [TSLA_daily_prices_1mo.csv](outputs/yfinance-tsla-20261011/TSLA_daily_prices_1mo.csv): the actual Computer-generated file, 22 rows and 11 requested columns. Retrieval timestamp `2026-10-11T13:53:19.197932+00:00`. Every OHLCV value and timestamp matches a separately captured public MCP result.
- [TSLA/AAPL/MSFT September CSV](outputs/yfinance-recovery-20261011/TSLA_AAPL_MSFT_2026-09-01_to_2026-10-01_1d.csv): the exact Computer export, 63 rows, 13 export columns, 14,274 bytes.
- [AAPL/MSFT/NVDA September CSV](outputs/yfinance-recovery-20261011/AAPL_MSFT_NVDA_2026-09-01_to_2026-10-01_1d.csv): the independent public MCP acceptance export, 63 rows.

SHA-256 values:

```text
TSLA_daily_prices_1mo.csv
c2a873fd7b06c125ffb4989542dc637c21bf0141c84982f07e2a49230c9c16ee

TSLA_AAPL_MSFT_2026-09-01_to_2026-10-01_1d.csv
7ebe7826b833b1074e64591929be8b0ef9ae598a6c008141a9684ac0a02342ac
```

## Evidence boundaries

Private, Git-ignored receipts: `finance-tunnel-repair-before-20261011.json`, `finance-refined-https-20261011T134634033120Z.json`, `finance-tsla-https-20261011.json`, and `finance-devrev-recovery-20261011.json`. The final receipt includes source hashes, service continuity, Computer observations, exact artifact checksums, and unchanged AAPL verification. Doctor evidence is under `state/mac-finance/refinement-baseline/doctor-after-repair.json`.

Computer acceptance uses observed tool summaries plus independently verified file bytes and provider values; it is not a full raw DevRev request/response capture. The earlier 69 offline and 23 ASGI tests remain valid for the unchanged implementation. This recovery changed the tunnel and connector binding, not Python source or dependencies. Original ContextForge remote connectivity is a separate unresolved issue.
