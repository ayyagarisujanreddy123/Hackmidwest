# ContextForge — Project Plan

**Planning version:** v0.1, October 10, 2026. **Team:** three builders.\
**Primary experience:** Web workspace first, then reuse in DevRev Computer.\
**Detailed product design:** [tasks/plan.md](tasks/plan.md).\
**Implementation tasks:** [tasks/todo.md](tasks/todo.md). **Progress:** [TODO.md](TODO.md). **Evidence:** [VALIDATION.md](VALIDATION.md).

## Product goal

Use AWS agents to examine a project's question and available context, identify a missing data/API capability, generate and test a minimal MCP connector configuration, and make the approved capability reusable through DevRev Computer. Users supply the problem; agents perform discovery, generation, validation, and execution. Explicit human activation approval remains a separate permission gate.

The sole demo case is: “Which engineering issue is linked to support ticket DEMO-101? Include its title and source references.” The existing owner-approved synthetic API supports it. This proves context recovery for one documented relationship; broader project diagnosis remains the product direction. Enterprise-Bench records remain unavailable. The limited demo inventory does not imply that DevRev globally lacks this functionality.

## What is proven

| Foundation | Evidence and limits |
|---|---|
| Bearer-authenticated MCP | Pure ASGI authentication, constant-time comparison, `/mcp`, port 8000, existing two tools; 13 post-cleanup checks passed through the real SDK and in-process ASGI |
| Existing DevRev connection | Fresh ContextForge Workflow Ping/InspectDemoCapability/ListCapabilities work; actual MCP proposal receipts show Strands execution. Historical ContextForge Test transport failure is separate |
| AWS application access | Local `contextforge` profile in `us-east-2`: actual Nova Micro inference returned `BEDROCK_WORKING`; 15 total tokens |
| Real Strands tool cycle | Strands 1.59.0 + `us.amazon.nova-micro-v1:0`; one `inspect_source_contract` call, exact returned fingerprint consumed; 2,621 total tokens |
| Backend MVP | Actual DevRev/Strands proposal generates `get_ticket_engineering_issues_76f8fc748bff`; ten validator checks PASS. Human approval followed by real MCP network GETs recovered DEMO-101, returned distinct DEMO-102 evidence, and denied DEMO-403 with source HTTP 403 |
| Human approval boundary | Owner-controlled OS administrator policy, interactive exact-version approval, atomic identity/hash audit, and matching-event execution guard; 37 scoped acceptance checks and actual human approval verified |
| Second-user reuse | Fresh teammate DEMO-102/DEMO-403 MCP network results match supplied responses; user confirms their own Bench-07 login. Same capability and original approval retained; shared source authorization, not per-user delegation |
| Minimal demonstration view | Actual Chrome inspection: 21 UI checks PASS, 22 current ASGI/evidence checks PASS; technical walkthroughs 74s/70s with labeled generation history and fresh live execution. Spoken delivery/hosting pending |
| Automatic reuse routing | Live model omitted an approved capability ID and failed safely; schema/prompt/context fix passes 31 local checks. MCP restart and live rerun pending |
| AWS deployment preflight | Read-only CloudShell confirms active Free Plan/$120 credits, eligible Ubuntu/t3.small, Ohio prices, and launch permission via DryRun. Forty-seven local deployment checks PASS; no instance/role or hosted endpoint exists yet |

Twenty-two local prototype checks passed before cleanup. Their synthetic REST and scripted-agent results are historical development evidence, not Enterprise-Bench correctness or real Bedrock connector-generation proof.

## How users access it

The planned private HTTPS workspace lets an authenticated team member ask a question, inspect the actual blocker, review the proposed capability and validation results, approve it if authorized, and see a sourced answer. A teammate then runs the same approved capability from the existing DevRev connector with another record.

The running demo page presents the actual blocked question, recorded Strands proposal, measured checks, human approval, and latest execution evidence. It has no generation or approval actions; live calls use Computer and human approval uses the CLI. The five-step walkthrough at `http://127.0.0.1:8002` has passed real Chrome and timed technical checks. Spoken delivery and hosted access remain pending. The broader interactive workspace is deferred.

