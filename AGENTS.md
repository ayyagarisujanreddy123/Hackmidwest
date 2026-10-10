# Repository Guidelines

## Project Structure & Module Organization

ContextForge is in discovery and integration preflight. The root contains:

- `PROJECT_PLAN.md`: product scope, proposed architecture, and integration boundaries.
- `TODO.md`: phased execution checklist and starter setup instructions.
- `VALIDATION.md`: acceptance gates, test IDs, and evidence templates.

Source code, tests, and assets are not present yet. The proposed stack is Python/MCP, AWS Strands, SQLite, and a React/TypeScript or HTML interface hosted on Akamai. Update this guide as implementation paths become available.

## Build, Test, and Development Commands

No root build or test commands exist. The documented `ContextForge_MCP_Connectivity_Starter.zip` is not included here. After obtaining and extracting it, run:

```bash
cd contextforge_mcp_starter
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python server.py
```

These commands create an isolated environment, install starter dependencies, and launch the MCP server at `http://localhost:8000/mcp`. Use the initialize probe in `TODO.md` and the Python client smoke test in `VALIDATION.md` to check connectivity.

## Coding Style & Naming Conventions

Use descriptive Markdown headings, fenced command examples, and `- [ ]` checklist items. No formatter or linter is configured. For new Python code, use four-space indentation, `snake_case` modules/functions, `PascalCase` classes, and typed capability inputs/outputs. Follow the planned stable MCP interfaces: `list_capabilities` and `run_capability`.

## Testing Guidelines

No automated testing framework or coverage threshold is established. Follow `VALIDATION.md`; reference test IDs such as A8, B5, and C8 in reports. Prove a real DevRev Computer `ping` invocation before adapter generation or UI polish. Cover missing records, unauthorized access, forbidden hosts/methods, mapping errors, and unapproved capabilities. Record expected versus observed results, timestamps, build identifiers, and sanitized evidence; mark PASS only after execution.

## Commit & Pull Request Guidelines

This directory has no Git history, so no commit convention can be inferred. Use concise, imperative messages, optionally prefixed by scope: `docs: clarify MCP validation`. Keep changes focused. PRs should describe purpose, affected TODO phase, linked issues when applicable, validation results, and sanitized screenshots for UI changes.

## Security & Configuration

Use only organizer-approved Enterprise-Bench evidence. Restrict adapters to allowlisted GET operations; require authenticated HTTPS before exposing records and human approval before capability activation. Keep credentials and sensitive records out of source, documentation, and logs.
