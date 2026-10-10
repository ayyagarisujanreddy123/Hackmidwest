# ContextForge — Progress and Next Work

**Status:** Planning v0.1. AWS compatibility checked; prototype tests/demo removed; reusable backend preserved.\
**Product decision:** Web workspace first, followed by DevRev Computer reuse.\
**Detailed plan:** [tasks/plan.md](tasks/plan.md). **Ordered implementation tasks:** [tasks/todo.md](tasks/todo.md). **Actual results:** [VALIDATION.md](VALIDATION.md).

**Version control:** Publish to `ayyagarisujanreddy123/Hackmidwest`; commit and push each completed checkpoint using [tasks/checkpoints.md](tasks/checkpoints.md). Local Git setup is blocked in this session because `.git` is protected; Git/`gh` network access also fails. Do not declare synchronization complete until remote publication and local setup are verified.

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

## Next implementation sequence

Use `tasks/todo.md` as the detailed checklist; its acceptance criteria are not yet satisfied merely because backend prototypes exist.

1. Establish the main Python package while retaining the current starter entry point.
2. Confirm approved source records/API, validation cases, and two meaningful inputs.
3. Complete persistent version/report/approval/history behavior.
4. Run a full model-generated connector recovery using real AWS access from the application worker.
5. Enable stable MCP dispatcher tools and prove Computer reuse.
6. Add authenticated web routes and job lifecycle, then build the one-page workspace.
7. Prepare and approve AWS resource/cost/access proposal; deploy and migrate only afterward.
8. Rehearse the live web-first workflow and second-user DevRev reuse.

## Pending prerequisites

- [ ] Organizer-approved Enterprise-Bench records or other explicitly approved source and its actual API/contract.
- [ ] Relationship supported by those records; candidate question must change if the join does not exist.
- [ ] Existing AWS profile or approved runtime role for the application worker. CloudShell access is proven; local credentials and EC2 role are not configured.
- [ ] Team web identities and authorized approver roles.
- [ ] Confirmed deployment hostname, eligible EC2 resources, current cost estimate, spending ceiling, shutdown owner, and explicit provisioning approval.
- [ ] DevRev discovery/resync of the new dispatcher tools and second-teammate permissions.
- [ ] Sponsor acceptance of approved evidence and the AWS hosting fallback; do not claim Akamai usage.

## Working-server command

Keep the existing server and tunnel running. If a restart is needed, from the starter folder in normal Terminal use the existing environment and enter the same secret privately:

```zsh
read -rs 'MCP_TOKEN?ContextForge token (hidden): '
export MCP_TOKEN
export CONTEXTFORGE_ENABLE_WORKFLOW=0
.venv/bin/python server.py
```

The removed smoke scripts are no longer launch instructions. Workflow tooling stays disabled until approved source settings and actual validation are ready. Do not build the frontend during this planning step, provision infrastructure, create credentials, or upgrade the account without the required authorization.
