# Second-User DevRev Reuse

**Status: D6 PASS.** The user confirms the invited teammate used their own Bench-07 Computer login. Actual supplied responses match fresh MCP network receipts: DEMO-102 HTTP 200 and correct source-backed evidence; DEMO-403 source HTTP 403 and no data. Ping/inventory PASS per the supplied responses. The same capability and original human approval were reused.

## Verified execution checkpoint

- Capability remains `get_ticket_engineering_issues_76f8fc748bff`, approved under the original human event; registry still contains one capability and one approval event.
- DEMO-102 at **2026-10-11 01:24:50 UTC**: `validation_logs/execution-20261011T012450173080Z-007ba1d1.json`, actual MCP/network GET, HTTP 200, full positive response hash and issue/reference fields match the documented fixture.
- DEMO-403 at **01:25:20 UTC**: `validation_logs/execution-20261011T012520054938Z-dab82516.json`, actual MCP/network GET, source HTTP 403, no disclosed records/references.
- Seventeen read-only reconciliation checks PASS in `validation_logs/devrev-reuse-evidence-20261011T012703377285Z.json`; the view correctly selects both fresh receipts. Browser verification remains pending.

The user explicitly confirmed the teammate's own login. Final evidence: `validation_logs/devrev-reuse-completion-20261011T013038388953Z.json`. Identity is user-attested; the alias was not supplied and is not invented. A shared MCP token cannot distinguish the owner from another user or delegate per-user source permissions.

## Give the teammate access

1. Keep the existing MCP process, synthetic API on port 8001, and Cloudflare Tunnel running on the owner's Mac. The teammate connects through Computer; they do not run Python or use `127.0.0.1` on their own machine.
2. In the owner's Computer app, click the bottom-left profile (**Sujanreddy298 / Bench-07**) and choose **Invite users**. Both controls were observed in the actual app. Invite the intended teammate as a regular user using the event's authorized account/seat. If the organizer manages membership or licenses, have them provide access; do not purchase seats or grant administrator rights for this test.
3. The teammate accepts the invitation and signs in with **their own** Computer identity in **Bench-07**. [DevRev's access policy](https://support.devrev.ai/en-US/devrev/article/8h8T7Tot-access-control-and-data-privacy) describes organization-scoped invitations; membership alone does not prove an authenticated custom connection.
4. Open **Settings → My Computer → Connectors → ContextForge Workflow**. This path was observed in the owner's app; the teammate confirms the card is visible in theirs. Keep the existing server URL, including `/mcp`.
5. If the connection asks for a **Personal Access Token**, enter the **existing MCP server token** privately, without a `Bearer ` prefix. Do not generate a DevRev account PAT. The server checks the configured `MCP_TOKEN`; an unrelated value returns HTTP 401. The owner can copy their existing saved token without printing it: `pbcopy < ~/.contextforge_mcp_token`. Transfer it through the team's private credential-sharing channel or enter it directly into the authorized connector field; never put it in a Computer prompt, chat, screenshot, repository, or receipt. Clear the clipboard after use with `pbcopy < /dev/null`. Do not rotate the working token for this test.
6. Save/connect using the existing card. Check **MCP Access** for enabled tools, then start a **new session** and ask: `Use ContextForge Workflow. Call Ping and ListCapabilities live. Show the actual tool responses.` Confirm Ping succeeds and the inventory contains `get_ticket_engineering_issues_76f8fc748bff` with `status=approved`.
7. If the card is absent, the organization administrator/organizer must confirm visibility. The owner's observed action menu contains resync, remove from agent, disconnect, and delete; a sharing control was not found there. If authentication or discovery still fails, record the exact credential-free error. Do not create a guessed duplicate, use the stale ContextForge Test connector, or change the working endpoint/token.

The teammate needs no AWS login, Python environment, or administrator role. Their connector does need the server token when prompted. This MVP uses one shared bearer token for the approved synthetic source; it does not establish individual source permissions. MCP exposes no administrator registration or approval tool; human approval remains restricted to the trusted local OS administrator.

## Execute reuse from their account

Paste this in the teammate's new session:

```text
Use ContextForge Workflow. Call RunCapability with capability_id
get_ticket_engineering_issues_76f8fc748bff and inputs {"ticket_id":"DEMO-102"}.
Show the actual tool response, dataset label, issue titles, and source references.
Do not generate another connector or modify approval.
```

Expected: `ok`, dataset `SYNTHETIC_CONTEXTFORGE_DEMO_V1`, issue `DEMO-ENG-202`, title `Synthetic issue: paginate report export queries`, and references:

- `synthetic://contextforge/tickets/DEMO-102`
- `synthetic://contextforge/issues/DEMO-ENG-202`

Then repeat the same call with `DEMO-403`. Expected: `forbidden`, `http_status=403`, and no data. This is the synthetic source's denial case; it does not establish per-user source identity delegation.

## Save actual evidence

Record the teammate's displayed account/team alias and Bench-07, UTC start/end, exact Computer response, and the new matching `validation_logs/execution-*.json` filename. Require `entry_point=mcp`, `transport=network`, the same capability/source revision, GET path, received HTTP 200/403, and matching IDs/references. The server's shared bearer token does not identify the individual; account evidence must come from the teammate's authenticated Computer session.

Mark D6 PASS only after this execution and identity check. Missing visibility/access is BLOCKED; an executed wrong result is FAIL. The demo view can refresh the new receipt, but viewing an old receipt is not a new reuse test.
