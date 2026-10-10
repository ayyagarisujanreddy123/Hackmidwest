# ContextForge

ContextForge helps an integration owner recover a blocked enterprise question: identify a missing data capability, generate a restricted read-only connector configuration, validate it with actual requests, obtain human approval, and reuse it through DevRev Computer.

## Current checkpoint

Planning v0.1. The authenticated MCP gateway and reusable backend are present. Nova Micro and one real AWS Strands tool cycle have been verified; the full business connector workflow, web workspace, and EC2 deployment remain pending.

The existing DevRev integration works according to the team's report. Preserve its two tools and current endpoint while implementing the next increments. No organizer-approved enterprise source has been configured. Standalone prototype tests and synthetic demo data were removed at the owner's request; sanitized historical results remain available.

## Start here

- [Product scope and current proof](PROJECT_PLAN.md)
- [Detailed web experience, architecture, and demonstration plan](tasks/plan.md)
- [Ordered implementation tasks](tasks/todo.md)
- [Progress and prerequisites](TODO.md)
- [Executed validation and its limits](VALIDATION.md)
- [MCP setup and backend configuration](contextforge_mcp_starter/README.md)
- [Commit and push policy](tasks/checkpoints.md)

## Development boundaries

Keep credentials, local AWS configuration, environments, databases, and customer records out of Git. Require `MCP_TOKEN` before starting the MCP server, and enter it privately using the backend setup instructions. Connector execution remains disabled until an explicitly approved source and validation cases are configured.

Build the backend proof before the web workspace. Infrastructure creation and AWS account upgrades require a separate approved resource proposal.
