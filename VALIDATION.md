# ContextForge — Validation & Go/No-Go Criteria

**Active work:** read-only Yahoo Finance MCP for DevRev Computer; further ContextForge product work and AWS deployment are paused. Existing workflow, authentication, approval controls, and running services are preserved. Finance evidence is recorded separately below.

**Purpose:** Record evidence that the system *actually works*. Do not mark a case PASS until it has been run in the team's environment.\
**Current state (October 10 local time; latest evidence October 11 UTC):** Synthetic connector generation, ten live validation checks, explicit human approval, source-backed DevRev execution, and **second-user reuse (D6) PASS**. The minimal demo passes native Chrome checks and two technical rehearsals in 74 and 70 seconds, with recorded generation clearly labeled and fresh live execution. A live Strands reuse decision omitted the capability ID and failed safely; its fix passes 31 local regressions but awaits a live rerun. AWS read-only preflight confirms an active Free Plan with $120 credits, eligible resources, Ohio prices, and DryRun launch permission. Deployment preparation passes 47 local checks; provisioning approval and actual hosted execution remain pending. Original approval is unchanged. Enterprise-Bench access remains unavailable. All business records are synthetic; teammate identity is user-attested. Follow [MVP_WORKFLOW.md](MVP_WORKFLOW.md).

## 1. Validation definitions

- **PASS:** Real operation executed; observed output matches an explicit expected result. Save a sanitized screenshot, log or receipt.
- **FAIL:** Real operation executed; output contradicted expectation or could not complete. Record error and fix owner.
- **BLOCKED:** Prerequisite, permission, source data or service unavailable; do not call it PASS.
- **NOT TESTED:** No execution evidence yet; do not infer success from screenshots or code existence.
- **CONDITIONAL PASS:** Allowed only for a clearly scoped limitation, written next to the result; not a substitute for the primary integration test.

Record results with UTC or local timezone, deployed build/version, hostname, test input reference, expected, observed, and tester. **Never record actual PATs, bearer secrets or customer data.**

### Yahoo Finance MCP — October 11, 2026 UTC

Scope: six explicitly requested read-only Yahoo Finance tools. Testing uses the existing Python environment, MCP 1.30.0, Strands 1.59.0, and `yfinance==1.7.0`. No working MCP process, tunnel, DevRev connection, AWS resource, or approval record was changed. Finance is disabled unless explicitly enabled or injected into an isolated test app.

| Executed check | Actual result |
| --- | --- |
| Dependency imports/version inspection and `.venv/bin/python -m pip check` | PASS: pinned finance SDK is installed; no broken requirements; MCP and Strands versions retained |
| `.venv/bin/python -m unittest discover -s tests -v` | PASS: all 25 tests executed successfully; provider test values are labeled fixtures, not live quotes |
| All six tools via MCP HTTP/ASGI | PASS with fixture provider: exact discovery, structured results, bounded inputs, and successful calls |
| Authentication and preserved baseline | PASS: missing/wrong bearer gets HTTP 401; missing token refuses startup; original Ping response and finance-disabled inventory retained |
| SDK history/statement conversion | PASS using actual pandas frames with invented values: dated records, latest rows, truncation, missing values as null, invalid dates rejected |
| ContextForge coexistence/approval boundary | PASS in a temporary registry: ten source validations succeed, generated connector remains inactive, MCP execution returns `approval_required`, finance works, and no approval event is created |
| Quote regression detection | PASS: invert the usable-price condition in an in-memory copy; all three relevant tests fail as expected; source file remains unchanged |
| Real AAPL quote in this restricted session | FAIL: provider reported `DNSError`; MCP returned `upstream_error`, `data=null`, and no invented price. Authenticated initialization, discovery, and two 401 checks in the same receipt PASS |
| Owner's normal-Terminal six-tool run, receipt inspected directly | FAIL overall: five tools return real provider data, news returns `no_data`; all six response hashes match; authentication and discovery PASS |
| Yahoo Finance through DevRev Computer | NOT TESTED: working MCP has not been restarted, and no finance connector was changed or created |

The earlier receipt is `validation_logs/finance-readiness-20261011T043327024696Z.json` (FAIL; one quote tool attempted at `2026-10-11T04:33:26.643991+00:00`). The new receipt appeared during inspection: `validation_logs/finance-readiness-20261011T044328614323Z.json`, checked at `2026-10-11T04:43:26.327262+00:00`. It exercises all six tools and records the following real-provider results:

| Tool | Actual returned evidence | Result |
| --- | --- | --- |
| `search_finance_symbols` | Three matching instruments, including AAPL / Apple Inc.; lookup reference | PASS |
| `get_stock_quote` | Finite AAPL price, USD currency, previous close, exchange, and separate October 9 market timestamp; quote reference | PASS |
| `get_company_profile` | Apple Inc. profile, sector/industry/country, website, and provider summary; quote reference | PASS |
| `get_price_history` | Five dated daily OHLCV records, October 5–9, with adjusted close, USD currency, and `auto_adjust=false`; quote reference | PASS |
| `get_financial_statement` | 33 metrics for the quarterly income statement ending June 30, 2026; explicit truncation and unknown currency retained as null; quote reference | PASS |
| `get_finance_news` | `status=no_data`, `data=null`; no article returned | FAIL |

Missing/wrong-token checks returned 401, authenticated initialization passed, and all eight expected MCP tools were discovered. Every saved tool response matches its recorded SHA-256. Neither receipt is a successful six-tool run. The readiness command uses real Yahoo Finance with in-process MCP, not the live DevRev transport.

**News diagnosis gate:** the current adapter expects nested `content.title`. Installed yfinance 1.7.0's Ticker implementation reads a ticker stream and removes advertisements; the maintainer also documents news through Search. The receipt alone does not show whether the upstream stream was empty, contained only ads, or used a different response shape. Do not guess the root cause. Added `check_finance.py --diagnose-news` to compare bounded Ticker requests (2 and 10 snippets) with Search news (2 results), saving only counts/types/field names to a separate private receipt. Syntax and nested/flat fixture-shape checks PASS; live diagnosis is pending normal-Terminal execution. `COMPLETE` is diagnostic completion, not a tool-readiness PASS. No endpoint or DevRev connector change is authorized by a failed readiness run.

Implementation: `contextforge_mcp_starter/finance.py`, opt-in registration in `server.py`, separate dependency file, and `check_finance.py`. Tests are in `contextforge_mcp_starter/tests/test_finance*.py`. See [FINANCE_MCP.md](FINANCE_MCP.md) for tool contracts and the controlled DevRev gate. After a complete real-provider receipt is inspected successfully, prepare a separate finance endpoint and owner-only Computer connector; preserve the existing integration throughout.

Development failures retained: initial missing-module/factory tests failed before implementation; an ASGI test lifespan crossed async task boundaries and was corrected in the harness; a misplaced date helper broke valid news URLs and was caught/corrected; the coexistence harness initially imported the synthetic factory incorrectly and was corrected. No failed assertion was removed or test skipped to obtain the final 25-test PASS.

### AWS deployment preparation — October 11, 2026, 03:58 UTC

