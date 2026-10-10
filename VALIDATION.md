# ContextForge — Validation & Go/No-Go Criteria

**Purpose:** Record evidence that the system *actually works*. Do not mark a case PASS until it has been run in the team's environment.\
**Current state (2026-10-10 22:48 UTC):** The user reports both authenticated MCP tools working in DevRev through Cloudflare Tunnel. Executed AWS Console and CloudShell checks prove Nova Micro access and a real Strands tool round trip. Twenty-two local prototype checks passed before the requested removal of test scripts and synthetic demo files; 13 post-cleanup checks passed for retained syntax, configuration gates, unauthorized rejection, and the original MCP tools. The full model-generated business connector, approved-data answer, web workspace, EC2 deployment, and second-user reuse remain unverified. Planning v0.1 is in [tasks/plan.md](tasks/plan.md).

## 1. Validation definitions

- **PASS:** Real operation executed; observed output matches an explicit expected result. Save a sanitized screenshot, log or receipt.
- **FAIL:** Real operation executed; output contradicted expectation or could not complete. Record error and fix owner.
- **BLOCKED:** Prerequisite, permission, source data or service unavailable; do not call it PASS.
- **NOT TESTED:** No execution evidence yet; do not infer success from screenshots or code existence.
- **CONDITIONAL PASS:** Allowed only for a clearly scoped limitation, written next to the result; not a substitute for the primary integration test.

Record results with UTC or local timezone, deployed build/version, hostname, test input reference, expected, observed, and tester. **Never record actual PATs, bearer secrets or customer data.**

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
| A8 | **Invoke** `ping` from DevRev Computer | Computer shows exact `pong - ContextForge MCP tool is reachable` from tool output | PASS (user-reported) — registered connector invokes the expected tools |
| A9 | Invoke `inspect_demo_capability` from Computer | Result includes `capability: connectivity-test`, `status: working`, `sample_records: 0` | PASS (user-reported) — registered connector invokes the expected tools |
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

**Pass:** HTTP 401 with `WWW-Authenticate: Bearer`. This request deliberately omits credentials. Use the authenticated SDK smoke client below to validate initialization, discovery, and invocation.

### A3/A4/A5 — Current verification

The standalone `connectivity_smoke.py` client was removed after the AWS check at the user's request. Historical commands in the run log refer to the earlier build, not current launch instructions.

The post-cleanup receipt records executed initialization, exact discovery, and both tool responses through the real MCP SDK and in-process ASGI. Keep the working normal-Terminal server/tunnel running. Real Computer invocation is user-reported; new dispatcher calls and public unauthorized rejection require their own receipts.

### Public tunnel caveat

The included starter uses `json_response=True` and `stateless_http=True`, and its TransportSecuritySettings allow `localhost:8000` and `127.0.0.1:8000`. The documented quick-tunnel command passes an origin Host header to match that allowlist. **Cloudflare Quick Tunnels do not support Server-Sent Events**; DevRev may need behavior that the tunnel does not carry. If A3/A5 pass locally but A8 fails, check the hosted transport, not just your tool code. The current tunnel works per the user. Keep it until an approved AWS replacement passes actual Computer calls; Akamai is currently unavailable.

## 4. Gate B — Source integrity and safe connector behavior

| ID | Test | Expected outcome | Status |
|---|---|---|---|
| B1 | Query known approved Enterprise-Bench record | Correct record ID and source reference returned | NOT TESTED |
| B2 | Query nonexistent record | `not_found` or explicitly empty, not fabricated data | NOT TESTED |
| B3 | Query ambiguous identifier | Ask to disambiguate or report ambiguity, not guess | NOT TESTED |
| B4 | Attempt unauthorized record/operation | Server returns denial regardless of agent prompt | NOT TESTED |
| B5 | Ask for an unlisted outbound URL/host | Executor refuses; no arbitrary requests/SSRF | NOT TESTED |
| B6 | Attempt non-GET mutation through generated adapter | Rejected by deterministic allowlist | NOT TESTED |
| B7 | Simulate slow or failed upstream API | Timeout/error visible; no fabricated success | NOT TESTED |
| B8 | Return record with missing evidence fields | Output marks source missing and withholds source-backed claim | NOT TESTED |
| B9 | Expose secure endpoint publicly | Authenticated HTTPS works; unauthenticated access denied | NOT TESTED |
| B10 | Change capability mapping version | Prior version and test record remain inspectable | NOT TESTED |