For teammates, [DEVREV_REUSE.md](DEVREV_REUSE.md) explains the verified Settings → My Computer → Connectors path. An invited teammate completed reuse from their own Bench-07 login, confirmed by the user and matched to fresh network receipts. The connector's PAT field accepts the existing shared `MCP_TOKEN`; this grants no administrator approval rights or per-user source delegation.

## Architecture decisions

- Python backend; proposed FastAPI/Jinja workspace with small JavaScript; existing MCP transport remains intact.
- Both web and MCP share the capability runtime and SQLite state.
- Strands gap investigator and connector builder use the verified Nova profile, bounded calls, and one repair attempt. Deterministic code decides validation outcomes.
- Administrator supplies approved source URL, contract, host allowlist, explicit read-only inspection authorization, and validation cases. Inspection/validation can run before a connector exists; activation requires separate human approval. Generated manifests contain no executable code, arbitrary destinations, credentials, or new permissions.
- Capability stays inactive until an authorized person approves the exact tested version. Source changes and disablement prevent execution.
- Opt-in `propose_connector`, `list_capabilities`, and `run_capability` have executed through the owner's Computer connection; invited-teammate reuse also passes within the shared synthetic-source scope. Approval remains a human CLI action.
- Keep MCP/AWS credentials server-side; protect web/API access separately from the MCP bearer scheme.

## Data, cleanup, and hosting

No organizer-approved Enterprise-Bench records or API endpoint have been confirmed. The public [schema reference](https://github.com/devrev/enterprise-bench/blob/main/docs/data-schema.md) describes entities; it is not proof of available records or API access. [The handoff](ENTERPRISE_BENCH_HANDOFF.md) documents the relationship and inputs needed. The pending normalized contract has no routes and no inspection authorization; it cannot execute.

The earlier prototype tests/demo were removed as requested. The owner subsequently approved a new small synthetic source for this proof. `contextforge_mcp_starter/demo/` explicitly labels its invented records and documented API; the configured source adapter remains replaceable. Standalone test scripts remain removed. Workflow stays disabled by default.

AWS EC2 is the requested hosting target because Akamai is unavailable. Read-only AWS checks confirm an active Free Plan with $120 credits, eligible Ubuntu/t3.small, current Ohio prices, and launch DryRun permission. The owner selected a temporary Cloudflare HTTPS tunnel running on EC2. [The concrete proposal](deploy/README.md) prepares one VM, loopback services, a narrowly scoped Nova role, an unchanged historical approval archive, fresh host-specific human approval, persistence, and rollback. The proposed 24-hour/$5 budget and infrastructure/access creation still require owner approval; actual Linux/role/HTTPS tests remain unexecuted. No resources or permissions were changed. Keep the working connection until staged remote MCP/Computer checks pass. Akamai-track eligibility is not established by AWS hosting.

## Build and demonstration gates

1. Preserve the current starter entry point and MCP integration; defer package migration.
2. Use the approved synthetic API and question; record validation and approval boundaries.
3. Preserve the completed real Strands → validation → human approval → recovered synthetic answer proof.
4. Preserve the completed teammate connection/reuse and continued-denial evidence; repeat live reuse during rehearsal without regenerating the working connector.
5. Load the tested reuse-ID fix and verify automatic existing-capability selection live. Rehearse the single question with recorded discovery labeled and live Computer execution; browser/technical walkthroughs already pass. Keep the broader interactive web workspace deferred.
6. Provision AWS only after approval; verify deployment/restart/migration and rehearse the web-first, three-minute demonstration.

The event deadline recorded by the team is Sunday, October 11, 8:00 a.m. Kansas City time. Keep a rehearsal/submission buffer. Defer public signups, multitenancy, arbitrary code generation, connector marketplace, many source types, and elaborate UI until the narrow flow works.