- **Requested approach:** existing MCP/synthetic API/Strands on EC2 with a temporary Cloudflare HTTPS tunnel. Owner explicitly requires approval before billable provisioning and preservation of the current DevRev connection.
- **Read-only AWS preflight PASS:** authenticated CloudShell; no active/stopped Ohio instances or instance profiles; `t3.small` has 2 GiB RAM and Free Tier eligibility; Canonical Ubuntu 24.04 image `ami-09519cc56eb20524a` is eligible; default VPC/subnets and the Ohio EC2 Instance Connect prefix list exist. Nova Micro's US profile is ACTIVE, with foundation models in `us-east-1`, `us-east-2`, and `us-west-2`.
- **Account/cost checks PASS:** Free Tier API returned plan `FREE`, status `ACTIVE`, remaining credits `$120`, expiration April 10, 2027. AWS Price List returned Ohio Linux t3.small `$0.0208/hour`, gp3 `$0.08/GiB-month`, and Nova Micro on-demand input/output `$0.000035/$0.00014` per 1,000 tokens. Public IPv4 adds `$0.005/hour` per [AWS pricing](https://aws.amazon.com/vpc/pricing/). VM + 8 GiB disk + IPv4 is approximately `$0.64/24h`, excluding inference/transfer.
- **Launch permission DryRun PASS:** `run_instances(DryRun=True, ...)` returned `DryRunOperation: Request would have succeeded, but DryRun flag is set.` This created no instance and does not establish capacity, IAM role creation/attachment, or application readiness.
- **Earlier environment failures retained:** local boto3 could not reach `https://us-east-2.signin.aws.amazon.com/v1/token` (`EndpointConnectionError`). Native terminal typing corrupted Python indentation; that attempt returned `IndentationError` before making AWS calls. Authenticated CloudShell execution with intact source resolved the read-only checks; no permissions were changed.
- **47 local deployment checks PASS:** private explicit-allowlist bundle; identical complete approval/manifest snapshot; checksummed extraction; refusal of existing targets, traversal, symlinks, duplicate members, and tampered files; packaged Python syntax; exact old capability ID/source fingerprint; ten source checks against the real synthetic ASGI app; inactive execution with no source request/approval event; migration command executes the existing validator and cannot activate; authenticated MCP initialize/discovery/original tools; missing/wrong-token 401; MCP rejects the inactive candidate; scoped role/tunnel/startup configuration; working runtime, root `AGENTS.md`, registry status, and approval ledger unchanged. ASGI checks are not remote TCP or AWS tests.
- **Verification-harness failure retained:** initial inspection assertion expected `structuredContent` and raised `KeyError`; the response contained valid JSON text. Corrected only the harness to handle both MCP representations; the repeated checks PASS. Receipt records this failure and correction.
- **Shell syntax PASS:** `bash -n deploy/install_ec2.sh`. Linux installation, systemd validation/startup, actual instance-role inference, HTTPS tunnel, hosted RunCapability, fresh administrator approval, and hosted persistence are **NOT TESTED**.
- **Approval state:** existing `get_ticket_engineering_issues_76f8fc748bff` remains approved only in the working Mac registry. All original approval events are preserved unchanged in a private archival snapshot. New-host candidates require real validation and explicit human approval; no UID substitution or automatic activation.
- **Next gate:** owner approval of the concrete [resource/role/cost/shutdown proposal](deploy/README.md), then isolated deployment and executed hosted gates. No billable infrastructure, runtime role, account upgrade, endpoint migration, or new public URL exists yet.
- **Private evidence:** `validation_logs/aws-deployment-preparation-20261011T035847570934Z.json` and `validation_logs/aws-ec2-preflight-20261011T040135580876Z.json` (14 AWS checks). The final 29-file private bundle is `/private/tmp/contextforge-ec2-demo.tar.gz`, mode 600, 37,951 bytes, SHA-256 `aad49346a52466079c06057acb6a2a72fddef31067532a7aa986d56f2630c0a4`. Final member-hash, whitespace, heuristic credential-pattern, and unchanged-runtime/AGENTS checks PASS. No secrets in receipts; private migration archives must stay out of Git.

## 2. Run log template

Copy this section when executing tests:

```markdown
### Run YYYY-MM-DD HH:MM [timezone]
- Tester / team role:
- Build or commit identifier:
- Endpoint (hostname only; no token or private path if sensitive):
- Test IDs run:
- Expected:
- Observed response / source ID:
- Status: PASS / FAIL / BLOCKED / NOT TESTED
- Error and remediation:
- Sanitized evidence location:
```

### Run 2026-10-10 21:31 UTC — Environment preflight

- Tester / team role: Codex / backend preflight.
- Build or commit identifier: planning-only workspace; no Git repository or server build present.
- Endpoint: none started or exposed.
- Test IDs run: environment prerequisites only; A1–A9 are blocked, not executed. No integration PASS/FAIL result is available.
- Expected: readable starter archive, Python compatible with `mcp==1.30.0`, and dependency-download access.
- Observed:
  - Workspace inventory contains `AGENTS.md`, `PROJECT_PLAN.md`, `TODO.md`, and `VALIDATION.md`; no starter ZIP or extracted server.
  - Filename searches found no starter in readable project/Desktop paths. Downloads and Documents returned `Operation not permitted (os error 1)`; their contents could not be inspected.
  - `python3 --version` returned `Python 3.9.6`; executable: `/Library/Developer/CommandLineTools/usr/bin/python3`. Import lookup found no installed `mcp` package; no newer Python executable was located in the checked standard installation paths.
  - `curl --head --silent --show-error --connect-timeout 5 --max-time 10 https://pypi.org/simple/mcp/` returned exit code 6: `Could not resolve host: pypi.org`.
  - Official [mcp 1.30.0 package metadata](https://pypi.org/project/mcp/1.30.0/) requires Python >=3.10. This is a metadata check, not a successful installation.
- Status: **BLOCKED**.
- Error and remediation: provide the starter in the workspace or a readable local path; provide a Python >=3.10 environment and dependency access. Inspect the actual archive before running its code. Keep the DevRev connectivity gate ahead of connector/Strands development.
- Sanitized evidence location: command outputs captured above; no credentials or enterprise records accessed.

### Run 2026-10-10 21:36 UTC — Extracted starter inspected; runtime blocked

- Tester / team role: Codex / backend preflight.
- Build identifier: `contextforge_mcp_starter/server.py` SHA-256 `0d9351dd2fcee40cb8239026f3c90cccaac06986bbf93511ba19ee4487a461ae`; original server source unchanged.
- Endpoint: `127.0.0.1:8000`; no server or public tunnel running.
- Test IDs run: local A3 transport probe attempted; A1/A2/A4/A5 blocked by prerequisites. No DevRev or Strands test executed.
- Expected: MCP initialize response, followed by SDK discovery and both data-free tool calls.
- Observed:
  - User supplied `contextforge_mcp_starter/` rather than the ZIP. Inspected `server.py`, `requirements.txt`, and `README.md`; the archive itself remains unavailable but is unnecessary for this extracted-source validation.
  - Source defines exactly `ping` and `inspect_demo_capability`, binds `127.0.0.1:8000`, uses JSON/stateless Streamable HTTP, and permits only the two documented local Host values. It contains no business data or credentials. This code review is not runtime validation.
  - An initialize POST to `http://127.0.0.1:8000/mcp` returned curl exit code 7: `Failed to connect to 127.0.0.1 port 8000`; server startup is still blocked.
  - Added `connectivity_smoke.py` using the [official pinned SDK client example](https://github.com/modelcontextprotocol/python-sdk/blob/v1.30.0/examples/snippets/clients/streamable_basic.py). Syntax parsing succeeded for the server and client; this does not prove imports or tool execution.
  - Executed `python3 contextforge_mcp_starter/connectivity_smoke.py`: exited 1 with **BLOCKED**, Python `3.9.6`, and an empty test-results object. Message: `Python >=3.10 is required; no MCP tests executed`.
- Status: **BLOCKED** — starter-file prerequisite resolved; compatible runtime and dependency access still required.
- Remediation requested: create the starter `.venv` with Python >=3.10 and install its pinned requirements in the user's normal Terminal, or provide an existing compatible environment path. Then start the unchanged server and rerun the smoke client before exposing the data-free endpoint to DevRev.
- Sanitized evidence: `validation_logs/connectivity-20261010T213603273614Z.json`.

### Run 2026-10-10 21:38 UTC — Dependencies verified; sandbox server launch failed

- Tester / team role: User installed runtime/dependencies; Codex verified and attempted server launch.
- Build identifier: unchanged starter server, SHA-256 recorded in the previous run.
- Endpoint: `127.0.0.1:8000`; sandbox process shut down after failed bind.
- Test IDs run: A1 dependency verification, A2 server launch. A3–A9 still await a running server.
- Expected: compatible Python, pinned SDK with working imports, clean dependency consistency, and a running port-8000 server.
- Observed:
  - `.venv/bin/python --version`: `Python 3.12.15`.
  - Installed MCP metadata: `1.30.0`; `ClientSession` transport, `FastMCP`, and `TransportSecuritySettings` imports resolved.
  - `.venv/bin/python -m pip check`: `No broken requirements found` (pip cache unavailable in this sandbox; consistency check completed).
  - `PYTHONUNBUFFERED=1 .venv/bin/python server.py`: application startup completed, then bind returned `[Errno 1] operation not permitted`; process exited 3.
- Status: **A1 PASS** (user installation confirmed by executed checks); **A2 FAIL in this sandbox**. Integration remains **BLOCKED** until the user starts the same server in normal Terminal.
- Remediation: run `.venv/bin/python server.py` in the starter folder outside this session and keep it open; then execute the smoke client against that live process. No source change is justified by the sandbox bind error.
- Sanitized evidence: `validation_logs/server-launch-sandbox-blocked.txt` and dependency-check output above.

### Run 2026-10-10 21:41 UTC — Live listener observed; session cannot reach it

- Tester / team role: User started the server in normal Terminal; Codex inspected the listener and executed HTTP/SDK probes.
- Build identifier: unchanged starter; `.venv` Python 3.12.15, MCP 1.30.0.
- Endpoint: `127.0.0.1:8000`; `lsof` observed Python PID 20331 in LISTEN state.
- Test IDs run: A2 listener check, A3 initialize attempts. A4/A5 could not execute because initialization did not complete.
- Expected: valid initialize response and real SDK tool results from the active server.
- Observed:
  - `lsof -nP -iTCP:8000 -sTCP:LISTEN` showed the Python process bound to `127.0.0.1:8000`.
  - The session's curl initialize request exited 7 without reaching the listener.
  - `.venv/bin/python connectivity_smoke.py` exited 1 with FAIL and no completed MCP tests. Initially the SDK wrapped its error in an ExceptionGroup; the client was updated to preserve leaf errors.
  - A rerun after that diagnostic change recorded `ConnectError: All connection attempts failed`. This is a failed session transport attempt, not evidence that either tool is faulty.
- Status: **A2 PASS** for the user's normal-Terminal server; session transport **FAIL**, integration verification **BLOCKED** until the client runs outside this restricted session.
- Remediation: keep the server open; run `.venv/bin/python connectivity_smoke.py` in a second normal Terminal. Inspect its saved receipt before marking A3/A4/A5 PASS.
- Sanitized evidence: `validation_logs/connectivity-20261010T214132428397Z.json` and `validation_logs/connectivity-20261010T214152140689Z.json`; listener output summarized above.

### Run 2026-10-10 21:46 UTC — Original local MCP baseline

- Tester: user executed the smoke client in normal Terminal; Codex inspected its saved receipt.
- Build: original data-free starter; Python 3.12.15, MCP 1.30.0, before authentication changes.
- Endpoint: `127.0.0.1:8000/mcp`.
- Expected: initialization, exactly two tools, exact `ping` response, and the demo-capability fields.
- Observed: protocol `2025-11-25`; tools `inspect_demo_capability` and `ping`; `pong - ContextForge MCP tool is reachable`; capability `connectivity-test`, status `working`, sample_records `0`.
- Status: **A3/A4/A5 and local inspection PASS**. This does not establish authenticated or DevRev connectivity.
- Evidence: `validation_logs/connectivity-20261010T214608488058Z.json`.

### Run 2026-10-10 22:07 UTC — Live authentication attempt

- Tester: normal-Terminal smoke-client receipt inspected by Codex; live server build identifier not captured.
- Endpoint: `127.0.0.1:8000/mcp`; Python 3.12.15, MCP 1.30.0.
- Expected: six unauthorized rejection checks, followed by authenticated protocol and tool success.
- Observed: missing and incorrect tokens returned HTTP 401 on GET, POST, and DELETE. The authenticated request could not be sent: `LocalProtocolError` rejected multiline text configured as the client token. No authenticated MCP/tool check completed.
- Status: **six rejection checks PASS; overall run FAIL**.
- Remediation: restart with a single-line secret, set the identical value in the client's Terminal, and rerun. Enter the value privately; do not paste commands into the token prompt.
- Evidence: `validation_logs/connectivity-20261010T220732466885Z.json`. Header contents were removed from its exception diagnostic; the original status and six observed results remain intact. Client reporting now omits arbitrary library exception text.

### Run 2026-10-10 22:10 UTC — Bearer authentication and streaming tests

- Tester: Codex; executed with the installed Python 3.12.15 and MCP 1.30.0.
- Build: `server.py` SHA-256 `03f3d4482b59eceac698e3eeb62d6c136cd083f365a8d1b561f393650526bb99`.
- Scope: in-process HTTPX ASGI transport with the real MCP SDK and session-manager lifespan; no live socket or DevRev request.
- Commands: `.venv/bin/python -m py_compile server.py connectivity_smoke.py test_server.py`; `.venv/bin/python -m unittest -v test_server`.
- Observed: both commands exited 0; **nine tests PASS**. Missing/empty/non-header-safe environment tokens prevent startup; 30 missing/incorrect/malformed-header cases return 401; authenticated initialization, discovery, and both tools succeed. The smoke client completes six rejection checks plus four MCP checks. Authorized stream frames and lifespan events pass unchanged; raw and escaped credentials are omitted from error reports.
- Earlier regression tests failed as expected before the fixes; an intermediate test used an impossible NUL environment value and was corrected to a supported control-character input. Final suite: `Ran 9 tests in 0.269s`, `OK`.
- Status: **syntax and in-process authentication PASS**. Authenticated live verification remains pending after restart; B9 and A8/A9 are not passed.
- Evidence: `validation_logs/auth-asgi-20261010T221001Z.txt`; executable checks in `contextforge_mcp_starter/test_server.py`.

### User-reported result — Existing DevRev connection, October 10

- Tester: user; exact invocation times, hostname, and screenshot were not supplied.
- Observed per user's explicit status report: bearer-authenticated MCP is connected through Cloudflare Tunnel; Computer invokes both `Ping` and `InspectDemoCapability` and receives their expected responses.
- Status: **A6–A9 PASS (user-reported execution)**. This was not independently rerun by Codex during the planning turn. Public unauthorized rejection and new dispatcher tools still need separate execution evidence.
- Preserve the active server/tunnel and connector; no endpoint change was made.

### Run October 10 — Dependency and local prototype regression checks

- Tester: Codex; local Python 3.12.15, MCP 1.30.0, Strands 1.59.0.
- Commands: `.venv/bin/python -m pip check`; `.venv/bin/python -m unittest -v test_server test_connectors test_workflow_mcp test_strands_workflow`.
- Observed: no broken requirements; **22 checks PASS**. Authenticated protocol and unchanged baseline tools work with the new dependencies. Restricted synthetic REST calls, changed inputs, invalid mappings, approval persistence, disablement, and optional MCP tools were exercised through real in-process HTTP/SDK operations.
- The three agent-orchestration checks use scripted agents. They do not prove live Bedrock gap detection, generation, or repair.
- Status: **local prototype PASS**, scoped to that pre-cleanup build and synthetic fixtures.
- Evidence: `validation_logs/workflow-local-before-cleanup-20261010.txt`, including command output and source hashes. Standalone scripts and fixtures were subsequently removed at the user's request; this receipt is historical evidence.

### Run October 10 — Nova Micro model access

- Tester: Codex, using the user's existing AWS Console session after explicit EULA confirmation.
- Environment: Bedrock playground, `us-east-2`; Nova Micro 1.0 with US inference profile `us.amazon.nova-micro-v1:0`.
- Input: `Reply with exactly: BEDROCK_WORKING`; maximum output 32 tokens, temperature 0.
- Expected / observed: exact `BEDROCK_WORKING` / exact `BEDROCK_WORKING`.
- Observed usage: 9 input tokens, 6 output tokens, 293 ms latency. Exact invocation timestamp was not captured.
- Status: **AWS model access PASS**; catalog visibility alone was not used as evidence.
- Evidence: `validation_logs/nova-console-20261010.json`, transcribed from the observed Console UI.

### Run 2026-10-10 22:42:35 UTC — Real Strands tool round trip

- Tester: Codex; existing AWS CloudShell session, Python 3.13.15, Strands 1.59.0, `us-east-2`, `us.amazon.nova-micro-v1:0`.
- Tool: data-free `contextforge_compatibility_probe(left=19, right=23)` returns its sum and a fresh diagnostic marker unknown to the model before invocation.
- Expected: exactly one tool call; typed model output reproduces the observed sum and marker.
- Observed: one call with the specified integers; tool returned sum `42`; model returned `42` and the identical marker. Usage: 1,346 input / 185 output / 1,531 total tokens. SDK stop reason `tool_use` accompanies the successful structured result.
- Status: **real model → tool → observed result PASS**. This proves compatibility, not a generated business connector or recovered enterprise question.
- An earlier temporary source transfer failed syntax checking because native text entry altered indentation; corrected before any inference request. No model-access failure was observed.
- Evidence: `validation_logs/aws-strands-20261010T224235Z.json`, transcribed from executed CloudShell JSON output. Marker is not a credential.
- No EC2/IAM resource or account upgrade was created; local application credentials remain unconfigured.

### Run 2026-10-10 22:47:59 UTC — Requested cleanup and MCP preservation

- Removed standalone test/smoke scripts, mock REST server, synthetic records/contract/cases, and their cached bytecode. Retained the four reusable backend modules, dependencies, legacy MCP tool responses, and sanitized receipts.
- Optional workflow now requires explicitly configured approved source URL, contract, host allowlist, and validation cases. Source fingerprint includes URL/contract/allowlist; changing it requires a new approval. Full business behavior against that post-cleanup configuration is not yet executed.
- Verification: one-off syntax/configuration and real MCP SDK checks over HTTPX ASGI; no test script was added back to the repository.
- First verification attempt: **FAIL in the verification assertion** because it expected `structuredContent`. Actual MCP output was JSON text; inspection confirmed the expected fields. The corrected check decoded the real text response; no server fix was needed.
- Final observed result: **13 checks PASS** — all retained Python syntax, missing-token startup refusal, missing-source workflow refusal, six missing/wrong-token GET/POST/DELETE 401 responses, authenticated initialization (protocol `2025-11-25`), exactly the two original tools, exact `pong`, and all legacy inspection fields.
- Scope: in-process protocol/authentication. Active DevRev was not restarted or independently re-invoked; approved-source execution, hosted workflow, and web UI are not covered.
- Evidence: `validation_logs/post-cleanup-mcp-20261010T224759Z.json`, including source hashes and expected observations.

### Run 2026-10-10 23:14:26 UTC — Newly approved synthetic source

- Scope: owner-approved invented demonstration data, `SYNTHETIC_CONTEXTFORGE_DEMO_V1`; not Enterprise-Bench/customer records.
- Executed eight checks using the real source ASGI app and HTTPX adapter: two distinct known records, simulated 403, missing 404, POST 405, rejected Host, and two correctly mapped issue responses.
- Status: **8 checks PASS**. Real HTTP/ASGI operations, not a live socket or model-generated connector.
- Evidence: `validation_logs/synthetic-source-20261010T231426Z.json`.

### Run 2026-10-10 23:21:56 UTC — Local AWS profile readiness

- Tester: owner ran the prepared command in normal Terminal; Codex inspected its saved receipt.
- Profile/region/model: `contextforge`, `us-east-2`, `us.amazon.nova-micro-v1:0`.
- Catalog: **PASS**; Nova models visible. Invocation eligibility is proven only for the selected Micro profile.
- Actual inference: **PASS**, exact `BEDROCK_WORKING`; 9 input / 6 output / 15 total tokens; 477 ms reported latency.
- Actual Strands call: **PASS**, exactly one `inspect_source_contract` invocation. Returned dataset, fingerprint `369f7ef86bcaa195496487b5d93e31edbf51b417737fa3625bba99833a2dcf05`, and allowed-operation count `1` exactly match the typed model answer. Strands usage: 2,282 input / 339 output / 2,621 total tokens.
- Evidence: `validation_logs/workflow-20261010T232156483219Z.json`.
- Earlier attempts from this restricted coding session were **BLOCKED** by `EndpointConnectionError`; missing CRT dependency was corrected before the successful owner run. No IAM permissions, infrastructure, or account tier changed.
- Limit: proves application-profile Bedrock and tool execution, not business connector generation.

### Run 2026-10-10 23:25:53 UTC — Backend MCP and approval acceptance

- **31 checks PASS** using the real MCP SDK, Streamable HTTP ASGI transport, and synthetic REST ASGI app.
- Both default and opt-in apps: authenticated initialize, six missing/wrong-token GET/POST/DELETE 401 checks each, exact inventories, original `pong`, and unchanged legacy inspection fields.
- Opt-in inventory: `ping`, `inspect_demo_capability`, `list_capabilities`, `run_capability`, `propose_connector`.
- Runtime: actual initial missing-capability blocker; validator PASS for known/changed/missing/simulated-forbidden inputs and host/method/path/injection/mapping rejection; unapproved execution denied; approved MCP calls return distinct issue IDs and references; restart retains approval; changed source and disablement deny execution.
- Invalid generation input is rejected before inference; concurrent generation is rejected without another paid model run.
- Evidence: `validation_logs/core-mcp-20261010T232553Z.json`.
- Important scope: manifest explicitly supplied for acceptance checks; automated test approval used only a separate temporary registry. The live registry was not approved. No live Bedrock-generated connector, socket, or DevRev invocation is covered by this receipt.

### Historical ContextForge Test retest — October 10, after backend acceptance

- Codex submitted a fresh request in the existing Computer app to execute both original tools using ContextForge Test, then inspected the returned responses.
- Both actual responses: `Operation Ping/InspectDemoCapability failed: MCP tool execution failed: Could not connect to MCP server with Streamable HTTP transport: TypeError: fetch failed`.
- Status: **FAIL — transport connectivity; neither tool executed**. Earlier successful baseline remains historical evidence.
- Evidence: `validation_logs/devrev-connectivity-20261010T233634222744Z.json`, transcribed from the observed Computer UI. Raw transport trace was not exported.
- This is the older **ContextForge Test** connector. The active **ContextForge Workflow** connector subsequently reached MCP/Strands and returned the actual receipts below; do not treat the old connector's failure as the active integration state.

### Backend checkpoint review — October 10

- Dependency compatibility: `python -m pip check` **PASS**, no broken requirements.
- All six Python modules parsed, all three demo JSON files decoded, and `zsh -n demo/env.zsh` **PASS**.
- Behavior review: busy-generation rejection **PASS**; an inverted guard compiled only in memory caused the assertion to fail by timeout, demonstrating that the check detects that regression. No source mutation, inference call, or live approval occurred.
- Local Markdown links, credential-pattern scan (heuristic), and `git diff --check` **PASS**.
- Checkpoint staging **BLOCKED**: `git add` failed with `fatal: Unable to create '/Applications/Projects/Hackmidwest/.git/index.lock': Operation not permitted`. No commit or push created; project edits remain intact. No further Git setup attempted.

### Run 2026-10-10 23:40:48 UTC — Original permission-classification failure

- Entry point: actual DevRev **ContextForge Workflow** → MCP → Strands/Nova Micro.
- Original question: `Find the engineering issues related to a customer's support ticket using its ticket ID.` Input: `DEMO-101`.
- Observed: empty inventory; initial execution `blocked / Missing approved capability`; Gap Investigator chose `permission_block`. No source inspection, manifest, or validation ran. Gap usage: 1,234 input / 152 output / 1,386 total tokens.
- Status: **FAIL — missing capability incorrectly treated as denied source access**. No connector was activated.
- Root cause: the investigator had no source-access tool and its prompt did not distinguish administrator-approved API inspection from human approval of a generated connector.
- Evidence: `validation_logs/workflow-20261010T234048199610Z.json`, inspected directly.

### Runs 2026-10-10 23:49–23:50 UTC — Source-permission fix and MCP regression

- Added explicit administrator source-inspection authorization, an allowlisted `inspect_source_access` tool, and `propose_new_connector` routing for a missing capability with a successful actual GET. Builder receives the approved API specification and observed access result. Activation remains a separate human action.
- **11 permission checks PASS:** authorized empty inventory, inactive tested candidate, changed input, revoked/missing authorization, unapproved operation, actual synthetic 403, injected 401, undocumented operation, missing record, and rejected source host.
- Scope: actual synthetic REST ASGI requests, scripted agent routing, supplied acceptance manifest, and temporary registries; not real Bedrock generation or live approval.
- **22 MCP/auth checks and syntax PASS:** default/opt-in inventories, initialize, unchanged baseline tools, missing/wrong-token GET/POST/DELETE 401 rejection, empty inventory, and missing-capability blocker. Real SDK over ASGI; no live socket.
- Evidence: `validation_logs/permission-regression-20261010T234951695242Z.json` and `validation_logs/permission-fix-mcp-20261010T235037764815Z.json`.

### Run 2026-10-10 23:54:42 UTC — Live access succeeds; decision omits operation ID

- Codex submitted the exact original question and `DEMO-101` to **ContextForge Workflow** after the owner restarted MCP.
- DevRev's live Ping and InspectDemoCapability returned their unchanged expected responses; ListCapabilities returned an empty synthetic inventory. **Baseline connectivity PASS**.
- Actual Strands `inspect_source_access` ran once against the loopback synthetic API: authorized operation `get_ticket_engineering_issues`, schema-checked HTTP **200**, observed status `ok`. Source revision: `12fdfce6a4f48ea997086cd83de546ce3813b9b57ed67bbc3c135cc038403132`.
- Generation: **FAIL / BLOCKED**. The proposal branch received a null operation ID, so the deterministic allowlist rejected it before the builder. No manifest or candidate was produced. The receipt's `gap` had been overwritten by that guard; this limitation was identified during code/receipt inspection.
- This is a malformed agent decision, **not evidence that source authorization needs widening**. The inspected operation was already authorized. Gap usage: 3,397 input / 263 output / 3,660 total tokens.
- Evidence: `validation_logs/workflow-20261010T235442515296Z.json` and UI transcript receipt `validation_logs/devrev-workflow-connectivity-20261010T235817700656Z.json`. No approval or activation occurred.

### Run 2026-10-10 23:56:37 UTC — Operation-ID correction

- Reproduced the defect: constructing `propose_new_connector` with `operation_id=null` was accepted (**regression assertion FAIL before fix**).
- Added descriptive output fields and a Pydantic cross-field validator requiring the verified operation ID for proposals. Strands returns validation feedback for invalid output; four bounded gap turns allow a correction. Receipts retain `agent_gap` separately from deterministic decisions.
- **14 focused checks PASS:** null/empty proposal IDs rejected; block/unsupported decisions can omit the ID; real installed Strands structured-output tool returns error feedback then accepts valid output; authorized path reaches ten actual validator checks; candidate stays tested/inactive; 401/403 override an agent's proposal while retaining its original decision; revoked/missing authorization and missing records remain blocked; syntax passes.
- Scope: real structured-output validation and HTTP/ASGI operations with scripted agent routing and temporary registries. This does not prove a new live Nova proposal.
- An initial verification command failed import because it referenced `app` instead of the source's `create_app`; corrected in the one-off verification command, without a product-code change. Dependency check also PASS: no broken requirements.
- Evidence: `validation_logs/gap-decision-regression-20261010T235637994448Z.json`. The subsequent owner restart enabled the successful live run below.

### Run 2026-10-10 23:59:30 UTC — Original DEMO-101 proposal succeeds through DevRev

- Entry point: fresh Computer **ContextForge Workflow** → authenticated MCP → actual Strands/Nova Micro agents → live synthetic REST source. Ping also returned the unchanged expected response after the owner restarted MCP.
- Exact original question and `DEMO-101`; inventory empty, initial task genuinely `blocked / Missing approved capability`.
- Gap Investigator invoked `inspect_source_access` once: explicitly authorized `get_ticket_engineering_issues`, schema-checked HTTP **200**, then chose **`propose_new_connector`** with that operation ID. `agent_gap` and enforced `gap` agree.
- Builder generated the manifest from the approved contract and invoked the real validator **twice**. Both reports PASS; an independent validation of the returned manifest also PASS. No failed mapping/repair occurred in this run.
- **Ten distinct checks PASS in all three reports:** manifest allowlist; known `DEMO-101` → `DEMO-ENG-201`; changed `DEMO-102` → `DEMO-ENG-202`; missing record; simulated forbidden record; arbitrary-host field; mutation method; undocumented path; path injection; wrong output mapping. Positive/missing/forbidden/mapping probes used actual HTTP requests; manifest/input rejection checks intentionally made no unauthorized request.
- Generated capability ID: **`get_ticket_engineering_issues_76f8fc748bff`**. Manifest:

```json
{
  "name": "get_ticket_engineering_issues",
  "purpose": "Retrieve engineering issues related to a specific support ticket",
  "operation_id": "get_ticket_engineering_issues",
  "method": "GET",
  "path_template": "/tickets/{ticket_id}/engineering-issues",
  "output_mapping": {
    "ticket_id": "ticket_id",
    "related_issues": "related_issues",
    "source_refs": "source_refs"
  }
}
```

- Requested-record check: `DEMO-101`, observed `ok`. Unapproved dispatcher attempt: **`approval_required`**. Workflow status: **`TESTED_REQUIRES_APPROVAL`**.
- Usage: gap 3,584 input / 363 output / 3,947 total; builder 6,888 input / 590 output / 7,478 total; combined **11,425 tokens**. No infrastructure, IAM, source authorization, account-tier, token, or endpoint change.
- Status: **PASS — actual generated proposal, source access, measured validation, and inactive approval boundary**. The final enterprise answer remains unverified until human approval and a fresh Computer execution.
- Primary evidence: `validation_logs/workflow-20261010T235930202162Z.json`, directly inspected and matched to the Computer response.
- Read-only SQLite audit at 2026-10-11 00:00:56 UTC: one capability; exact manifest/hash-derived ID; status **`tested`**, `approved_by=null`, matching source revision and PASS report. No approval action performed. Audit evidence: `validation_logs/live-proposal-audit-20261011T000056121968Z.json`.

### Run 2026-10-11 00:00:47 UTC — Live forbidden input and approval protection

- Fresh **ContextForge Workflow** calls: InspectDemoCapability returned the unchanged expected response; ListCapabilities showed the exact candidate in status **`tested`**. Actual RunCapability for that ID and `DEMO-101` returned **`approval_required`**. No activation or approval occurred.
- ProposeConnector used the original question with the documented synthetic `DEMO-403` input. The actual source inspection returned HTTP **403**, `observed_status=forbidden`, `status=permission_block`.
- **Deterministic permission enforcement PASS:** final `gap.action=permission_block`, workflow `BLOCKED`, no generated manifest/capability ID, `tool_validations=[]`, no builder usage. The existing tested candidate was retained unchanged.
- **Raw agent classification FAIL:** `agent_gap.action=propose_new_connector` incorrectly claimed source access was confirmed despite the 403. The guard overrode that decision. Do not describe this as the agent understanding all permission errors; correctness depends on deterministic source-status enforcement. Prompt/classification refinement is future work, not a reason to loosen the guard.
- Gap usage: 3,708 input / 420 output / 4,128 total tokens. No builder inference or validator call ran.
- Evidence: `validation_logs/workflow-20261011T000047285949Z.json`, inspected directly and matched to Computer's actual response. The later read-only registry audit confirms a single inactive candidate, `approved_by=null`.

### Permission-fix checkpoint review — October 10 local time

- Retained Python syntax and demo JSON **PASS**; `zsh -n demo/env.zsh`, `python -m pip check`, local Markdown links, and `git diff --check` **PASS**.
- Live receipts verified directly; generated ID recomputed from the exact manifest; SQLite opened read-only and confirmed one inactive candidate with no approver. The Nova 403 classification error is retained separately from the passing permission guard.
- Staging the explicit reviewed backend/demo/documentation paths **BLOCKED**: `git add` exited 128, `fatal: Unable to create '/Applications/Projects/Hackmidwest/.git/index.lock': Operation not permitted`. No commit/push created. Existing `AGENTS.md`, credentials, state, environments, and ignored local receipts were not staged or modified for publication.

### Run 2026-10-11 00:13:20 UTC — Human-administrator approval acceptance

- Reproduced a real authorization defect in a **temporary registry**: arbitrary nonempty `--approver` label could activate a candidate. Regression assertion **FAIL before fix**. The actual generated connector remained `tested`, no approver.
- Approval now requires the registry owner's OS UID, membership in an explicit private administrator policy, an interactive Terminal, and exact confirmation after reviewing the current manifest/source/complete PASS report. Labels do not grant authority. Policy/registry ownership and permissions are checked; source/candidate changes during review deny approval. The approval and identity/hash audit event commit atomically.
- `init-admin` only registers the human owner's OS identity after exact interactive confirmation; it never activates a connector or overwrites existing policy. Neither administrator registration nor approval is exposed through MCP.
- **33 grouped acceptance checks PASS:** absent/unlisted/unsafe/symlink policy, private database, headless/wrong/cancelled confirmation, incomplete/failed/mismatched tests, changed/revoked source, tampered manifest, role revocation and candidate changes during review, explicit role setup without activation, no policy overwrite, authenticated identity audit, actual distinct REST records/references, forbidden response, request receipt metadata/privacy, invalid-input rejection, both MCP modes' 401/initialize/inventory/original tools, approved temporary dispatcher calls, and absence of MCP approval/audit override.
- Scope: simulated human confirmation **only in separate temporary registries**, actual synthetic REST ASGI requests, real MCP SDK/ASGI. **Not live human approval, socket execution, or teammate reuse.** Actual live registry verified read-only as `tested`, `approved_by=null` after the checks.
- Added private execution receipts for actual GET path, received HTTP status, transport type, outcome, and references; returned tool payload remains compatible. No bearer headers, credentials, arbitrary invalid-input fields, or customer records recorded.
- Evidence: `validation_logs/approval-acceptance-20261011T001320650066Z.json`, including source hashes. Retained syntax, dependency consistency, CLI help, and `git diff --check` also PASS. The actual administrator policy is not yet configured/readable; human action is required.

### Run 2026-10-11 00:16:36 UTC — Persistent approval event enforcement

- Added a dispatcher check for a matching administrator event bound to the exact manifest hash, source revision, registry-owner UID, and verified approver identity. A raw `status=approved` or forged label alone cannot enable a capability.
- **Final 37 grouped checks PASS**: repeated the relevant 33 checks after this change and added legacy/forged activation without an event, mismatched administrator UID, changed manifest after approval, and changed approver identity. Each denial prevents the HTTP request.
- Scope remains temporary registries, simulated human input, real MCP/REST ASGI. The actual generated candidate was again verified `tested`, no approver; no human approval or live network execution is claimed.
- Evidence: `validation_logs/approval-acceptance-20261011T001636918138Z.json` with final source hashes.

### Runs 2026-10-11 00:29–00:34 UTC — Explicit human administrator approval

- Tester: project owner in normal Terminal; Codex later verified CLI receipts and the registry read-only.
- `init-admin` recorded `ADMINISTRATOR_CONFIGURED` for OS identity `sujanreddyayyagari`, UID `501`, at 00:29:12 UTC. Repeating initialization at 00:30:31 correctly returned `BLOCKED` rather than overwriting the policy.
- Unconfirmed approvals at 00:31:28 and 00:32:52 returned `BLOCKED`; the connector remained inactive for those attempts.
- Explicit approval succeeded at **00:34:09.863834 UTC** for `get_ticket_engineering_issues_76f8fc748bff`. SQLite now records `approved`, the verified OS administrator, and one matching approval event. The report contains all ten mandatory PASS checks.
- Manifest SHA-256: `76f8fc748bffa0a28829b910b72a7d5e96a62bf5f5de607f45b68223bd75ac1d`. Source revision: `12fdfce6a4f48ea997086cd83de546ce3813b9b57ed67bbc3c135cc038403132`. Validation-report SHA-256: `abc7378077ec39d6c716837dd1034d7a32aeb78b7c76e7c83799351b7b26e4b5`.
- Status: **human approval PASS; unconfirmed approval rejection PASS**. This is the trusted local OS administrator boundary; MCP agents cannot approve, and web/enterprise identity delegation is not established.
- Evidence: `validation_logs/workflow-20261011T002912086985Z.json`, `workflow-20261011T003031056393Z.json`, `workflow-20261011T003128132557Z.json`, `workflow-20261011T003252764271Z.json`, `workflow-20261011T003409865622Z.json`, and the read-only approval audit below.

### Run 2026-10-11 00:35:17 UTC — First approved execution fails upstream

- Entry point: actual `mcp`, approved capability, network `GET /tickets/DEMO-101/engineering-issues`.
- Expected: correct ticket/issue data and references. Observed: `upstream_error`, no issue IDs or references, and no received HTTP status in the trace. Computer displayed the failure and withheld an answer.
- Status: **FAIL for task completion**. The receipt does not identify the underlying network/source failure; do not infer a received HTTP error or a root cause. Later successful calls are separate executions, not a replacement of this evidence.
- Evidence: `validation_logs/execution-20261011T003517951940Z-9ec195b0.json` and the saved Computer conversation.

### Runs 2026-10-11 00:41–00:43 UTC — Approved execution and recovered answer

- Tester: owner using **ContextForge Workflow** in DevRev Computer; Codex inspected the saved Computer responses and matched private execution receipts.
- Capability: `get_ticket_engineering_issues_76f8fc748bff`; approval `approved`; unchanged source revision and manifest above. Every receipt has `entry_point=mcp`, `transport=network`, method `GET`, and a received source HTTP status.

| UTC time | Input | Expected / observed | Result | Execution receipt in `validation_logs/` |
|---|---|---|---|---|
| 00:41:51.806942 | `DEMO-101` | HTTP 200, `ok`, `DEMO-ENG-201`, title “Synthetic issue: normalize SAML audience after migration,” ticket and issue references | PASS | `execution-20261011T004151806942Z-d7f1023d.json` |
| 00:43:14.216053 | `DEMO-102` | HTTP 200, `ok`, different issue `DEMO-ENG-202`, title “Synthetic issue: paginate report export queries,” corresponding references | PASS | `execution-20261011T004314216053Z-2526c9d4.json` |
| 00:43:14.737612 | `DEMO-403` | Source HTTP 403, tool `forbidden / http_status=403`, no records or references | PASS | `execution-20261011T004314737612Z-3c5fe286.json` |

- Positive references are `synthetic://contextforge/tickets/<ticket_id>` and `synthetic://contextforge/issues/<issue_id>`. Both full source-response SHA-256 values match the exact JSON bodies produced by the documented synthetic fixtures: DEMO-101 `75a5a4e96a322cc9d26eb52e7f621b60841f6a2729c683d89864f5f052fc66e7`; DEMO-102 `aef8886f61d9618147200724762fb1aeb822a7396c62dabc8b3af3a077741f80`.
- Computer displayed the correct DEMO-101 issue/title/references and answered the original previously blocked question. Its exact DEMO-102 and DEMO-403 tool JSON also matches the receipts. The observed account is `Sujanreddy298 Bench-07`; these calls do **not** prove a second user's access.
- Status: **D4/D5 PASS for the owner-approved synthetic source; changed-input execution and post-approval denial PASS**. No new connector, approval bypass, or hardcoded runtime response was required. The source's 403 is a synthetic denial case, not evidence of DevRev per-user permission delegation.

### Audit 2026-10-11 00:48:37 UTC — End-to-end evidence reconciliation

- **23 evidence checks PASS** against saved receipts and read-only SQLite: hash-derived ID, exact manifest/report/source binding, trusted administrator UID, blocked confirmations, live Strands proposal, actual MCP network paths/statuses, distinct returned evidence, exact positive response-body hashes, and preservation of the earlier failure.
- Current source hashes are recorded in the audit receipt. No request, model inference, approval, service restart, or second-user invocation was executed during this audit; existing Computer responses were inspected through the native app.
- Evidence: `validation_logs/end-to-end-evidence-audit-20261011T004837420359Z.json`. This reconciliation is separate from the ten product validation checks and the earlier 37 scoped acceptance checks.

### Checks 2026-10-11 00:58–01:10 UTC — Minimal demo and preparation

- Implemented a separate read-only view on loopback port 8002 using existing Starlette/Uvicorn and plain HTML/CSS/JavaScript. It projects the actual synthetic proposal, measured report, exact current approval, and latest MCP execution receipts. Generation history is labeled recorded; refresh performs no model, source, execution, or approval action.
- Initial **28 HTTPX/ASGI checks PASS** at 00:58:15 UTC: current hashes/approval, distinct source-body-verified projections, source 403 withholding, static routes, host/CSP/no-cache/privacy controls, mutation/private-route rejection, changed source, incomplete evidence, missing registry, and no database modification. Evidence: `validation_logs/demo-view-asgi-20261011T005815556465Z.json`.
- Review found incorrect environment names in the new view/deployment examples. Aligned them with the working runtime's `CONTEXTFORGE_ALLOWED_SOURCE_HOSTS` and `CONTEXTFORGE_DB`, and closed read-only database connections explicitly. Existing backend modules and source configuration were not changed.
- Final **41 focused checks PASS** at 01:10:38 UTC: 30 read-only/view/configuration checks, five inactive Enterprise-Bench contract checks, five deployment static boundary checks, and retained Python syntax. Alternate-database configuration reaches the view and backend; a changed source allowlist withholds verified approval and answers. The real registry remained unchanged. Evidence: `validation_logs/demo-and-preparation-20261011T011038288653Z.json`, with final UI source hashes. JavaScript syntax also passed `node --check`.
- The Enterprise-Bench handoff contract has a valid normalized-output schema, **no routes**, and **inspection authorization false**. Real adapter calls in-process return `permission_block` / `forbidden`, reject the synthetic manifest, and make no HTTP request. This is an inactive preparation boundary, **not** approved-data integration.
- AWS examples separate the MCP secret from source/view services, retain loopback ports, separate protected web access from MCP bearer access, avoid publicly proxying the source, and perform no automatic approval. Only static/environment checks ran; **Caddy/systemd runtime, hosted model/source/MCP, and deployment remain NOT TESTED**. No instance, IAM permission, DNS, account tier, or working endpoint was changed.
- An actual `.venv/bin/python demo_view.py` launch in this agent session exited 3 with `[Errno 1] operation not permitted` while binding `127.0.0.1:8002`. **Socket startup BLOCKED by sandbox; browser and timed rehearsal NOT TESTED.** The owner must start this separate process in normal Terminal; existing MCP/source/tunnel need no restart.

### Teammate access update — captured 2026-10-11 01:13–01:14 UTC

- Initial teammate Computer session reported no ContextForge/Ping/ListCapabilities tools; no tool was invoked. Owner Settings → My Computer → Connectors showed **ContextForge Workflow Connected** and all five tools. The observed action menu contained resync/remove/disconnect/delete; no sharing control was found there.
- The teammate then confirmed **Bench-07** and a visible connector card, but was prompted for a Personal Access Token and lacked the server token. Reuse was **BLOCKED on authentication**, recorded in `validation_logs/devrev-reuse-blocker-20261011T011356563210Z.json`. Six backend source hashes still matched the end-to-end audit.
- Clarified that this field accepts the existing server's `MCP_TOKEN`, entered privately without a `Bearer ` prefix, not a DevRev account PAT. No secret was read, printed, recorded, rotated, or sent by Codex; server authentication and CLI-only human approval remain intact.
- The user subsequently reported the teammate connected successfully. **Connection success is user-reported; D6 remains NOT TESTED** until their own session executes Ping/ListCapabilities and the approved DEMO-102/DEMO-403 calls. At 01:14:50 UTC the latest execution receipts were still the owner's 00:41–00:43 calls. Teammate alias and fresh matching network receipts remain pending.
- Evidence: `validation_logs/devrev-reuse-status-20261011T011450610156Z.json`. Follow [DEVREV_REUSE.md](DEVREV_REUSE.md); a shared bearer cannot attest an individual identity or per-user record permissions.

### Runs 2026-10-11 01:24–01:25 UTC — Reported teammate tool calls

- The user supplied actual Computer responses: Ping returned the exact baseline string, ListCapabilities returned the same approved ID, DEMO-102 returned the correct issue/title/references, and DEMO-403 returned `forbidden`, HTTP 403, with no data. Ping/inventory are **user-reported PASS**; the dispatcher calls have independent fresh network receipts below.
- **01:24:50.173080 UTC, DEMO-102:** `execution-20261011T012450173080Z-007ba1d1.json` records actual MCP/network `GET /tickets/DEMO-102/engineering-issues`, received HTTP 200, and `ok`. Full source-body SHA-256 remains `aef8886f61d9618147200724762fb1aeb822a7396c62dabc8b3af3a077741f80`, matching the documented synthetic issue `DEMO-ENG-202`, title “Synthetic issue: paginate report export queries,” and both supplied references. **PASS**.
- **01:25:20.054938 UTC, DEMO-403:** `execution-20261011T012520054938Z-dab82516.json` records actual MCP/network GET, received source HTTP 403, and `forbidden`; issue IDs and source references are empty. **PASS**. This remains a synthetic source denial, not per-user identity delegation.
- Both calls use `get_ticket_engineering_issues_76f8fc748bff`, the unchanged source revision, and `approval_state=approved`. Read-only SQLite shows exactly one capability and the original single 00:34:09 administrator event; no new generation or approval was required.
- **17 reconciliation checks PASS** at 01:27:03 UTC: fresh actual requests, positive full-body hash and returned evidence, continued denial, manifest/source/report/UID binding, ten original product checks, fresh view projections, six unchanged backend source hashes, and no audit database mutation. Evidence: `validation_logs/devrev-reuse-evidence-20261011T012703377285Z.json`. Codex executed evidence reads only, not another live tool/model/source call.
- The owner confirms the teammate was invited into the organization. **D6 identity confirmation remains pending:** the provided outputs and shared bearer do not identify the caller. Confirm the calls came from the teammate's own Bench-07 Computer login before marking full second-user reuse PASS; do not repeat the already verified dispatcher calls merely to collect an alias.

### Confirmation captured 2026-10-11 01:30:38 UTC — D6 complete

- The user explicitly confirmed: **“Yes, teammate’s own login.”** Combined with the previously confirmed Bench-07 connection and actual fresh dispatcher receipts, this completes **D6 PASS for the approved synthetic source**.
- Tester: invited Bench-07 teammate; alias was not supplied and is not invented. Computer identity is confirmed by the user, not independently observed by Codex or inferred from the bearer token. Ping/inventory are user-reported actual outputs; DEMO-102/DEMO-403 network/source results and original approval continuity are independently verified.
- Reused the existing capability and human approval without another proposal or activation. The source denial remained enforced; no per-user source permission, official-data, or hosting claim follows from this test.
- Final evidence: `validation_logs/devrev-reuse-completion-20261011T013038388953Z.json`, referencing the 17-check audit and both fresh execution receipts. Browser rehearsal (D10), actual Enterprise-Bench access (B1), and hosted workflow (D7) remain pending.

### Checks 2026-10-11 01:44–01:53 UTC — Browser demo and timed execution

- The owner started the view at `http://127.0.0.1:8002`. Native Chrome inspection executed **21 UI checks PASS**: actual labeled records/manifest/checks/approval, all five walkthrough steps, keyboard navigation, copying, distinct input selection, sanitized execution details, fresh receipt refresh, 393×852 narrow layout, offline error handling, recovery, and console diagnostics. Browser/CDP backends were unavailable; native CUA controlled Chrome.
- Fixed a reproduced sticky-guide overlap by aligning scroll targets to the start and removing sticky positioning on narrow screens; desktop and phone selection retests PASS. No backend feature, dependency, source, or approval change was made for UI polish.
- **22 read-only ASGI/evidence reconciliation checks PASS** at 01:50:44 UTC: exact approval/manifest/source bindings, positive source-body hash, fresh network receipt, original teammate evidence, private headers, mutation/host rejection, unavailable evidence, and changed-source withholding. JavaScript syntax also PASS. Receipt: `validation_logs/demo-current-evidence-audit-20261011T015044621681Z.json`.
- Two technical walkthroughs completed in **74 seconds** (01:44:00–01:45:14) and **70 seconds** (01:51:23–01:52:33). Each showed recorded generation/validation/approval, executed DEMO-101 live in Computer, refreshed the new receipt, and inspected saved teammate success/denial. Fresh network HTTP 200 receipts: `execution-20261011T014444677863Z-d9f18378.json` and `execution-20261011T015156996729Z-ba44ce07.json`; exact issue/title/references and source-body hash verified.
- **D10 PASS for this technical recorded-history-plus-live-execution scope.** Spoken stage delivery, a fresh generation/approval cycle within three minutes, and hosted access were not tested. Six backend module hashes and the single approval were unchanged at this checkpoint. Receipt: `validation_logs/demo-browser-rehearsal-20261011T015319302873Z.json`.

### Run 2026-10-11 01:57 UTC — Automatic existing-capability selection

- Executed `ProposeConnector` live through Computer with: “Which engineering issue is linked to support ticket DEMO-101? Include its title and source references.” Actual Nova/Strands usage: 1,808 input + 210 output = 2,018 tokens. Initial approved capability execution returned correct source data.
- **FAIL:** the Gap Investigator chose `reuse_existing` with `capability_id=null`. The approved-inventory guard rejected it with `Agent selected a capability that is not approved`. No connector was generated or activated; direct approved execution remains working. Receipt: `validation_logs/workflow-20261011T015738072518Z.json`.
- Root cause: `GapDecision` conditionally required the proposal operation ID but accepted an omitted reuse ID; context did not explicitly bind the initial result to its capability ID. The exact response reproduced the schema weakness (**RED FAIL**): `validation_logs/reuse-selection-red-20261011T015845970396Z.json`.
- Fixed the conditional reuse-ID validator, field description, prompt, and `initial_capability_id` context/receipt binding. The model must select an exact approved inventory ID; runtime membership checks remain authoritative. No fallback fills in a model decision.
- **31 focused local checks PASS** at 02:02:56 UTC: invalid reuse IDs rejected, pinned Strands structured-output tool returns actionable validation errors, explicit reuse runs the real source adapter in-process, unapproved IDs rejected, source 403 and absent authorization enforced, generation still invokes ten validator checks and stays inactive, original MCP tools/authentication preserved, syntax valid, working registry/approval and five other backend modules unchanged. Controlled agents and ASGI source were used here; this is not a live Bedrock rerun. Receipt: `validation_logs/reuse-selection-fix-20261011T020256818606Z.json`.
- **Live fixed rerun PENDING MCP restart.** Preserve the same token, source, tunnel, registry, and demo process. Do not count this local fix as a successful live automatic reuse decision.

## 3. Gate A — Protocol and DevRev connectivity (must pass first)

| ID | Test | Expected outcome | Current status |
|---|---|---|---|
| A1 | Install `mcp==1.30.0` from starter requirements | Install completes without dependency error | PASS — Python 3.12.15, pinned SDK imports, pip check verified |
| A2 | Run starter `python server.py` locally | Process remains active; listens on `127.0.0.1:8000` | PASS — user confirms authenticated integration running; post-cleanup ASGI verified |
| A3 | Local MCP `initialize` request | HTTP success with MCP initialization data | PASS — original live baseline and post-cleanup authenticated ASGI; no fresh live local receipt |
| A4 | Discover tools via MCP client | Both `ping` and `inspect_demo_capability` listed | PASS — original live baseline and post-cleanup authenticated ASGI; no fresh live local receipt |
| A5 | Invoke `ping` via MCP client | Exact response `pong - ContextForge MCP tool is reachable` | PASS — original live baseline and post-cleanup authenticated ASGI; no fresh live local receipt |
| A6 | Expose temporary HTTPS tunnel (data-free starter only) | Authenticated HTTPS `/mcp` endpoint is reachable remotely | PASS (user-reported) — authenticated Cloudflare endpoint used by Computer |
| A7 | Register connector in DevRev | Setup succeeds; tools are discoverable as applicable | PASS (user-reported) — registered connector invokes the expected tools |
| A8 | **Invoke** `ping` from DevRev Computer | Computer shows exact `pong - ContextForge MCP tool is reachable` from tool output | PASS — fresh ContextForge Workflow invocation after restart |
| A9 | Invoke `inspect_demo_capability` from Computer | Result includes `capability: connectivity-test`, `status: working`, `sample_records: 0` | PASS — fresh ContextForge Workflow invocation after restart |
| A10 | Stop tunnel and repeat request | Connector becomes unavailable without invented output | NOT TESTED |

**A8 is the essential go/no-go test.** A1–A7 alone do not prove that Computer can call tools. Passing A8 proves connectivity only—not data correctness, auth, sponsor acceptance or connector generation.

### Local HTTP rejection probe

In one terminal start the supplied server. In another:

```bash
curl -i http://localhost:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"validation","version":"1.0"}}}'
```

**Pass:** HTTP 401 with `WWW-Authenticate: Bearer`. This request deliberately omits credentials. Current SDK acceptance receipts cover authenticated initialization, discovery, and invocation; the old smoke client was removed.

### A3/A4/A5 — Current verification

The standalone `connectivity_smoke.py` client was removed after the AWS check at the user's request. Historical commands in the run log refer to the earlier build, not current launch instructions.

The post-cleanup receipt records executed initialization, exact discovery, and both tool responses through the real MCP SDK and in-process ASGI. Keep the working normal-Terminal server/tunnel running. Real Computer invocation is user-reported; new dispatcher calls and public unauthorized rejection require their own receipts.

### Public tunnel caveat

The included starter uses `json_response=True` and `stateless_http=True`, and its TransportSecuritySettings allow `localhost:8000` and `127.0.0.1:8000`. The documented quick-tunnel command passes an origin Host header to match that allowlist. **Cloudflare Quick Tunnels do not support Server-Sent Events**; DevRev may need behavior that the tunnel does not carry. If A3/A5 pass locally but A8 fails, check the hosted transport, not just your tool code. The current tunnel works per the user. Keep it until an approved AWS replacement passes actual Computer calls; Akamai is currently unavailable.

## 4. Gate B — Source integrity and safe connector behavior

| ID | Test | Expected outcome | Status |
|---|---|---|---|
| B1 | Query known approved Enterprise-Bench record | Correct record ID and source reference returned | NOT TESTED |
| B2 | Query nonexistent record | `not_found` or explicitly empty, not fabricated data | PASS for newly approved synthetic API; Enterprise-Bench NOT TESTED |
| B3 | Query ambiguous identifier | Ask to disambiguate or report ambiguity, not guess | NOT TESTED |
| B4 | Attempt unauthorized record/operation | Server returns denial regardless of agent prompt | PASS — live synthetic 403 blocks proposal and remains forbidden after human approval; local absent/revoked authorization and 401 rejection also pass; real customer/per-user permissions NOT TESTED |
| B5 | Ask for an unlisted outbound URL/host | Executor refuses; no arbitrary requests/SSRF | PASS in current configured-runtime negative checks; live agent scenario NOT TESTED |
| B6 | Attempt non-GET mutation through generated adapter | Rejected by deterministic allowlist | PASS — actual Strands-generated manifest validator rejects POST; source POST 405 also checked locally |
| B7 | Simulate slow or failed upstream API | Timeout/error visible; no fabricated success | Live upstream_error surfaced without invented data; controlled timeout/failure simulation NOT TESTED |
| B8 | Return record with missing evidence fields | Output marks source missing and withholds source-backed claim | NOT TESTED |
| B9 | Expose secure endpoint publicly | Authenticated HTTPS works; unauthenticated access denied | NOT TESTED |
| B10 | Change capability mapping version | Prior version and test record remain inspectable | NOT TESTED |

**Gate B passes only if B1, B2, B4, B5, B6 and B9 pass.** Others are strongly recommended. The current starter requires bearer authentication even for the content-free Gate A probe; public access must use HTTPS.

## 5. Gate C — Agent behavior and generator correctness

| ID | Scenario | Expected behavior | Status |
|---|---|---|---|
| C1 | Task already solvable using an existing tool | Coordinator chooses reuse, not redundant generation | NOT TESTED |
| C2 | Task blocked only by missing permission | Coordinator requests access, not privilege escalation | Enforcement PASS (live synthetic 403 and local revoked/missing authorization/401); raw Nova classification FAIL on live 403, safely overridden |
| C3 | Task blocked by incorrect field mapping | Coordinator proposes a mapping fix | NOT TESTED |
| C4 | Task lacks a necessary read-only operation, available in approved API | Builder proposes valid typed adapter manifest | PASS — live original DEMO-101 proposal, generated GET manifest and measured validation |
| C5 | API operation missing from allowed specification | Builder refuses to invent endpoint | PASS in deterministic/scripted permission checks; live model scenario NOT TESTED |
| C6 | Proposed adapter maps wrong output field | Actual test fails with traceable mismatch | PASS in current approved synthetic runtime checks; live model repair NOT TESTED |
| C7 | Failed mapping test returned to Strands | Agent proposes a bounded correction; rerun measured test | NOT TESTED |
| C8 | Model tries to activate an unapproved adapter | Server refuses activation or execution | PASS — live proposal's unapproved dispatcher attempt returns approval_required; agents expose no approval tool |
| C9 | Model call/tool-call budget exhausted | Clear partial/unresolved result, no infinite loop | NOT TESTED |
| C10 | Known source link removed | Explanation becomes uncertain; no invented link or root cause | NOT TESTED |

### Minimal acceptance for the "AI built it" claim

1. Store the **original task** and initial tool inventory.
2. Have Strands produce a **new manifest from the allowed API contract** (not merely select a hardcoded finished connector).
3. Save a test transcript showing at least one real request, parameter validation, and observed source fields.
4. Human approves activation.
5. The original task executes through the activated manifest.
6. Repeat with a changed input and show the returned evidence changes accordingly.

If item 2 is not implemented, call it **AI-assisted connector configuration** rather than automatic connector creation. If item 5 is not implemented, do not claim the blocked task was resolved.

## 6. Gate D — End-to-end product and sponsor demonstration

| ID | Test | Pass condition | Status |
|---|---|---|---|
| D1 | Run one real enterprise question before capability activation | Missing operation is correctly described and logged | PASS for original question in constrained synthetic inventory: actual MCP initial result blocked; real enterprise source NOT TESTED |
| D2 | Analyze need using actual approved feedback/task evidence | Missing context type supported by cited records | NOT TESTED |
| D3 | Generate and test proposed operation | All mandatory tests produce real reports | PASS — actual DevRev/Strands generated connector, ten distinct measured checks; labeled synthetic source |
| D4 | Approve operation and invoke via stable MCP tools | Operation works; requires no arbitrary prompt bypass | PASS — explicit OS administrator approval bound to exact manifest/source/PASS report; live MCP network GETs succeed |
| D5 | Repeat original Computer question | Returns a source-backed, relevant answer | PASS — saved Computer answer and DEMO-101 execution receipt match the synthetic source; earlier failed attempt retained |
| D6 | Second authorized teammate uses different input | Same capability works for them within permissions | PASS — user confirms invited teammate's own Bench-07 login; fresh DEMO-102/DEMO-403 MCP network receipts match actual supplied responses; identity is user-attested, source authorization shared |
| D7 | Approved hosted system serves real workflow | Can inspect hosted agent/tool/database requests | NOT TESTED — AWS templates statically checked, not installed; eligibility/identity/hostname/full quote/provisioning approval pending |
| D8 | Strands handles tool feedback | Logs show model→tool→result→revision or decision | PASS — actual source inspection decision and builder validator reports consumed; live mapping repair NOT TESTED |
| D9 | Revoke or disable capability | Further calls are denied; previous activity remains auditable | Denial PASS in current ephemeral runtime checks; production audit history NOT TESTED |
| D10 | Three-minute live demonstration | Repeatable within time; no hidden pre-recorded result passed off as live | PASS — technical walkthroughs 74s/70s: labeled recorded generation/approval plus fresh live Computer execution; spoken delivery and fresh generation within the time limit NOT TESTED |

**Must-pass for intended sponsor story:** D3–D8 and D10. If another user's access is blocked by playground provisioning, ask the DevRev sponsor immediately; do not fake the reuse claim.

## 7. Go / narrow / pivot decisions

### GO — build the full narrow connector workshop

- A8 passes (Computer calls actual MCP tool).
- Approved Enterprise-Bench source can be queried (B1), and authenticated hosting is working (B9).
- Strands successfully consumes real tool feedback (D8).
- One useful, realistically testable missing operation exists in the agreed workflow.

### NARROW — keep the work reusable, reduce autonomy

Use when the gateway and source access work but connector generation is unstable:

- Generate a **proposed mapping for one fixed operation**.
- Keep source-linked explanation and rigorous tests.
- Approve activation manually and call via a stable dispatcher.
- Describe the product honestly as **AI-assisted capability creation**.

### PIVOT / ASK SPONSOR — core DevRev integration unavailable

Use when DevRev cannot call a compliant remote MCP server after trying the official starter and sponsor help:

- Consider a reusable DevRev Computer skill using existing available tools and an Enterprise-Bench dataset-backed task.
- Preserve AWS Strands and Akamai where they add genuine functionality.
- Do not claim a DevRev connector prize outcome from a local-only demo.

## 8. Suggested objective measurements

| Metric | What to record | Avoid claiming |
|---|---|---|
| **Task completion** | Did the original question produce a verified useful artifact? | “Connected” means completed |
| **Build success** | % of candidate manifests passing agreed real tests (show numerator/denominator) | Universal connector generation |
| **Correctness** | Matched source IDs and assertions on held-out inputs | Model agreement as objective truth |
| **Reuse** | Different user and different input successfully invoked same tool | Replaying a cached answer as reuse |
| **Latency** | Detection-to-tested proposal; proposal-to-usable tool time | Extrapolating one fast demo to all enterprise APIs |
| **Security** | Unauthorized operations actually denied | Prompt-only permission controls |
| **Model consumption** | Model calls, tool calls, run duration | Unlimited spontaneous agents |

## 9. Current facts, unknowns, and references

### Confirmed

- Reusable backend remains; earlier standalone tests/demo were removed. A newly authorized synthetic API, explicit configuration, and documented records are now present.
- MCP 1.30.0 and Strands 1.59.0 coexist without reported dependency conflicts; default authenticated MCP works in post-cleanup ASGI checks.
- Fresh ContextForge Workflow calls return both baseline responses and inventory through DevRev; the historical ContextForge Test transport failure is separate.
- Nova Micro invocation and a real Strands tool/result cycle also passed through the local `contextforge` AWS profile; receipt inspected directly.
- Actual MCP/Strands proposal generated `get_ticket_engineering_issues_76f8fc748bff` after an authorized live HTTP 200 inspection. Ten real validation checks PASS; the authorized human later approved the exact manifest/source/report, with a matching persistent audit event.
- Live approved network GETs through DevRev returned the exact DEMO-101 and DEMO-102 source-backed results; DEMO-403 stayed denied. Saved Computer responses and full positive source-response hashes were inspected. Earlier upstream failure remains recorded.
- Web-first product planning and a minimal read-only synthetic evidence view are present; actual Chrome checks, evidence reconciliation, and two timed technical walkthroughs PASS. The broader interactive workspace and hosted access remain unimplemented.
- Live automatic reuse failed safely on a null model-selected capability ID. Schema/prompt/context correction passes 31 local checks; live fixed rerun is pending server restart.
- Public-schema Enterprise-Bench handoff and an inactive output contract are prepared; no authorized records/API are available. Denied inspection/execution performs no HTTP request in the focused checks.
- AWS service/proxy examples and rollback gates are prepared and statically checked. No EC2 resources, IAM permissions, account tier, or working DevRev connection were changed.
- Invited teammate reused the same approved capability with DEMO-102 and DEMO-403. Fresh real network receipts match the supplied Computer responses, and the user confirms their own Bench-07 login. Named identity was not supplied; the shared bearer does not identify an individual.

### Still unverified

- Organizer-approved records/API and a supported business relationship.
- Successful live agent selection of an existing capability after the tested fix, and live mapping repair; real generation, validation, human approval, and recovered answer are proven for the single synthetic API.
- EC2 runtime role authorization and actual Linux hosting; eligibility and launch DryRun now pass, but no resources exist. Local-profile invocation is proven.
- Hosted web authentication, approval, state persistence, and restart behavior.
- Per-user source authorization and independently observed named Computer identity. D6 passes for the user-confirmed invited teammate within the shared synthetic-source scope.
- AWS migration, hosted URL, owner-approved 24-hour/$5 budget, and infrastructure/access approval. Current $120 credits and Ohio price inputs were verified read-only.
- Sponsor acceptance of the hosting fallback; AWS deployment does not establish Akamai-track eligibility.

### Primary references

- [Enterprise-Bench schema](https://github.com/devrev/enterprise-bench/blob/main/docs/data-schema.md)
- [Strands structured output](https://strandsagents.com/docs/user-guide/sdk/agents/structured-output/)
- [Strands lifecycle limits](https://strandsagents.com/docs/user-guide/sdk/agents/lifecycle-controls/)
- [Strands Bedrock provider](https://strandsagents.com/docs/user-guide/sdk/model-providers/amazon-bedrock/)
- [AWS inference profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html)
- [FastAPI templates](https://fastapi.tiangolo.com/advanced/templates/)
- [Caddy authenticated access](https://caddyserver.com/docs/caddyfile/directives/basic_auth)
- [Cloudflare Quick Tunnel limitations](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)

The synthetic proof includes another authorized person's reuse and timed technical browser execution. Fixed automatic reuse, spoken stage delivery, official-data integration, and hosted access still require their own executed acceptance evidence.

## GitHub checkpoint preparation — October 10, 2026

Target: `https://github.com/ayyagarisujanreddy123/Hackmidwest.git`. The owner authorized publication and commits/pushes at each completed checkpoint.

| Executed check | Actual result |
|---|---|
| `git init -b main` in this workspace | FAIL / environment blocker: writing `.git` returned `Operation not permitted` |
| Git remote inspection using `git ls-remote` | FAIL / environment blocker: `Could not resolve host: github.com` |
| GitHub CLI repository inspection | FAIL / environment blocker: unable to connect to `api.github.com` |
| Authenticated GitHub browser inspection | PASS: the requested repository exists, is public, and initially has no commits |
| Credential-pattern scan of publication candidates | PASS: no matches for AWS/GitHub keys, private keys, long bearer credentials, credential assignments, or credential-bearing URLs; heuristic scan is not a full security audit |
| Backend verification continuity | PASS: all four retained Python files match the SHA-256 hashes in the executed post-cleanup MCP receipt; no backend code changed for this checkpoint |
| Publication whitespace checks | Initial FAIL: eleven Markdown hard breaks and one trailing log blank line; converted hard breaks to Markdown backslashes and trimmed the final empty log line, then all 30 candidate files passed `git diff --no-index --check` against `/dev/null` |

Added the project entry-point README and checkpoint policy; expanded ignores for local AWS/agent configuration. Existing `AGENTS.md` remains unchanged. The working server and tunnel were not restarted. Local Git connection and publication require separate confirmation of their actual outcomes; preparation alone does not prove a successful push.

## Mac-hosted Yahoo Finance MCP — October 11, 2026

**Scope:** complete the user-requested yfinance MCP connector in DevRev Computer, with the owner's Mac running the server. The original ContextForge server on port 8000 and its connection are preserved. Finance uses a separate loopback server on port 8003, private bearer secret, and Cloudflare HTTPS tunnel. Yahoo Finance is a separate public-data integration, not Enterprise-Bench event evidence.

Executed between **06:15 and 06:26 UTC** with Python 3.12, `mcp==1.30.0`, `yfinance==1.7.0`, `uvicorn==0.54.0`, and `starlette==1.7.0`. `pip check` reports no broken requirements. Runtime receipts include source-file SHA-256 build identifiers and real provider response hashes; they are private under `validation_logs/`.

| ID | Expected | Observed | Result / evidence |
| --- | --- | --- | --- |
| F1 | Diagnose empty news before changing the adapter | Ticker news returned 0 raw records for counts 2 and 10; Search news returned 2 flat records with title, publisher, link, and provider timestamp | PASS: `finance-news-diagnostic-20261011T061517250590Z.json` |
| F2 | Guard the actual news format and security boundaries | Regression tests first failed on flat news and nullable provider objects. After the fix, all 33 offline tests pass, including isolated Host/port validation and private token-file restrictions | PASS: `.venv/bin/python -m unittest discover -s tests -q`; fixtures are invented data |
| F3 | All six tools return real provider data and references through authenticated MCP | Missing/incorrect tokens reject with 401; initialize/discovery and all six AAPL calls pass. News contains actual publishers, UTC publication times, and article URLs | PASS: `finance-readiness-20261011T061655574467Z.json`; all six response hashes verified. Current build/complete-check evidence: `finance-readiness-20261011T062239123456Z.json` |
| F4 | Public HTTPS transport works with the real MCP Python client | 13 checks pass: missing/incorrect token rejection, initialize, exact tool inventory, ping, all six finance calls, rejected symbol URL, and out-of-range news limit | PASS: `finance-mac-https-20261011T062132784881Z.json`; `devrev_call=false` |
| F5 | Background services preserve credential and original server | Both per-user LaunchAgents run. Repeated `start` preserves loaded processes; after hardening the private file reader, only the new finance server was restarted. HTTPS ping/inventory and original ContextForge ping still pass; generated token is absent from publication candidates | PASS: `finance-mac-continuity-20261011T062641329043Z.json` |
| F6 | DevRev custom connector authenticates and discovers the tools | Earlier retries returned 401 with correctly formatted Bearer headers. Resync still selected the old October 10 connection. Selecting the saved October 11, 2:02 AM finance connection fixed discovery at 07:06:57 UTC: actual DevRev requests returned 200/202 and matched the server secret. The owner then finished personal Connect; Computer shows yFinance connected! and eight discovered tools | PASS: `finance-devrev-resync-20261011T070657Z.json`, `finance-devrev-live-20261011T071130Z.json`; earlier FAIL receipts retained |
| F7 | Computer invokes all six tools live and rejects invalid inputs | Fresh Computer session returns ping plus six successful AAPL finance results, with retrieval times and references. Symbol URL and news limit 11 reached the connector and returned `string_pattern_mismatch` / `less_than_equal` validation errors with no valid data | PASS: `finance-devrev-live-20261011T071130Z.json`; observed Computer summaries plus correlated server HTTP metadata, not a complete raw-provider capture |
| F8 | Cleanup preserves finance auth and running transport | Temporary diagnostics removed; HTTPS initialize, eight-tool discovery, ping, missing/incorrect-token rejection, and all 33 offline tests pass. Final Computer finance ping also PASS. Token absent from publication candidates | PASS: `finance-mac-final-20261011.json` |
| F9 | Recheck the original ContextForge connection without modifying it | Local original MCP ping PASS. Original ContextForge Workflow ping in Computer was dispatched but failed with Streamable HTTP `TypeError: fetch failed` | FAIL for original remote continuity; original server, tunnel, and connector configuration unchanged. Separate from successful finance acceptance |

The review mutation inverted the token-file permission condition in memory. Four security tests caught it with two failures and one error; no repository or running-service file was mutated. Private token files reject insecure permissions, symlinks, and short secrets. Serving tools retain input bounds, explicit unavailable/error statuses, and source references. Workflow generation and approval tools are excluded from the finance server even if the workflow environment flag is set.

The Mac must remain awake and online. User agents stop on logout and start on login. A Quick Tunnel hostname changes when its process restarts; use `mac_host.py status` to obtain the current endpoint and update DevRev after a restart. JSON responses avoid Quick Tunnel's documented SSE limitation. These checks establish the executed Mac/HTTPS setup and observed DevRev finance invocation, not production uptime or a stable domain. The original ContextForge remote continuity failure remains unresolved; its working local server and configuration are preserved.

## Yahoo Finance refinements — October 11, 2026

The owner approved the refinements and additional use-case tests, then chose to keep the current URL. Scope is recorded in [FINANCE_REFINEMENTS.md](FINANCE_REFINEMENTS.md). Nine finance tools now run on the separate Mac service, with the original `ping` and `inspect_demo_capability` retained (11 total). No dependencies, bearer-secret rotation, approval changes, or original ContextForge restart were required.

| ID | Expected | Observed | Result / evidence |
| --- | --- | --- | --- |
| F10 | Date ranges, batches, CSV, cache, retries, and timeouts preserve data and enforce bounds | All 69 offline tests pass. MCP HTTP fixtures reject invalid calendar dates, ambiguous modes, URLs as symbols, excessive lists/spans/limits, and unsupported intervals. CSV fixtures cover precision, blank nulls, quoted text, formula protection, manifests, and checksums. Controlled timeouts keep actual workers at two and recover afterward | PASS: `state/mac-finance/refinement-baseline/offline-final-after-tunnel-detection.log`; fixtures are invented data |
| F11 | All nine tools and additional cases work with real Yahoo data | 23 authenticated in-process ASGI readiness checks pass, including stocks, an ETF, full-year crypto, Tokyo trading dates, a currency pair, empty stock weekends, crypto weekends, partial batch/CSV, and cache metadata | PASS: `finance-readiness-20261011T095943300761Z.json`; timestamp/build hashes in receipt, `devrev_call=false` |
| F12 | Refined tools work through the running Mac server and MCP Python SDK | 32 real loopback network checks pass at 10:27:33–38 UTC: missing/incorrect token rejection, initialize, exact 11-tool inventory, ping, all nine tools, ten additional cases, and eight invalid inputs | PASS: `finance-refined-loopback-20261011T102738278509Z.json`; actual provider responses and current source hashes, `devrev_call=false` |
| F13 | Actual provider dates and completeness match the requests | AAPL quarter returns 61 rows (Jan 2–Mar 31); SPY weekly returns 14; BTC-USD year returns 366 without truncation; Toyota `7203.T` September returns 19 Asia/Tokyo dates; EURUSD=X returns 5. AAPL weekend returns `no_data`, while BTC returns exactly Sep 12–13. Missing `ZZNOEXIST99` leaves AAPL/MSFT rows available with `partial` | PASS: same F12 receipt; no stock holiday/weekend prices are invented |
| F14 | Exported stock CSV exactly matches its MCP content | AAPL/MSFT/NVDA September export has 63 rows (21 each), 13 columns, Sep 1–30 coverage, and `truncated=false`. Saved bytes, MCP byte count, and SHA-256 match | PASS: [CSV](outputs/yfinance-refinements-20261011/AAPL_MSFT_NVDA_2026-09-01_to_2026-10-01_1d.csv); checksum and source metadata in F12 receipt. This artifact was saved from a local SDK response, not Computer Canvas |
| F15 | Diagnostics distinguish PAT problems from transport problems and preserve the original services | Private token/local auth/initialize/11-tool discovery/ping/Yahoo quote pass. Finance reload changed only MCP PID 61366→66829; tunnel PID 55599 and original ContextForge PID 32614 remained. `server.py` matches its pre-refinement hash; the private secret is absent from all 62 publication candidates. `pip check` and diff whitespace checks pass | PASS for local and preservation checks: `doctor-live-after-startup.json`, `doctor-expired-tunnel.json`, and F12 receipt; private baseline directory. Initial immediate post-reload startup failure is retained in `doctor-live.json` |
| F16 | Existing public HTTPS remains usable and DevRev sees the refined tools | Cloudflare's first `Tunnel not found` log event is 08:05:05 UTC, before finance reload at 10:00:47 UTC. The old hostname no longer resolves; `status` now correctly reports `expired`/no public endpoint. Computer's saved connector still shows the original 8-tool inventory | FAIL for current public transport; new DevRev acceptance NOT TESTED. Recreating only finance's tunnel and updating the existing connector URL awaits the owner's pending choice |

The review mutation changed the end-exclusive comparison to include the end date in a disposable copy. The range-boundary regression test caught it. Repository and running service files were not mutated. Previous failed receipts, including public transport failure, remain retained; local acceptance does not establish public HTTPS or Computer acceptance of the new tools.

## GitHub publication — October 11, 2026

The owner explicitly requested all repository changes be pushed. Earlier protected-index and network failures remain historical evidence; this session's Git access works.

| ID | Expected | Observed | Result |
| --- | --- | --- | --- |
| G1 | Preserve remote work and publish the reviewed increments | Fetch succeeded; the starting local and remote `main` were both `6ec6331`. Five focused commits were created, and a normal push advanced GitHub `main` to `397ba5d` without forcing or rewriting history | PASS: actual `git push origin main` output |
| G2 | Keep private state and credentials out of Git | All 62 publication candidates scanned; no known private finance secret or recognized credential patterns found. Tokens, environment files, runtime logs, SQLite databases, approval archives, caches, and virtual environments remained ignored | PASS: publication scan and explicit staged-path review |
| G3 | Verify the submitted code | 69 automated tests, all 24 Python syntax checks, five JSON parses, JavaScript/shell syntax, dependency consistency, and diff whitespace checks passed | PASS: executed before commit/push |

Published source checkpoints are listed in [tasks/checkpoints.md](tasks/checkpoints.md). Infrastructure remains unprovisioned, and the new finance tools still await public-tunnel repair and DevRev resync; GitHub publication does not establish either acceptance gate.