**Gate B passes only if B1, B2, B4, B5, B6 and B9 pass.** Others are strongly recommended. The current starter requires bearer authentication even for the content-free Gate A probe; public access must use HTTPS.

## 5. Gate C — Agent behavior and generator correctness

| ID | Scenario | Expected behavior | Status |
|---|---|---|---|
| C1 | Task already solvable using an existing tool | Coordinator chooses reuse, not redundant generation | NOT TESTED |
| C2 | Task blocked only by missing permission | Coordinator requests access, not privilege escalation | NOT TESTED |
| C3 | Task blocked by incorrect field mapping | Coordinator proposes a mapping fix | NOT TESTED |
| C4 | Task lacks a necessary read-only operation, available in approved API | Builder proposes valid typed adapter manifest | NOT TESTED |
| C5 | API operation missing from allowed specification | Builder refuses to invent endpoint | NOT TESTED |
| C6 | Proposed adapter maps wrong output field | Actual test fails with traceable mismatch | PASS in pre-cleanup synthetic prototype; approved source NOT TESTED |
| C7 | Failed mapping test returned to Strands | Agent proposes a bounded correction; rerun measured test | NOT TESTED |
| C8 | Model tries to activate an unapproved adapter | Server refuses activation or execution | PASS in pre-cleanup synthetic MCP/runtime checks; live agent scenario NOT TESTED |
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
| D1 | Run one real enterprise question before capability activation | Missing operation is correctly described and logged | NOT TESTED |
| D2 | Analyze need using actual approved feedback/task evidence | Missing context type supported by cited records | NOT TESTED |
| D3 | Generate and test proposed operation | All mandatory tests produce real reports | NOT TESTED |
| D4 | Approve operation and invoke via stable MCP tools | Operation works; requires no arbitrary prompt bypass | NOT TESTED |
| D5 | Repeat original Computer question | Returns a source-backed, relevant answer | NOT TESTED |
| D6 | Second authorized teammate uses different input | Same capability works for them within permissions | NOT TESTED |
| D7 | Approved hosted system serves real workflow | Can inspect hosted agent/tool/database requests | NOT TESTED — AWS fallback planned; Akamai unavailable; provisioning needs approval |
| D8 | Strands handles tool feedback | Logs show model→tool→result→revision or decision | PASS for data-free Nova compatibility; business generation/repair NOT TESTED |
| D9 | Revoke or disable capability | Further calls are denied; previous activity remains auditable | Denial PASS in pre-cleanup prototype; production audit history NOT TESTED |
| D10 | Three-minute live demonstration | Repeatable within time; no hidden pre-recorded result passed off as live | NOT TESTED |

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

- Four reusable Python backend modules remain; standalone tests and synthetic demo files were removed on request.
- MCP 1.30.0 and Strands 1.59.0 coexist without reported dependency conflicts; default authenticated MCP works in post-cleanup ASGI checks.
- User reports both baseline tools working in DevRev through Cloudflare Tunnel.
- Nova Micro invocation and a real Strands tool/result cycle executed successfully in the AWS Console/CloudShell.
- Web-first product planning v0.1 is documented in `tasks/plan.md`; no web application or EC2 instance was built in this turn.

### Still unverified

- Organizer-approved records/API and a supported business relationship.
- Full real Strands gap detection, generated connector, repair, and recovered enterprise answer.
- Worker AWS credentials outside CloudShell; EC2 role and hosting eligibility.
- Hosted web authentication, approval, state persistence, and restart behavior.
- New stable dispatcher discovery/invocation and second-user DevRev reuse.
- AWS migration, budget, hostname, and infrastructure approval.
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

Complete product validation still requires another authorized person to use an approved capability in Computer to answer a source-backed question that the initial supported inventory could not answer.

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
