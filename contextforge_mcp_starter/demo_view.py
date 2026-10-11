"""Local, read-only presentation of the synthetic proof; never executes or approves."""

from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route
import uvicorn

from connectors import ConnectorManifest
from synthetic_source import DATASET


STARTER = Path(__file__).resolve().parent
UI = STARTER / "demo_ui"
CHECKS = {"manifest_allowlist", "known_record_1", "known_record_2", "missing", "forbidden",
          "arbitrary_host", "mutation", "undocumented_path", "path_injection", "wrong_mapping"}


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_receipt(path: Path) -> dict | None:
    try:
        if path.stat().st_size > 512 * 1024:
            return None
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) and value.get("dataset") == DATASET else None
    except (OSError, ValueError):
        return None


def load_evidence(database: Path, logs: Path) -> dict:
    records = json.loads((STARTER / "demo/records.json").read_text())
    contract = json.loads(Path(os.environ.get(
        "CONTEXTFORGE_CONTRACT_PATH", STARTER / "demo/source_contract.json")).read_text())
    if records["dataset"] != DATASET or contract["x-contextforge-dataset"] != DATASET:
        raise ValueError("This local view accepts only the labeled synthetic source")
    config = {"contract": contract,
              "base_url": os.environ.get("CONTEXTFORGE_SOURCE_URL", "http://127.0.0.1:8001").rstrip("/"),
              "allowed_hosts": sorted(host.strip() for host in os.environ.get(
                  "CONTEXTFORGE_ALLOWED_SOURCE_HOSTS", "127.0.0.1").split(",") if host.strip())}
    revision = digest(json.dumps(config, sort_keys=True).encode())
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT * FROM capabilities ORDER BY updated_at DESC LIMIT 1").fetchone()
        if row is None:
            return {"status": "empty", "dataset": DATASET,
                    "message": "No candidate is recorded in this registry yet."}
        manifest = ConnectorManifest.model_validate_json(row["manifest"]).model_dump()
        manifest_hash = digest(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())
        report = json.loads(row["report"])
        if row["id"] != manifest["name"] + "_" + manifest_hash[:12] or report.get("dataset") != DATASET:
            raise ValueError("Candidate evidence does not match the synthetic proof")
        approval = db.execute("SELECT * FROM approvals WHERE capability_id=? ORDER BY event_id DESC LIMIT 1",
                              (row["id"],)).fetchone()
    tests = report.get("tests", {})
    validated = (report.get("status") == "PASS" and set(tests) == CHECKS
                 and all(t.get("status") == "PASS" for t in tests.values()))
    approved = bool(approval and row["status"] == "approved" and validated
                    and approval["approved_by"] == row["approved_by"]
                    and approval["administrator_uid"] == database.stat().st_uid
                    and approval["manifest_sha256"] == manifest_hash
                    and approval["validation_sha256"] == digest(row["report"].encode())
                    and approval["source_revision"] == row["source_revision"] == revision)
    proposal = None
    for path in sorted(logs.glob("workflow-*.json"), reverse=True):
        candidate = read_receipt(path)
        if (candidate and candidate.get("capability_id") == row["id"]
                and candidate.get("manifest") == manifest
                and candidate.get("execution_mode") == "strands"
                and candidate.get("status") == "TESTED_REQUIRES_APPROVAL"):
            proposal = {"run_id": candidate["run_id"], "recorded_at": candidate["recorded_at"],
                        "question": candidate["question"], "entry_point": candidate.get("entry_point"),
                        "initial_status": candidate["initial_task_result"]["status"],
                        "gap_action": candidate["gap"]["action"],
                        "tool_validation_calls": len(candidate.get("tool_validations", [])),
                        "unapproved_status": candidate["unapproved_task_result"]["status"]}
            break
    executions = {}
    allowed_tickets = {*records["tickets"], "DEMO-403"}
    for path in sorted(logs.glob("execution-*.json"), reverse=True):
        receipt = read_receipt(path)
        if not receipt or receipt.get("capability_id") != row["id"] or receipt.get("entry_point") != "mcp":
            continue
        ticket = receipt.get("inputs", {}).get("ticket_id")
        if ticket not in allowed_tickets or ticket in executions:
            continue
        request = receipt.get("http_request", {})
        item = {"ticket_id": ticket, "status": receipt["observed_status"],
                "recorded_at": receipt["recorded_at"], "receipt": path.name,
                "method": request.get("method"), "path": request.get("path"),
                "http_status": request.get("http_status"), "transport": request.get("transport"),
                "response_verified": False, "denial_verified": False, "data": None}
        if item["status"] == "forbidden":
            item["denial_verified"] = (receipt.get("source_revision") == revision
                and receipt.get("approval_state") == "approved" and request.get("transport") == "network"
                and request.get("method") == "GET" and request.get("path") == f"/tickets/{ticket}/engineering-issues"
                and request.get("http_status") == 403 and request.get("response_received") is True
                and receipt.get("evidence") == {"issue_ids": [], "source_refs": []})
        expected = records["tickets"].get(ticket)
        if expected and item["status"] == "ok":
            evidence = {"issue_ids": [issue["id"] for issue in expected["related_issues"]],
                        "source_refs": expected["source_refs"]}
            item["response_verified"] = (receipt.get("source_revision") == revision
                and receipt.get("approval_state") == "approved" and request.get("transport") == "network"
                and request.get("method") == "GET" and request.get("path") == f"/tickets/{ticket}/engineering-issues"
                and request.get("http_status") == 200 and request.get("response_received") is True
                and request.get("response_sha256") == digest(JSONResponse({"dataset": DATASET, **expected}).body)
                and receipt.get("evidence") == evidence)
            if item["response_verified"]:
                item["data"] = {key: expected[key] for key in ("ticket_id", "related_issues", "source_refs")}
        executions[ticket] = item
    return {"status": "ok", "dataset": DATASET, "capability_id": row["id"], "manifest": manifest,
            "registry_status": row["status"], "source_current": row["source_revision"] == revision,
            "approval_verified": approved,
            "approval": {"approved_by": approval["approved_by"], "approved_at": approval["approved_at"]}
                        if approved else None,
            "validation": {"status": report.get("status"), "tested_at": report.get("tested_at"),
                           "verified": validated, "tests": [{"name": name, "status": test.get("status"),
                               "observed": test.get("observed_status", "allowlisted")}
                               for name, test in tests.items()]},
            "proposal": proposal, "executions": executions}


