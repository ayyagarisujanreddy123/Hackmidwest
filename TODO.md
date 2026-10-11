# ContextForge — Progress and Next Work

**Active priority:** [Yahoo Finance MCP for DevRev Computer](FINANCE_MCP.md). The owner paused further ContextForge product work and AWS deployment. Preserve the working server, Strands workflow, approved connector, and DevRev connection. Do not restart the existing MCP server for finance testing.

## Yahoo Finance connector checkpoint

- [x] Implement six bounded, read-only Yahoo Finance tools with provider timestamps, source references, and explicit unavailable/error responses.
- [x] Add opt-in finance registration without changing the existing bearer authentication or workflow approval requirement.
- [x] Verify installed finance dependencies and `pip check`; preserve MCP 1.30.0 and Strands 1.59.0.
- [x] Execute 25 offline tool/MCP/SDK tests, including a temporary-registry check that finance cannot approve a generated connector.
- [x] Add `check_finance.py` to exercise real provider calls through authenticated in-process MCP and save private receipts without restarting services.
- [x] Record the restricted-session real quote failure (`DNSError`); no fabricated fallback data.
- [x] Inspect the owner's new Terminal receipt `finance-readiness-20261011T044328614323Z.json`: five tools return real data, all six response hashes match, authentication/discovery PASS; overall FAIL because news returns `no_data`.
- [x] Diagnose the real empty news response: Ticker returns zero records; Search returns two flat records. Saved live response-shape evidence before changing the adapter.
- [x] Resolve news with the documented read-only Search API and execute complete six-tool real-provider readiness PASS; 33 offline tests also PASS.
- [x] Start an isolated finance-only server on the owner's Mac, port 8003, with a separate private token and HTTPS tunnel; 13 live HTTPS MCP SDK checks PASS. LaunchAgents and operational commands are implemented.
- [x] Resolve the stale DevRev resync connection binding, finish personal yFinance activation, and execute live ping, all six tools, and two rejected-input checks through Computer; save sanitized receipts.
- [x] Recheck the unchanged ContextForge connection: local MCP ping PASS, original Computer connector ping FAIL with a transport error. Preserve its server, tunnel, and connector configuration; record this separate unresolved failure.
- [x] Review, commit, and push the completed workflow, demo, finance, and deployment-preparation increments; private credentials, runtime state, and receipts remain ignored.

## Yahoo Finance refinements — October 11, 2026

- [x] Implement validated date ranges (start inclusive, end exclusive, maximum 366 days) and complete bounded full-year history by default.
- [x] Add multi-symbol history and direct CSV content for 1–5 tickers, with per-symbol outcomes, dates, timezone, null handling, precision, and checksum.
- [x] Add a 30-second/128-entry success cache, one transient retry, rate-limit metadata, and two provider workers that remain bounded after timeouts.
- [x] Add read-only `mac_host.py doctor`, finance-only `reload`, and expired-tunnel detection without changing authentication or the token.
- [x] Execute all 69 offline tests and 23 authenticated in-process real-provider checks across all nine finance tools and additional market/date/error cases.
- [x] Execute 32 real loopback network/MCP SDK checks against the running Mac service; verify the actual 63-row AAPL/MSFT/NVDA September CSV and its checksum.
- [x] Reload only finance; local authenticated discovery shows 11 tools and Yahoo quote succeeds. Original ContextForge process and finance tunnel process preserved.
- [x] Diagnose independent Quick Tunnel expiration: its old hostname no longer resolves and the tunnel log reports `Tunnel not found` from 08:05:05 UTC, before finance reload.
- [ ] Receive the owner's choice on replacing the expired temporary finance URL; retain the current setup until approval.
- [ ] Verify the refined tools through real public HTTPS and resync the existing yFinance connector without changing its token or permissions.
- [ ] Execute new range and CSV tools in DevRev Computer and verify the resulting Canvas CSV against its MCP checksum.

## Preserved ContextForge status

**Status:** Synthetic backend workflow, second-user reuse (D6), browser checks, and timed technical walkthroughs PASS. Original capability/approval unchanged. Automatic Strands reuse exposed a null capability-ID failure; the fix passes 31 local checks and awaits server restart/live rerun. Enterprise-Bench access and AWS hosting remain pending.\
**Product decision:** Web workspace first, followed by DevRev Computer reuse.\
**Detailed plan:** [tasks/plan.md](tasks/plan.md). **Ordered implementation tasks:** [tasks/todo.md](tasks/todo.md). **Actual results:** [VALIDATION.md](VALIDATION.md).

**Version control:** Git access is working in the October 11 session. Five reviewed workflow/demo/finance/deployment commits were pushed to `origin/main` through `397ba5d`. Published checkpoints and verification are recorded in [tasks/checkpoints.md](tasks/checkpoints.md); private runtime state and receipts remain outside Git.

## Completed foundation

