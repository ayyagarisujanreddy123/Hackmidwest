# ContextForge — Project Plan

**Planning version:** v0.1, October 10, 2026. **Team:** three builders.\
**Primary experience:** Web workspace first, then reuse in DevRev Computer.\
**Detailed product design:** [tasks/plan.md](tasks/plan.md).\
**Implementation tasks:** [tasks/todo.md](tasks/todo.md). **Progress:** [TODO.md](TODO.md). **Evidence:** [VALIDATION.md](VALIDATION.md).

## Product goal

Help an integration owner recover a blocked enterprise question by identifying the missing data capability, proposing a minimal read-only connector configuration, validating it with actual requests, obtaining human approval, and making it reusable by another teammate through DevRev Computer.

The first release supports one approved source and one useful relationship lookup. Ticket-to-engineering-issue lookup is a candidate, pending confirmation from actual approved records. The limited demo inventory does not imply that DevRev globally lacks this functionality.

## What is proven

| Foundation | Evidence and limits |
|---|---|
| Bearer-authenticated MCP | Pure ASGI authentication, constant-time comparison, `/mcp`, port 8000, existing two tools; 13 post-cleanup checks passed through the real SDK and in-process ASGI |
| Existing DevRev connection | User reports successful `Ping` and `InspectDemoCapability` through Cloudflare Tunnel; independently rerunning Computer was not part of this turn |
| AWS model access | Nova Micro playground returned the exact probe response; 9 input / 6 output tokens |
| Real Strands tool cycle | Strands 1.59.0 + `us.amazon.nova-micro-v1:0` in `us-east-2`; one actual tool invocation, exact result and fresh proof marker consumed; 1,531 total tokens |
| Reusable backend groundwork | Restricted GET executor, SQLite registry/approval, bounded gap/builder workflow retained; full model-generated business connector is not yet proven |

Twenty-two local prototype checks passed before cleanup. Their synthetic REST and scripted-agent results are historical development evidence, not Enterprise-Bench correctness or real Bedrock connector-generation proof.

## How users access it

The planned private HTTPS workspace lets an authenticated team member ask a question, inspect the actual blocker, review the proposed capability and validation results, approve it if authorized, and see a sourced answer. A teammate then runs the same approved capability from the existing DevRev connector with another record.

Use a single page with question, capability review, and answer/reuse panels. Keep before/after results visible. CLI remains an administrative fallback. A deployed URL, web login, and frontend do not exist yet; the detailed plan defines them.

## Architecture decisions

- Python backend; proposed FastAPI/Jinja workspace with small JavaScript; existing MCP transport remains intact.
- Both web and MCP share the capability runtime and SQLite state.
- Strands gap investigator and connector builder use the verified Nova profile, bounded calls, and one repair attempt. Deterministic code decides validation outcomes.
- Administrator supplies approved source URL, contract, host allowlist, and validation cases. Generated manifests contain no executable code, arbitrary destinations, credentials, or new permissions.
- Capability stays inactive until an authorized person approves the exact tested version. Source changes and disablement prevent execution.
- Add stable `list_capabilities` and `run_capability` tools only after verification and a deliberate DevRev resync. Preserve the existing tool names and responses.
- Keep MCP/AWS credentials server-side; protect web/API access separately from the MCP bearer scheme.

## Data, cleanup, and hosting

No organizer-approved Enterprise-Bench records or API endpoint have been confirmed. The public [schema reference](https://github.com/devrev/enterprise-bench/blob/main/docs/data-schema.md) describes entities; it is not proof of available records or API access.

The user authorized synthetic development fixtures earlier, then requested removal after AWS compatibility checks. Standalone test scripts, smoke client, mock REST server, and synthetic dataset/contract have now been removed. Reusable backend modules and sanitized evidence remain. The optional workflow requires explicit approved-source configuration and stays disabled by default.

AWS EC2 is the requested hosting target because Akamai is unavailable. The AWS account has a user-reported $100 Free Plan credit budget. No infrastructure creation or account upgrade is authorized. Prepare a concrete resource, permissions, HTTPS, cost, and teardown proposal before requesting approval. Keep the working tunnel until the replacement passes remote MCP and actual Computer calls. Akamai-track eligibility is not established by AWS deployment.

## Build and demonstration gates

1. Package the preserved backend without breaking the current MCP integration.
2. Confirm one approved source and question; prove measured validation and approval boundaries.
3. Execute a real Strands-generated business connector workflow, then recover the original question.
4. Prove DevRev reuse by another authorized teammate with a different record.
5. Build the authenticated web workspace against real backend state.
6. Provision AWS only after approval; verify deployment/restart/migration and rehearse the web-first, three-minute demonstration.

The event deadline recorded by the team is Sunday, October 11, 8:00 a.m. Kansas City time. Keep a rehearsal/submission buffer. Defer public signups, multitenancy, arbitrary code generation, connector marketplace, many source types, and elaborate UI until the narrow flow works.
