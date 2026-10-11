# ContextForge Main Product — Implementation Tasks

**Plan:** [plan.md](plan.md). **Status:** Broader product backlog; the immediate backend proof takes priority.\
**Owners:** B = backend/deployment, A = Strands, D = web/DevRev/demo.\
The earlier prototype tests/demo were removed on request. The owner later approved a new labeled synthetic source. Verification means executed product/API/MCP operations with saved receipts; deterministic connector validation remains a product feature.

## Immediate backend checkpoint

- [x] Local-profile Nova inference and real Strands tool/result receipt verified.
- [x] Approved synthetic REST specification, records, restricted validation, and opt-in MCP proposal/dispatcher implemented.
- [x] Original MCP tools, 401 rejection, source validation, and approval boundaries executed in-process.
- [x] Fresh ContextForge Workflow baseline calls and actual Strands source inspection reach the live synthetic API (HTTP 200).
- [x] Distinguish source permission from activation; reject malformed proposal operation IDs and retain the original agent decision. Focused regression checks PASS.
- [x] Real Strands-generated connector passes live REST validation through DevRev (`20261010T235930202162Z`); candidate stays inactive.
- [x] Live dispatcher denial and synthetic HTTP 403 hold the approval/source boundaries; raw denied-input agent classification failure recorded separately.
- [x] Replace approver-label trust with explicit OS administrator policy, interactive confirmation, and persistent approval-event enforcement; 37 local acceptance checks PASS.
- [x] Human approves the exact tested version; Computer returns the previously blocked answer. Ledger, positive source hashes, changed input, and post-approval 403 verified.
- [x] Invited teammate reuses the same approved ID: fresh DEMO-102 HTTP 200 and DEMO-403 source HTTP 403; user confirms their own Bench-07 login.
- [x] One-use-case evidence walkthrough passes real Chrome inspection and technical rehearsals in 74s/70s; recorded history remains labeled.
- [x] Reproduce the live null reuse-ID failure and pass 31 local checks for the schema/prompt/context correction; existing registry and approval remain unchanged.
- [ ] Load the fix with an MCP-only restart and verify live Strands chooses the exact approved ID and answers the original question.

Use [the live runbook](../MVP_WORKFLOW.md). Existing modules remain the MVP entry point; preserve the approved local registry, source, token, and tunnel.

## Current follow-up slices

### A — Second-user DevRev reuse (D + B)

**Dependency:** Teammate's own licensed account in Bench-07 and authenticated ContextForge Workflow connection. **Scope:** Runbook and actual Computer calls.

- [x] Teammate confirms Bench-07/card visibility and reports successful connection after the server-token prompt; private setup runbook prepared.
- [x] Teammate invokes Ping/ListCapabilities; actual supplied responses match the expected baseline and approved inventory.
- [x] Same approved ID returns DEMO-102 evidence and denies DEMO-403, with fresh matching network receipts and unchanged human approval.
- [x] User confirms teammate's own Bench-07 login; exact supplied output and 17-check reconciliation saved. Alias not supplied; shared MCP bearer is not claimed as per-user source authorization.

**Verification:** D6 PASS; `devrev-reuse-completion-20261011T013038388953Z.json` references fresh 01:24–01:25 UTC execution receipts and user-attested own-account confirmation. Preserve this evidence; repeat only for rehearsal or new endpoint validation.

### B — Local demo interface (D + B)

**Dependency:** Proven synthetic backend. **Scope:** Four files; no new dependency, agent, connector type, or server approval route.

- [x] Read-only loopback view implemented for actual blocked → generated → tested → human-approved → executed evidence with labels/timestamps; verified in ASGI.
- [x] Selected-record receipt and copyable DevRev prompt agree in code; incomplete/changed evidence withholds data in executed checks.
- [x] Thirty view/privacy/configuration checks PASS after environment parity fix; working registry and six backend source hashes unchanged.
- [x] Real browser, keyboard controls, narrow layout, copy, and fresh receipt refresh verified after normal-Terminal startup; 21 native Chrome observations PASS.
- [x] Five-step walkthrough, readable times, inspectable evidence, offline error/recovery, 22 current ASGI/evidence checks, and two timed technical rehearsals PASS.
- [ ] Spoken three-minute presentation includes the one question, correctly labeled generation history, live verified automatic reuse, saved teammate proof, and source denial.