- [x] Inspect the supplied extracted MCP starter and project documents.
- [x] Run original local MCP initialization, discovery, and both tools; receipt saved.
- [x] Require `MCP_TOKEN`, pure ASGI bearer authentication, HTTP 401 rejection, and constant-time comparison.
- [x] Preserve `ping`, `inspect_demo_capability`, `/mcp`, and port 8000.
- [x] Connect authenticated MCP to DevRev Computer through Cloudflare Tunnel; both tools work **per the user's report**.
- [x] Install Strands 1.59.0; confirm MCP stays at 1.30.0 and dependency checks pass.
- [x] Execute Nova Micro in the AWS Console; exact probe response received.
- [x] Execute real Strands → Nova → tool → observed result; one tool call, matching fresh marker, 1,531 total tokens.
- [x] Execute 22 local prototype checks before removal, including authenticated MCP, restricted REST execution, approval, changed inputs, and scripted workflow control.
- [x] Remove standalone tests, smoke client, mock REST server, synthetic fixtures, and their cached bytecode as requested.
- [x] Retain backend executor, registry, and Strands workflow; require explicit approved-source configuration instead of a synthetic fallback.
- [x] Execute 13 post-cleanup checks: retained syntax, startup/configuration gates, six 401 checks, authenticated MCP initialization, exact tool inventory, and both original responses.
- [x] Write the detailed web access, architecture, screen flow, deployment, team tasks, and three-minute demonstration plan.
- [x] Receive explicit approval for the new labeled synthetic source; document one GET API and two invented records.
- [x] Verify local AWS catalog, actual Nova Micro inference, and one Strands tool/result call from receipt `workflow-20261010T232156483219Z.json`.
- [x] Implement opt-in `propose_connector`, restricted generated manifests, real REST validation, and CLI-only human approval.
- [x] Execute eight synthetic-source checks and 31 MCP/runtime acceptance checks, including unchanged original tools, 401 rejection, approval persistence, changed-source denial, and disablement.
- [x] Recheck Ping, InspectDemoCapability, and ListCapabilities through the active ContextForge Workflow connector.
- [x] Verify live Strands inspection of the documented, owner-approved synthetic source: HTTP 200 for `DEMO-101`.
- [x] Separate source-inspection authorization from connector activation; missing/revoked source authorization and 401/403 still block generation.
- [x] Require a non-null verified operation ID for proposals; preserve the agent decision; execute 14 focused follow-up checks.
- [x] Rerun the exact original DEMO-101 question through DevRev: real Strands generation and ten distinct validation checks PASS (`20261010T235930202162Z`).
- [x] Audit the shared registry read-only: exact generated manifest and ID, status `tested`, `approved_by=null`, unapproved execution denied.
- [x] Execute live DEMO-403 denial through DevRev: actual HTTP 403 forces `permission_block`; no builder/validator, no new candidate.
- [x] Verify live RunCapability rejects the actual tested candidate with `approval_required`; legacy inspection response unchanged.
- [x] Reproduce the arbitrary-approver-label weakness in a temporary registry and replace it with OS identity, explicit administrator policy, and human confirmation.
- [x] Execute 37 approval/MCP/source acceptance checks in temporary registries; unauthorized/headless/stale approvals and unaudited activation denied, original auth/tools preserved, GET execution receipts verified.
- [x] Verify real administrator setup and human approval for `get_ticket_engineering_issues_76f8fc748bff`; unconfirmed attempts remain blocked and recorded.
- [x] Verify live approved DevRev/MCP network GETs for DEMO-101 and DEMO-102, exact source-response hashes, issue titles, and references; original blocked question is answered.
- [x] Verify DEMO-403 remains forbidden after approval, with real source HTTP 403 and no disclosed records.
- [x] Reconcile saved Computer outputs, approval ledger, manifest/source/report hashes, and receipts; retain the earlier `upstream_error` failure.
- [x] Guide teammate connection through the visible Bench-07 connector and private server-token field; successful connection user-reported.
- [x] Match reported teammate DEMO-102/DEMO-403 tool outputs to fresh 01:24–01:25 UTC MCP network receipts; exact source-body hash and denial verified, original approval unchanged. Seventeen reconciliation checks PASS.
- [x] Complete D6 using the user's explicit confirmation of the invited teammate's own Bench-07 login; caller identity is user-attested, not inferred from the shared bearer.
- [x] Implement the minimal read-only synthetic evidence view; thirty focused view/privacy/configuration checks PASS, including matching backend environment names.
- [x] Prepare Enterprise-Bench handoff and inactive output contract; five checks confirm no routes, no inspection authorization, and no HTTP execution.
- [x] Prepare uninstalled AWS/systemd/Caddy examples and rollback plan; five static boundary checks PASS, actual hosted runtime NOT TESTED.
- [x] Polish the five-step evidence walkthrough; execute 21 native Chrome checks, narrow layout, keyboard/copy controls, offline recovery, and fresh live receipt refresh.
- [x] Execute 22 current view/evidence checks and two timed technical walkthroughs (74s and 70s); recorded generation remains labeled and live DEMO-101 calls produce new receipts.
- [x] Reproduce live automatic reuse failure, require an explicit model-selected approved ID, bind the initial result to its ID, and pass 31 local regressions without modifying approval or source permissions.
- [ ] Restart only MCP and rerun the exact DEMO-101 question through live Strands/Computer; require `REUSED`, the actual approved ID, and fresh source-backed results.

