# ContextForge MCP and reusable backend

The working DevRev integration retains bearer-authenticated Streamable HTTP at `/mcp` on loopback port 8000. Its default tools remain `ping` and `inspect_demo_capability`, with unchanged responses. The opt-in workflow adds `propose_connector`, `list_capabilities`, and `run_capability`; it cannot activate connectors.

## Run the existing integration

Use the installed Python environment. Baseline dependencies are pinned in `requirements.txt`; optional Strands dependencies are in `requirements-workflow.txt`.

```zsh
cd contextforge_mcp_starter
read -rs 'MCP_TOKEN?ContextForge token (hidden): '
export MCP_TOKEN
export CONTEXTFORGE_ENABLE_WORKFLOW=0
.venv/bin/python server.py
```

Use the same secret privately in DevRev's server-token/PAT field, without a `Bearer ` prefix. Do not print it or store it in source, receipts, or logs. Missing or malformed tokens prevent startup; missing/incorrect request tokens return 401. Keep the existing tunnel during the proof.

An authorized teammate may see the same connector card yet still be asked to authenticate their connection. Its PAT field requires the existing server token; it is not a DevRev account PAT. Follow [the teammate guide](../DEVREV_REUSE.md) for private transfer and live checks. The shared bearer authorizes the same synthetic source, not individual record permissions or connector approval.

## Retained modules

- `server.py`: pure ASGI bearer authentication and compatible MCP tools.
- `connectors.py`: typed, allowlisted GET execution and response validation.
- `capability_runtime.py`: validation, SQLite registry, human approval, and disablement.
- `strands_workflow.py`: bounded gap investigation and connector proposal through Strands.
- `aws_model.py`: existing AWS-profile configuration, real readiness checks, and sanitized failures.
- `synthetic_source.py`, `demo/`: newly authorized synthetic API/specification/records for this proof.
- `demo_view.py`, `demo_ui/`: local read-only evidence page; actual generation/execution stay in Computer.
- `enterprise_bench/source_contract.pending.json`: inactive normalized-output handoff; no routes or source authorization.

Earlier standalone tests/demo were removed as requested. The owner subsequently approved the new labeled synthetic source. No standalone test scripts were added back. Receipts in `../validation_logs/` are local evidence and ignored by Git.

## Approved-source workflow configuration

Workflow is disabled by default. Enabling it requires administrator-confirmed values for:

- `CONTEXTFORGE_SOURCE_URL`
- `CONTEXTFORGE_CONTRACT_PATH`
- `CONTEXTFORGE_ALLOWED_SOURCE_HOSTS` (comma-separated)
- `CONTEXTFORGE_VALIDATION_CASES_PATH`
- optional `CONTEXTFORGE_DB` (otherwise local `state/capabilities.sqlite3`)

The approved demonstration settings are in `demo/env.zsh`; they select loopback port 8001 and explicitly labeled synthetic records. The contract allows one GET operation; cases define known/missing/simulated-forbidden inputs. There is no automatic source fallback. Replace administrator configuration when approved enterprise data arrives.

The trusted contract must declare `x-contextforge-read-only-inspection-authorized: true`; each permitted GET operation needs `x-contextforge-allowed: true`. These settings document administrator permission to inspect and validate that source before a connector exists. Missing/false authorization denies access. The investigator performs one actual GET, receives access evidence, and may choose `propose_new_connector` with the verified operation ID. Actual 401/403 still block generation. Human CLI approval is separately required before dispatcher execution; source inspection never activates a connector. Models cannot modify these permissions.

Bedrock uses existing profile `contextforge`, region `us-east-2`, and `us.amazon.nova-micro-v1:0`. Real local-profile inference and a Strands tool/result check passed. `requirements-workflow.txt` includes the pinned `botocore[crt]` extra needed for AWS console login. Model calls have token/turn/deadline limits and no automatic paid retries.

Follow [the live workflow runbook](../MVP_WORKFLOW.md) for source startup, MCP restart, actual Computer calls, and human approval. SQLite state is shared by CLI and MCP. Generated manifests cannot contain executable code, credentials, arbitrary URLs, mutation methods, or undocumented routes.

## Human administrator approval

Approval uses the registry owner's authenticated OS identity and an explicit private role policy. The owner runs `strands_workflow.py init-admin` in a normal interactive Terminal and confirms their UID. This creates `~/.contextforge/approval-policy.json` (mode 600, private directory mode 700); an existing policy is never overwritten. The path comes from the OS account database, not `HOME` or a model-selected environment setting.

Then run `strands_workflow.py approve ACTUAL_CAPABILITY_ID`. Review the displayed manifest, source revision, and every measured test; type `APPROVE ACTUAL_CAPABILITY_ID` only if authorized and satisfied. Optional `--approver` is a display label, never an authorization grant. Missing/unlisted administrator identity, unsafe policy permissions, headless/piped input, failed/incomplete tests, source changes, and changes during review deny approval. The trusted OS username/UID, exact manifest hash, source revision, and validation hash are recorded atomically in SQLite. Dispatcher execution requires a matching administrator audit event; a flipped status or changed manifest/approver cannot reuse approval.

This MVP's administration boundary is the trusted local registry-owner account; teammates execute through authenticated DevRev/MCP and receive no approval tool. Agents cannot register administrators or approve connectors through MCP. Role setup and actual approval must be performed by the human owner; test fixtures use separate temporary registries.

`run_capability` retains its response format and writes private `../validation_logs/execution-*.json` receipts with input ID, approval state, observed status, source references, and actual GET/HTTP status. Network and in-process ASGI transports are distinguished. Receipts omit bearer headers, environment credentials, and arbitrary invalid-input fields.

## Minimal local demonstration view

In a separate normal Terminal, retain all working processes and run:

```zsh
cd /Applications/Projects/Hackmidwest/contextforge_mcp_starter
source demo/env.zsh
.venv/bin/python demo_view.py
```

Open `http://127.0.0.1:8002`. The view reads `CONTEXTFORGE_DB` in read-only mode and sanitized receipts; source binding uses the same `CONTEXTFORGE_ALLOWED_SOURCE_HOSTS` and contract settings as the runtime. It accepts only the current labeled synthetic proof, verifies approval/response hashes, and offers a five-step walkthrough, copyable prompts, and evidence refresh. It has no generation or approval endpoint, requires no MCP token/AWS login, and binds only to loopback. Recorded generation stays labeled. ASGI/privacy checks and 21 native Chrome checks PASS; two technical walkthroughs with fresh Computer execution took 74s/70s. See the live runbook for the pending automatic reuse fix and restart.

The broader interactive workspace is planned. Read [the product plan](../tasks/plan.md), [implementation tasks](../tasks/todo.md), and [actual validation](../VALIDATION.md). [AWS examples](../deploy/README.md) are preparation only; no EC2 resources have been provisioned.