**Verification:** Completed native Chrome checks and 74s/70s technical walkthroughs at `http://127.0.0.1:8002`; receipts are recorded in `VALIDATION.md`. Spoken delivery remains pending. **Files:** `demo_view.py`, `demo_ui/index.html`, `demo_ui/workspace.css`, `demo_ui/workspace.js`.

### C — Enterprise-Bench handoff (B)

**Dependency:** Public schema for preparation; organizer authorization and records/API for actual integration.

- [x] Document public ticket → component/part → engineering-issue relationship and exact source/access inputs still needed; inactive normalized contract denies inspection/execution in five checks.
- [ ] Keep a separate contract, validation cases, and registry for an authorized replacement source; no fabricated paths/IDs/relations.
- [ ] Once access arrives, execute the existing validation suite and require fresh human approval; B1 remains pending meanwhile.

**Verification:** Read the official schema; inspect actual licensed records and API contract before writing the concrete adapter. See `ENTERPRISE_BENCH_HANDOFF.md`.

### D — Isolated AWS preparation (B + account owner)

**Dependency:** Confirmed deployment target, account eligibility, runtime identity, HTTPS access, cost cap, and explicit provisioning approval before creation.

- [x] Prepare one-VM service/HTTPS examples, ownership-aware human approval bootstrap, persistence, and rollback gates; five static boundary checks PASS, no installation/provisioning performed.
- [x] Owner selects temporary Cloudflare HTTPS on EC2; AWS read-only checks verify Free Plan/$120 credits, eligible resources, current Ohio prices, and launch DryRun. Scoped Nova-role/tunnel/package/migration preparation passes 47 local checks.
- [ ] Obtain approval for the concrete 24-hour/$5 VM/disk/IP/security-group/runtime-role proposal and scheduled stop. Actual Linux/cloudflared/systemd runtime remains NOT TESTED; Caddy is deferred.
- [ ] Stage independently; verify role-based Nova/Strands, MCP auth, source denial, new human approval, and restart before Computer cutover.
- [ ] Keep local/tunnel available until hosted and second-user tests pass; no account/IAM changes during preparation.

**Verification:** Review `deploy/README.md`; validate configuration without creating resources. Hosted gates stay NOT TESTED.

The numbered tasks below are the broader product backlog. Do not make package migration a prerequisite for these four slices.

At every completed checkpoint, review, commit, and push the relevant changes according to [checkpoints.md](checkpoints.md). Record the commit ID and actual push result; preserve unsynced changes if Git access is blocked.

## Task 1 — Establish the main package

**Owner:** B. **Dependencies:** None. **Scope:** Medium, up to five files.

Move reusable settings and MCP entry points into the proposed package incrementally; retain the existing starter entry point during migration.

**Acceptance criteria:**
- [ ] Main package has explicit configuration and a documented launch command.
- [ ] Missing bearer token prevents startup; missing approved-source settings keep workflow unavailable.
- [ ] Existing `ping`, `inspect_demo_capability`, `/mcp`, port 8000, and default inventory remain compatible.

**Verification:** Execute syntax/import checks, authenticated initialization/discovery/both tools, and missing/wrong-token 401 requests. Save results. **Likely files:** `pyproject.toml`, `contextforge/__init__.py`, `contextforge/config.py`, `contextforge/mcp_server.py`, starter `server.py`.

## Task 2 — Connect one approved source

**Owner:** B + D. **Dependencies:** Task 1, organizer/source approval. **Scope:** Medium, three to four files.

Confirm actual records, contract, permissions, and two different input IDs. Implement only the first supported read-only relationship; select a different question if the intended join is absent.