## Paused ContextForge implementation sequence

The tested local version remains available. The sequence below is retained for a future resumption; it is not authorization to restart or deploy during finance testing. Follow [MVP_WORKFLOW.md](MVP_WORKFLOW.md) and the ordered follow-up tasks in [tasks/todo.md](tasks/todo.md) when the owner resumes this work.

1. **Automatic one-question flow:** load the tested reuse-ID fix with an MCP-only restart, then execute the exact question live through `ProposeConnector`. Stop on model/permission errors; never substitute an ID into the agent's decision. Preserve the working connector and approval.
2. **One-use-case demo:** use support-ticket → engineering-issue lookup throughout the [three-minute flow](MVP_WORKFLOW.md#minimal-web-first-demonstration). The evidence view and technical execution are already browser-tested. Rehearse spoken delivery with labeled recorded discovery, a live question-driven call, teammate reuse evidence, and continued denial. A fresh generation replay needs a separate registry and explicit human approval.
3. **AWS deployment is paused:** [the concrete EC2/tunnel proposal](deploy/README.md) is retained. AWS verified $120 remaining credits, Free Plan/instance eligibility, Ohio prices, and launch permission via DryRun. The private packaging/migration/MCP checks pass 47 local assertions. Future creation still requires explicit approval for the 24-hour/$5 resource and restricted-role proposal; hosted Linux/Bedrock/MCP remain NOT TESTED. Keep the existing DevRev URL and local fallback.
4. **Enterprise-Bench:** use [the prepared handoff](ENTERPRISE_BENCH_HANDOFF.md) when organizer-approved records/API arrive. Actual integration remains BLOCKED; use an isolated source/registry, real validation, and fresh human approval. Continue existing labeled synthetic development meanwhile.
5. Save each actual result and checkpoint the completed work; defer package migration and additional features.

Later: improve Nova's raw 403 classification; deterministic source denial is already enforced and must remain authoritative.

## Pending prerequisites

- [x] Owner-approved synthetic source and documented relationship for the proof; Enterprise-Bench remains unavailable.
- [x] Local `contextforge` AWS profile and `us-east-2` real Nova/Strands invocation verified; no EC2 role created.
- [x] Live model-generated connector passes measured validation through DevRev.
- [x] Human explicitly approves the exact tested generated connector; receipt and approval ledger verified.
- [x] Computer invokes the new tools and returns the recovered answer; actual network receipts and saved UI verified.
- [x] Teammate confirms Bench-07/card visibility and reports successful MCP connection.
- [x] Reported Ping/ListCapabilities match expected responses; fresh actual MCP RunCapability requests and results independently verified.
- [x] User confirms invited teammate's own Computer login for D6; individual identity is not carried by the shared bearer.
- [ ] Organizer-approved Enterprise-Bench records/API and allowed read scope confirmed; public schema alone is insufficient.
- [ ] Team web identities and authorized approver roles.
- [x] Select temporary Cloudflare HTTPS on EC2; verify active Free Plan/$120 credits, eligible Ubuntu/t3.small, Ohio VM/disk/Nova prices, and EC2 launch permission via DryRun without provisioning.
- [x] Prepare restricted EC2 role policy, MCP-only tunnel unit, private checksummed bundle, unchanged approval archive, and inactive manifest revalidation; 47 local checks PASS.
- [ ] Owner approves one VM/disk/IP/security group, the scoped Nova runtime role, 24-hour window, $5 credit ceiling, and scheduled stop before provisioning.
- [ ] Deploy independently; execute Linux service startup, role-based Nova/Strands, fresh human approval, remote MCP/RunCapability, denial, and restart checks; provide the verified HTTPS URL.
- [x] DevRev discovers/invokes live proposal and inventory tools.
- [x] Approved dispatcher execution, distinct input results, and continued source denial.
- [x] Second-teammate reuse (D6) for the shared synthetic source; fresh actual results and user-attested identity recorded.
- [ ] Sponsor acceptance of approved evidence and the AWS hosting fallback; do not claim Akamai usage.

## Working-server command

Keep the existing server and tunnel running. If a restart is needed, from the starter folder in normal Terminal use the existing environment and enter the same secret privately:

```zsh
read -rs 'MCP_TOKEN?ContextForge token (hidden): '
export MCP_TOKEN
source demo/env.zsh
export CONTEXTFORGE_ENABLE_WORKFLOW=1
.venv/bin/python server.py
```

This command retains the tested workflow mode and is preserved for a future authorized restart. **Do not restart now:** the owner explicitly requested that the working server stay running during finance validation. The reuse-ID fix still awaits a future live rerun. Keep the source on port 8001, demo view on 8002, and current tunnel running. Infrastructure, account tier, and AWS permissions remain unchanged.
