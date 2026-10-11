# Enterprise-Bench Adapter Handoff

**Status:** Public-schema preparation complete; actual integration BLOCKED on organizer-authorized records/API. Continue using `SYNTHETIC_CONTEXTFORGE_DEMO_V1`, with its current configuration and approval unchanged.

## What the public schema establishes

The official [data schema](https://github.com/devrev/enterprise-bench/blob/main/docs/data-schema.md) describes the synthetic **Maple Payments** dataset: CRM support tickets, PM engineering issues, and a shared product hierarchy. Its documented relationship is **ticket → product part/component → engineering issue**. The `data/crm_json_data/` and `data/pm_json_data/` names are upstream layout references, **not confirmed paths in this workspace**. The schema does not specify concrete REST routes, join-field names, record IDs, or our authorized access.

## Prepared contract boundary

[`enterprise_bench/source_contract.pending.json`](contextforge_mcp_starter/enterprise_bench/source_contract.pending.json) defines the existing normalized ticket/issue output shape. It intentionally has **no operations** and `x-contextforge-read-only-inspection-authorized=false`. It cannot generate or activate a connector. It contains no invented upstream endpoint, record, credential, or implicit permission grant.

Retain the current `SourceAdapter` and manifest type. Once actual access is provided, implement only the documented GET relationship lookup. If the authorized upstream requires multiple reads, a small administrator-configured adapter can normalize the verified join; models still select only a single documented read-only capability. Do not infer a ticket's related issue from similar wording or claim that component co-membership proves causation.

## Required handoff from the organizer

- Readable records/archive path or approved endpoint; dataset/version and license/authorization scope.
- API specification and any source authentication method, configured privately server-side.
- Actual ticket/component/issue join fields and evidence-reference format.
- Two independently checked ticket/issue examples, a missing record, and an explicitly authorized denial scenario. Never create a denied case by changing production permissions.
- Permission to send the necessary context to the tested US Nova inference profile; it can route within the US across Regions. [Bedrock routing documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html)

## Integration acceptance

1. Inspect the authorized records/specification and establish the two relationships with exact source references. Resolve ambiguous joins rather than guessing.
2. Prepare a separate concrete contract, validation-case file, source settings, and SQLite registry. Do not replace `demo/env.zsh` or the currently working registry.
3. Execute source discovery and the existing known/changed/missing/forbidden/host/method/path/injection/mapping checks. Record observed results; add source-auth checks only if the approved API needs them.
4. Generate a fresh restricted manifest with Strands, keep it inactive, and obtain explicit human approval for its source revision and passing report.
5. Run the original question through a staged MCP endpoint, then verify second-user access. Switch the demo only after these checks pass. B1 stays NOT TESTED until an actual approved Enterprise-Bench request succeeds.
