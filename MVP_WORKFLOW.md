# ContextForge MVP Workflow

**Planning v0.1:** The current product design is [tasks/plan.md](tasks/plan.md), with implementation work in [tasks/todo.md](tasks/todo.md).

The intended flow is: blocked question in a private web workspace → Strands gap investigation → restricted connector configuration → actual deterministic validation → human approval → sourced answer → second-teammate reuse in DevRev Computer.

Keep the existing authenticated MCP integration working. New dispatcher tools remain opt-in. Web and MCP must share the same approved-capability runtime, with credentials kept server-side.

Standalone prototype tests and the synthetic mock API/data were removed after successful AWS compatibility checks, as requested. Reusable backend modules and sanitized measurements remain. The workflow now requires explicitly configured approved source records, contract, host allowlist, and validation cases; no source path has been invented.

Nova/Strands compatibility is proven. A complete model-generated business connector, hosted web workspace, EC2 deployment, and DevRev reuse of the generated capability remain unverified. Record those separately in `VALIDATION.md`.

AWS hosting requires a concrete resource/cost/permissions proposal and explicit approval. Do not provision infrastructure or upgrade the account during planning.