**Acceptance criteria:**
- [ ] Confirmed source returns a real approved record with identifiers and references; source credentials remain server-side.
- [ ] Generated manifests cannot select hosts, mutation methods, or undocumented routes.
- [ ] Source label and approved validation cases are explicit; no automatic synthetic fallback.

**Verification:** Execute known/changed/missing/forbidden inputs and rejected path/host/method/mapping cases; also exercise timeout, redirect, oversize, and missing-reference behavior. Save measured output. **Likely files:** `source.py`, `models.py`, `validation.py`, source configuration documentation.

## Task 3 — Persist approval and evidence

**Owner:** B. **Dependencies:** Task 2. **Scope:** Small to medium, two to three files.

Separate immutable manifest versions from validation reports, approvals, and workflow history. Both web and MCP share the registry.

**Acceptance criteria:**
- [ ] Passing validation produces an inactive candidate; only an authorized human can approve the reviewed version.
- [ ] Source URL/contract/allowlist changes invalidate prior approval; disablement blocks execution.
- [ ] Restart preserves capabilities, reports, approvals, and before/after evidence without overwriting history.

**Verification:** Attempt execution before approval, after approval, after source change, after disablement, and after restart. Verify exact inputs and source references. **Likely files:** `registry.py`, `models.py`, `cli.py`.

## Checkpoint 1 — Source and runtime

- [ ] One approved question is supported by actual evidence.
- [ ] Authorization, source boundaries, and approval gates were exercised.
- [ ] MCP baseline still works; results recorded in `VALIDATION.md`.

## Task 4 — Execute the full Strands recovery workflow

**Owner:** A + B. **Dependencies:** Task 3, existing authenticated AWS profile or approved runtime role. **Scope:** Medium, three files.

Use the verified Nova profile for gap investigation and manifest generation. Keep measured validation as a callable tool; allow one repair and record bounded usage.

**Acceptance criteria:**
- [ ] A real model run chooses reuse, access block, mapping issue, missing capability, or unsupported task from actual evidence.
- [ ] For the supported missing capability, the builder generates a manifest and calls the validator; real feedback controls success.
- [ ] Human approval followed by execution resolves the original question; budget/provider failure returns an explicit unresolved result.

**Verification:** Execute missing-capability and existing-capability cases with real Bedrock calls; inspect tool calls and reports. Exercise a mapping failure and repair without granting new permissions. **Likely files:** `workflow.py`, `validation.py`, `cli.py`.

## Task 5 — Prove DevRev capability reuse

**Owner:** D + B. **Dependencies:** Task 4. **Scope:** Small, two files plus DevRev administration.

Enable `list_capabilities` and `run_capability` once, retaining the baseline tools. Resync the actual connector if required.

**Acceptance criteria:**
- [ ] Computer discovers and invokes the stable dispatcher tools.
- [ ] Original question succeeds with the approved capability and correct source references.
- [x] A second authorized teammate invokes the same capability for the second record; evidence changes correctly. Proven in the retained starter, without package migration.

**Verification:** Save actual Computer outputs for both users/inputs; attempt an unapproved/disabled ID and verify denial. **Likely files:** `mcp_server.py`, integration instructions.

## Task 6 — Add authenticated web workflow routes

**Owner:** B. **Dependencies:** Task 4 and agreed team roles. **Scope:** Medium, four files.

Implement the proposed API, explicit authorization, CSRF checks, and a bounded asynchronous job runner. The UI and MCP use the same capability runtime.

**Acceptance criteria:**
- [ ] Operator can submit a workflow and poll actual persisted state; approver can approve only a current passing candidate.
- [ ] Browser never receives AWS credentials or `MCP_TOKEN`; unauthorized reads/actions and forged identity headers fail.
- [ ] Duplicate submissions are controlled; restart marks unfinished work interrupted without repeating model charges.

**Verification:** Execute allowed/denied role actions, invalid inputs, duplicate submission, failed validation, origin/CSRF rejection, and worker restart. Save receipts. **Likely files:** `web.py`, `jobs.py`, `models.py`, gateway configuration.

