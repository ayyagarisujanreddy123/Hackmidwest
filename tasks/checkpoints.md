# Repository Checkpoints

**Repository:** [ayyagarisujanreddy123/Hackmidwest](https://github.com/ayyagarisujanreddy123/Hackmidwest). **Remote:** `origin`. **Integration branch:** `main`.

The owner has instructed contributors and coding agents to **commit and push at every completed checkpoint**. This authorizes publishing reviewed project changes to this repository; it does not authorize infrastructure provisioning or credential disclosure.

## Completing a checkpoint

1. Finish one coherent increment and execute its relevant verification. Use the acceptance criteria in [todo.md](todo.md).
2. Update [progress](../TODO.md) and [actual results](../VALIDATION.md). Distinguish executed results from reports, plans, and untested behavior.
3. Inspect `git status --short` and the intended diff. Stage explicit project paths; exclude credentials, private records, environments, caches, and databases.
4. Review `git diff --cached` and `git diff --cached --check`. Commit with a specific imperative message, such as `feat: add approved capability execution` or `docs: define web demo checkpoints`.
5. Push the checkpoint to `origin`. On `main`, run `git push origin main`; on a feature branch, push that branch for review. Do not force-push or overwrite remote work.
6. Report the commit ID, verification, and push outcome. A failed push leaves the checkpoint unpublished; preserve the local work and explain the blocker. Do not create empty commits solely to mark a checkpoint.

## Environment restrictions

This coding session cannot write local `.git` metadata or reach GitHub through Git/`gh`. GitHub's authenticated browser interface is available for publishing the reviewed baseline. Initial local Git setup therefore requires the owner's normal Terminal. After setup, agents must still report any tool restriction that prevents a later commit or push; a browser commit must be described accurately.

## Initial publication from normal Terminal

The target repository was empty when inspected. Run each command in order; stop on an error and do not force-push. Complete any GitHub authentication locally without sharing credentials.

```zsh
cd /Applications/Projects/Hackmidwest
git init -b main
git remote add origin https://github.com/ayyagarisujanreddy123/Hackmidwest.git
git add .gitignore AGENTS.md README.md PROJECT_PLAN.md TODO.md VALIDATION.md MVP_WORKFLOW.md contextforge_mcp_starter/*.py contextforge_mcp_starter/*.txt contextforge_mcp_starter/README.md tasks/*.md validation_logs/
git diff --cached --check
git commit -m "chore: save verified ContextForge planning checkpoint"
git push -u origin main
```

If staging preceded the final whitespace cleanup, rerun the `git add` command before committing. Share the resulting commit ID or credential-free error so remote publication can be verified.
