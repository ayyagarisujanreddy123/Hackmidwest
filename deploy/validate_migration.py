"""Retest archived manifests on the new host; never transfer activation permission."""

import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "contextforge_mcp_starter"))

from capability_runtime import CapabilityRuntime
from strands_workflow import save_receipt


async def main():
    root = Path(__file__).resolve().parent.parent
    metadata = json.loads((root / "migration/candidates.json").read_text())
    runtime = CapabilityRuntime.from_environment()
    if any(item["status"] == "approved" for item in runtime.list_capabilities()["capabilities"]):
        raise ValueError("Refusing to change an already approved staging registry")
    candidates = metadata["candidates"]
    if not candidates or any(item["source_revision"] != runtime.source_revision for item in candidates):
        raise ValueError("Migration requires the unchanged, explicitly approved source configuration")
    results = []
    for item in candidates:
        report = await runtime.validate_candidate(item["manifest"])
        state = await runtime.run_capability(report["capability_id"], {"ticket_id": runtime.validation_cases["known"][0]["ticket_id"]}) if report["capability_id"] else {}
        passed = report["status"] == "PASS" and report["capability_id"] == item["capability_id"] and state.get("status") == "approval_required"
        results.append({"status": "PASS" if passed else "FAIL", "validation": report, "unapproved_execution": state})
    result = {"status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL",
              "entry_point": "deployment_manifest_revalidation", "results": results,
              "archived_registry_sha256": metadata["archived_registry_sha256"],
              "approval_state": "inactive_requires_explicit_human_approval"}
    receipt = save_receipt(result)
    print(json.dumps({**result, "receipt": str(receipt)}, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
