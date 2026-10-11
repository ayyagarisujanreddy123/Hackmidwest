# Repository Guidelines

## Project Structure & Module Organization

ContextForge has a local Python/MCP implementation and a separate Mac-hosted Yahoo Finance connector. The root contains:

- `PROJECT_PLAN.md`: product scope, proposed architecture, and integration boundaries.
- `TODO.md`: phased execution checklist and starter setup instructions.
- `VALIDATION.md`: acceptance gates, test IDs, and evidence templates.
- `FINANCE_MCP.md`: finance tool contract, Mac service management, and DevRev setup.
- `FINANCE_REFINEMENTS.md`: range, batch, CSV, reliability, and diagnostics contracts.

`contextforge_mcp_starter/` contains the MCP gateway, Strands workflow, SQLite registry, synthetic API, finance tools, and `tests/`. `finance.py` registers nine finance tools; `finance_export.py`, `finance_execution.py`, and `finance_diagnostics.py` handle CSV, bounded provider work, and read-only checks. `finance_server.py` isolates finance on port 8003; `mac_host.py` manages its Mac LaunchAgents and HTTPS tunnel. Private state and evidence are Git-ignored. Further ContextForge product work and AWS deployment remain paused.

## Build, Test, and Development Commands

Run backend commands from `contextforge_mcp_starter` using Python 3.12 and its virtual environment:

```bash
cd contextforge_mcp_starter
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-finance.txt
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python check_finance.py
.venv/bin/python check_finance.py --scenarios
.venv/bin/python mac_host.py status
.venv/bin/python mac_host.py doctor
```

After a complete real-provider readiness PASS, `mac_host.py start` starts only the separate finance server and tunnel; `stop` disables them. `reload` restarts only the finance MCP process and preserves the tunnel process; allow startup before running `doctor`. `status` marks an expired Quick Tunnel unavailable even if its process is still running. Preserve the existing ContextForge service on port 8000 during finance work. See `README.md` for workflow dependencies and `FINANCE_MCP.md` for private token entry. Do not print secrets or restart the original server for finance testing.

## Coding Style & Naming Conventions

Use descriptive Markdown headings, fenced command examples, and `- [ ]` checklist items. No formatter or linter is configured. For new Python code, use four-space indentation, `snake_case` modules/functions, `PascalCase` classes, and typed capability inputs/outputs. Follow the planned stable MCP interfaces: `list_capabilities` and `run_capability`.

## Testing Guidelines

The backend uses `unittest`; no coverage threshold is established. Follow `VALIDATION.md`; reference test IDs such as A8, B5, and C8 in reports. Prove a real DevRev Computer `ping` invocation before adapter generation or UI polish. Cover missing records, unauthorized access, forbidden hosts/methods, mapping errors, and unapproved capabilities. Keep offline fixtures distinct from live provider and DevRev evidence. Record expected versus observed results, timestamps, build identifiers, and sanitized evidence; mark PASS only after execution.

## Commit & Pull Request Guidelines

Use concise, imperative messages, optionally prefixed by scope: `docs: clarify MCP validation`. Keep changes focused and preserve pre-existing uncommitted work. PRs should describe purpose, affected TODO phase, linked issues when applicable, validation results, and sanitized screenshots for UI changes.

## Security & Configuration

Use only organizer-approved Enterprise-Bench evidence. Restrict adapters to allowlisted GET operations; require authenticated HTTPS before exposing records and human approval before capability activation. Keep credentials and sensitive records out of source, documentation, and logs.

The user-authorized finance connector reads public Yahoo Finance data separately; it is not Enterprise-Bench business evidence. Its private token authorizes bounded read-only tools and grants no workflow approval or Mac command execution.
