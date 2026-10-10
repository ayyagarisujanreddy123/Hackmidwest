# ContextForge MCP and reusable backend

The working DevRev integration retains bearer-authenticated Streamable HTTP at `/mcp` on loopback port 8000. Its default tools remain `ping` and `inspect_demo_capability`, with unchanged responses. The legacy inspection tool remains for compatibility even though standalone tests and synthetic demo files have been removed.

## Run the existing integration

Use the installed Python environment. Baseline dependencies are pinned in `requirements.txt`; optional Strands dependencies are in `requirements-workflow.txt`.

```zsh
cd contextforge_mcp_starter
read -rs 'MCP_TOKEN?ContextForge token (hidden): '
export MCP_TOKEN
export CONTEXTFORGE_ENABLE_WORKFLOW=0
.venv/bin/python server.py
```

Use the same secret privately in DevRev's server-token/PAT field, without a `Bearer ` prefix. Do not print, save, or commit it. Missing or malformed tokens prevent startup; missing/incorrect request tokens return 401. Keep the existing tunnel while the product is planned.

## Retained modules

- `server.py`: pure ASGI bearer authentication and compatible MCP tools.
- `connectors.py`: typed, allowlisted GET execution and response validation.
- `capability_runtime.py`: validation, SQLite registry, human approval, and disablement.
- `strands_workflow.py`: bounded gap investigation and connector proposal through Strands.

The standalone smoke/unit-test scripts, mock REST API, and synthetic fixtures were removed at the user's request. Previous receipts remain in `../validation_logs/`. Syntax and the default MCP integration were checked again after cleanup; this is not full business-workflow verification.

## Approved-source workflow configuration

Workflow is disabled by default. Enabling it requires administrator-confirmed values for:

- `CONTEXTFORGE_SOURCE_URL`
- `CONTEXTFORGE_CONTRACT_PATH`
- `CONTEXTFORGE_ALLOWED_SOURCE_HOSTS` (comma-separated)
- `CONTEXTFORGE_VALIDATION_CASES_PATH`
- optional `CONTEXTFORGE_DB` (otherwise local `state/capabilities.sqlite3`)

No approved source path has been confirmed. The contract must label its dataset and explicitly allow GET operations; validation cases identify approved known/missing/forbidden inputs and expected references. There is no synthetic fallback. Models cannot activate candidates.

Bedrock requires an existing authenticated AWS profile or approved runtime role and a region. The tested combination is Strands 1.59.0, `us-east-2`, and `us.amazon.nova-micro-v1:0`. Only CloudShell access has been proven; local credentials are not configured. Never create permanent keys or change account tier as an implicit setup step.

The web workspace is planned, not implemented. Read [the product plan](../tasks/plan.md), [implementation tasks](../tasks/todo.md), and [actual validation](../VALIDATION.md). No EC2 resources have been provisioned.