## Task 7 — Build the one-page web workspace

**Owner:** D. **Dependencies:** Task 6; backend release gates first. **Scope:** Medium, four files.

Build the question, capability-review, and answer/reuse panels from real API state, using Jinja/HTML, CSS, and small JavaScript.

**Acceptance criteria:**
- [ ] User sees the original blocked result, actual progress, measured checks, human approval, and sourced answer together.
- [ ] Failure and missing-source states are readable; approval is unavailable when checks fail or role is insufficient.
- [ ] Different-record retry and copyable DevRev instruction work without exposing secrets.

**Verification:** Use a real browser for the complete workflow, keyboard navigation, delayed/failed requests, page reload, and narrow viewport. Compare every displayed result with backend receipts. **Likely files:** `templates/workspace.html`, `static/workspace.css`, `static/workspace.js`, `web.py`.

## Checkpoint 2 — Usable product

- [ ] Complete authenticated web journey works against the approved source and real Strands.
- [ ] Computer reuse works; current integration remains available.
- [ ] No hardcoded results or removed synthetic fixtures substitute for evidence.

## Task 8 — Prepare the AWS deployment proposal

**Owner:** B + account owner. **Dependencies:** Checkpoint 2. **Scope:** Small to medium, three configuration/doc files.

Prepare service/gateway configuration and a concrete resource/cost proposal without provisioning anything.

**Acceptance criteria:**
- [x] Region, eligible instance, disk, temporary tunnel, scoped Nova permissions, current cost inputs, proposed duration, and stop/archive handling are specified.
- [x] Free Tier API confirms active Free Plan and $120 remaining credits; eligible resources and launch permission are checked read-only, with no upgrade.
- [x] Existing tunnel remains unchanged; isolated staging and rollback are documented.
- [ ] Owner approves infrastructure/access/budget before creation; real Linux installation still needs execution.

**Verification:** Validate configuration syntax and dependency installation; account owner reviews the concrete proposal and explicitly approves creation. **Likely files:** `deploy/README.md`, service units, HTTPS gateway config.

## Task 9 — Deploy and migrate after approval

**Owner:** B + D. **Dependencies:** Task 8 and explicit infrastructure/access approval. **Scope:** Small, two to three files plus authorized AWS actions.

Deploy to the approved EC2 environment, verify role-based inference and persisted state, then change DevRev's endpoint.

**Acceptance criteria:**
- [ ] Authenticated HTTPS web and MCP work; unauthorized requests fail.
- [ ] Real Strands generation/validation and recovered answer work from the hosted worker, including after restart.
- [ ] Computer uses the AWS endpoint successfully; original integration can be restored if migration fails.

**Verification:** Execute remote authenticated/unauthorized requests, hosted workflow, restart, and real Computer calls before declaring migration complete. Record endpoint/build and budget status. **Likely files:** deployment configuration and runbook.

## Task 10 — Rehearse and record the demonstration

**Owner:** All. **Dependencies:** Task 9; approved records, both users, and sponsor requirements confirmed. **Scope:** Small, documentation/evidence only.

Follow the timed web-first story in the plan. Show a fresh live recovery, then a second record in Computer.

**Acceptance criteria:**
- [ ] Full demonstration finishes within three minutes using actual calls.
- [ ] Both inputs and their source relationships are verified; replay/fallback material is labeled.
- [ ] Limits, actual sponsor usage, AWS shutdown owner, and final PASS/FAIL results are recorded honestly.

**Verification:** Rehearse twice after the final code/deployment change; record actual timing and failures. **Likely files:** `VALIDATION.md`, demo runbook, sanitized receipts.

## Checkpoint 3 — Ready to demonstrate

- [ ] All product release gates in `plan.md` pass in the deployed environment.
- [x] A second teammate successfully reuses the approved capability within the shared synthetic-source scope.
- [ ] Costs and post-event shutdown have an owner; no secrets are visible.