class PrivateViewHeaders:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def protected_send(message):
            if message["type"] == "http.response.start":
                message = {**message, "headers": [*message.get("headers", []),
                    (b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"content-security-policy", b"default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")]}
            await send(message)
        await self.app(scope, receive, protected_send)


def create_app(*, database=None, receipt_directory=None):
    database = Path(database or os.environ.get("CONTEXTFORGE_DB", STARTER / "state/capabilities.sqlite3"))
    logs = Path(receipt_directory or STARTER.parent / "validation_logs")

    async def evidence(request):
        try:
            return JSONResponse(load_evidence(database, logs))
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error):
            return JSONResponse({"status": "unavailable", "message":
                "Proof evidence is missing or inconsistent. Check the registry and source configuration; no result is assumed."}, status_code=503)

    async def index(request):
        return FileResponse(UI / "index.html")

    async def css(request):
        return FileResponse(UI / "workspace.css", media_type="text/css")

    async def javascript(request):
        return FileResponse(UI / "workspace.js", media_type="text/javascript")

    app = Starlette(routes=[Route("/", index), Route("/workspace.css", css),
                            Route("/workspace.js", javascript), Route("/api/evidence", evidence)],
                    middleware=[Middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])])
    return PrivateViewHeaders(app)


if __name__ == "__main__":
    uvicorn.run(create_app(), host="127.0.0.1", port=8002, log_level="warning")
