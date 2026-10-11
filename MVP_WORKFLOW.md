# ContextForge Live Backend Proof

Use the original task: **Find the engineering issues related to a customer's support ticket using its ticket ID.** Input: `DEMO-101`.

## One use case and the automation contract

The project vision is project-aware AWS agents that turn a missing context/API capability into a reusable MCP capability. This demo proves one bounded case: **a support engineer needs the engineering issue behind a support ticket**. Use this exact question throughout:

> Which engineering issue is linked to support ticket DEMO-101? Include its title and source references.

The administrator configures one approved API specification and read-only scope once. The user supplies the question and ticket ID. Strands checks the inventory, inspects authorized source access when needed, generates a restricted manifest, and invokes real validation. The generated capability stays inactive until an authorized human approves its exact tested version. Execution then returns actual API evidence and references. The same gateway exposes the capability to Computer; users do not write adapter code or configure another MCP server for each question.

If an approved capability already answers the question, Strands should select its exact ID and reuse it. If access is absent or denied, it must block. **Current live reuse regression:** the model omitted that ID; a 31-check local schema/prompt fix awaits MCP restart and live rerun. Keep the existing approved connector; do not reset its registry to manufacture a fresh gap.

For a genuinely fresh generation demonstration, prepare an isolated registry/endpoint, invoke the same question against its empty inventory, require actual source/validator receipts, and obtain explicit human approval before execution. That replay is not yet tested. The current polished demonstration instead labels the original executed generation/approval as history and performs execution live.

All records are invented demonstration data labeled `SYNTHETIC_CONTEXTFORGE_DEMO_V1`. They are not Enterprise-Bench or customer records. The approved OpenAPI contract is [`demo/source_contract.json`](contextforge_mcp_starter/demo/source_contract.json); it authorizes read-only inspection and allows only `GET /tickets/{ticket_id}/engineering-issues`. Source inspection/generation permission is independent of human connector activation. `DEMO-403` is a simulated forbidden response; `DEMO-404` is missing.

**Executed checkpoint:** Run `20261010T235930202162Z` generated `get_ticket_engineering_issues_76f8fc748bff`; ten checks PASS, initially inactive. The trusted human approved the exact version at 00:34:09 UTC on October 11. Actual Computer/MCP network GETs recovered DEMO-101 at 00:41:51 and returned DEMO-102/denied DEMO-403 at 00:43:14. Earlier failures remain in [actual results](VALIDATION.md). The registry is now `approved`; do not regenerate or reapprove this candidate just to show the demonstration.

**Second-user checkpoint:** The invited teammate reused the same approved capability: fresh DEMO-102 HTTP 200 at 01:24:50 UTC and DEMO-403 source HTTP 403 at 01:25:20 UTC. Seventeen read-only reconciliation checks pass; the user confirmed their own Bench-07 login. D6 PASS, scoped to the shared synthetic source. No generation or approval was repeated.

## Start the source and enable the workflow

In a new normal Terminal, keep this process running:

```zsh
cd /Applications/Projects/Hackmidwest/contextforge_mcp_starter
.venv/bin/python synthetic_source.py
```

In the existing MCP Terminal, stop only the Python server with Ctrl+C, then:

```zsh
cd /Applications/Projects/Hackmidwest/contextforge_mcp_starter
source demo/env.zsh
export CONTEXTFORGE_ENABLE_WORKFLOW=1
.venv/bin/python server.py
```

These startup commands are for stopped services; keep currently working processes running. Retain the existing `MCP_TOKEN` and Cloudflare Tunnel. The MCP endpoint remains `/mcp`, port 8000. The source stays on loopback port 8001. If startup requires the token, enter the same secret privately using the backend README; never share it in chat or logs.

## Verify before generating

Have DevRev Computer use **ContextForge Workflow** to execute Ping and InspectDemoCapability. Require their actual unchanged responses. The older ContextForge Test connector had a stale transport failure. Opt-in tools are `list_capabilities`, `propose_connector`, and `run_capability`.

Execute `list_capabilities`. On a fresh registry it contains no approved capabilities. Execute `run_capability` with ID `trace_ticket_issues` and inputs `{"ticket_id":"DEMO-101"}`; save the actual blocked result. If an approved capability already exists, report reuse instead of staging a false blocker.

## Generate and review

The demo candidate is already generated and approved. The instructions below reproduce generation only in a separately configured registry; generating the same ID in the working registry can reset its approval. Use the saved, explicitly labeled generation receipt for the current demonstration.

Ask Computer to invoke `propose_connector` with the original question and `ticket_id="DEMO-101"`. It uses Nova Micro through Strands for gap detection and manifest generation; its validator performs actual REST requests and negative checks. Calls are bounded, with one repair attempt and no automatic paid retries.

Inspect the newly saved `validation_logs/workflow-*.json`: real `execution_mode="strands"`, source authorization and actual HTTP inspection, `agent_gap` and enforced `gap`, generated manifest, tool validation reports, final PASS, and an unapproved execution denial. A proposal must name the inspected allowlisted operation. The expected successful proposal status is `TESTED_REQUIRES_APPROVAL`. Failure or missing tool feedback leaves the task unresolved. Never widen permissions to repair malformed model output.

If Computer cannot invoke the new proposal tool, diagnose separately with:

```zsh
source demo/env.zsh
.venv/bin/python strands_workflow.py propose \
  --question "Find the engineering issues related to a customer's support ticket using its ticket ID." \
  --ticket-id DEMO-101 --profile contextforge --region us-east-2
```

A CLI proposal does not prove DevRev invocation.

## Human approval and recovered answer

The following administrative steps are complete for the current connector. Use them only for a fresh independently tested candidate; approval is not needed again for teammate reuse.

The human registry owner first explicitly registers their authenticated OS identity, in a normal interactive Terminal:

```zsh
source demo/env.zsh
.venv/bin/python strands_workflow.py init-admin
```

Type the displayed `AUTHORIZE ADMIN <UID>` phrase only if authorized as the project's local administrator. The command creates a private role policy outside the repository, never overwrites existing policy, and does not activate any connector. For this workspace the observed owner is `sujanreddyayyagari`, UID `501`.

After reviewing the exact generated ID, manifest, and passing report, that human runs:

```zsh
.venv/bin/python strands_workflow.py approve get_ticket_engineering_issues_76f8fc748bff
```

The CLI displays the current exact candidate and all tests. Only after review, type `APPROVE get_ticket_engineering_issues_76f8fc748bff`. Piped/headless approval and unauthorized OS identities are rejected; a display label cannot grant permission. Changes during review invalidate the confirmation. SQLite records the authenticated administrator and immutable approval evidence. No agent/MCP approval tool exists.

MCP reads the same SQLite registry, so approval itself requires no restart. The running implementation already writes execution receipts; no restart is needed for this documentation or demo-view checkpoint.

Have Computer execute `run_capability` with that ID and `{"ticket_id":"DEMO-101"}`. Expected source evidence: `DEMO-ENG-201`, title `Synthetic issue: normalize SAML audience after migration`, and matching ticket/issue `synthetic://` references. Show the dataset label and answer only what these fields support. Optional reuse with `DEMO-102` must return `DEMO-ENG-202`.

Record actual before/after outputs, approver receipt, validation results, timestamps, and failure/retry attempts in `VALIDATION.md`. Replays must be labeled. Package migration, broader web actions, and infrastructure creation remain deferred.

Repeat RunCapability for `DEMO-102`, then `DEMO-403`; require a different issue/reference set and continued HTTP 403 denial. Inspect the new `execution-*.json` receipts for `entry_point=mcp`, `transport=network`, GET path, actual HTTP status, and returned source IDs. An unapproved/disabled request must have no outbound HTTP evidence.

An already authorized teammate must use their own Computer account to invoke the same connector and capability ID. Suggested prompt: `Use ContextForge Workflow. Call RunCapability with capability_id get_ticket_engineering_issues_76f8fc748bff and inputs {"ticket_id":"DEMO-102"}. Show the actual tool response, including the synthetic dataset label and source references.` Record their identity and execution time with the matching receipt. Do not count another session under the owner's account as teammate reuse.

Follow [the teammate runbook](DEVREV_REUSE.md) for connection authentication. The PAT field requires the existing MCP server token entered privately, not a DevRev account PAT. A visible connector card alone does not prove an authenticated session.

## Minimal web-first demonstration

Start the read-only view in a **new normal Terminal**, leaving MCP, the synthetic source, and tunnel running:

```zsh
cd /Applications/Projects/Hackmidwest/contextforge_mcp_starter
source demo/env.zsh
.venv/bin/python demo_view.py
```

Open `http://127.0.0.1:8002`. The view needs no token or AWS credentials and makes no model, source, execution, or approval call. It shows only the current synthetic proof; do not expose this loopback view publicly. Hosted access is a separate [deployment proposal](deploy/README.md).

1. **0:00–0:30 — Gap:** Show the one question, actual initially blocked result, and recorded Strands proposal timestamp. Say: “The answer needs a relationship our configured tools could not retrieve.”
2. **0:30–1:05 — Validate:** Open the generated GET manifest and ten executed checks. Say: “Strands generated the configuration and called the validator; the tests made actual source requests.”
3. **1:05–1:25 — Approve:** Show the actual administrator and approval time. Explain that source-inspection permission allows generation, while activation requires a separate human decision.
4. **1:25–2:25 — Answer and reuse:** Execute DEMO-101 live in Computer, then refresh the view and require a new receipt plus correct issue/title/references. After the reuse fix passes live, use the question-driven prompt below instead of supplying the capability ID. Show the already-verified teammate DEMO-102 result as saved second-user evidence; schedule a live teammate repeat only if they are present.
5. **2:25–3:00 — Deny:** Show the actual saved DEMO-403 source HTTP 403 with no returned records. State that all data is synthetic, source authorization is shared, and official data/hosting remain pending.

Question-driven Computer prompt, **use after the pending live fix is verified**:

```text
Use ContextForge Workflow. Call ProposeConnector with question "Which engineering issue is linked to support ticket DEMO-101? Include its title and source references." and ticket_id "DEMO-101". Show the actual decision and answer. Reuse the existing approved capability; do not approve or activate anything.
```

The existing copyable `RunCapability` prompt remains the tested live execution fallback; disclose any failed agent run. Browser, keyboard, phone layout, copy, refresh, and offline recovery checks PASS. Two technical walkthroughs with labeled history and fresh live execution took **74s and 70s**. Spoken delivery and a fresh generation/approval cycle within three minutes remain untested. See [actual results](VALIDATION.md).
