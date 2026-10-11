"""Measured connector tests and an SQLite registry with CLI-only approval."""

from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from uuid import uuid4

from pydantic import ValidationError

from approval import ApprovalDenied, confirm_approval
from connectors import ConnectorManifest, SourceAdapter, TicketInput


class CapabilityRuntime:
    def __init__(self, database, source: SourceAdapter, *, validation_cases_path, receipt_directory=None):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.source = source
        self.validation_cases = json.loads(Path(validation_cases_path).read_text())
        self.receipt_directory = Path(receipt_directory) if receipt_directory else Path(__file__).resolve().parent.parent / "validation_logs"
        source_config = {"contract": source.contract, "base_url": source.base_url, "allowed_hosts": sorted(source.allowed_hosts)}
        self.source_revision = hashlib.sha256(json.dumps(source_config, sort_keys=True).encode()).hexdigest()
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS capabilities (
                id TEXT PRIMARY KEY, manifest TEXT NOT NULL, status TEXT NOT NULL,
                report TEXT, source_revision TEXT NOT NULL, approved_by TEXT,
                updated_at TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS approvals (
                event_id INTEGER PRIMARY KEY, capability_id TEXT NOT NULL, approved_by TEXT NOT NULL,
                administrator_uid INTEGER NOT NULL, approver_label TEXT, manifest_sha256 TEXT NOT NULL,
                source_revision TEXT NOT NULL, validation_sha256 TEXT NOT NULL, approved_at TEXT NOT NULL)""")
        self.database.chmod(0o600)

    @classmethod
    def from_environment(cls):
        required = ("CONTEXTFORGE_SOURCE_URL", "CONTEXTFORGE_CONTRACT_PATH",
                    "CONTEXTFORGE_ALLOWED_SOURCE_HOSTS", "CONTEXTFORGE_VALIDATION_CASES_PATH")
        if any(not os.environ.get(key, "").strip() for key in required):
            raise ValueError("Workflow requires an approved source URL, contract, host allowlist, and validation cases")
        source = SourceAdapter(
            base_url=os.environ["CONTEXTFORGE_SOURCE_URL"],
            contract_path=os.environ["CONTEXTFORGE_CONTRACT_PATH"],
            allowed_hosts=tuple(host.strip() for host in os.environ["CONTEXTFORGE_ALLOWED_SOURCE_HOSTS"].split(",") if host.strip()),
        )
        return cls(
            os.environ.get("CONTEXTFORGE_DB", str(Path(__file__).resolve().parent / "state" / "capabilities.sqlite3")),
            source, validation_cases_path=os.environ["CONTEXTFORGE_VALIDATION_CASES_PATH"],
        )

    def _read(self, capability_id):
        with closing(sqlite3.connect(self.database)) as db:
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM capabilities WHERE id = ?", (capability_id,)).fetchone()
        return dict(row) if row else None

    def list_capabilities(self) -> dict:
        """List configured connector IDs and approval status; execute only approved IDs."""
        with closing(sqlite3.connect(self.database)) as db:
            rows = db.execute("SELECT id, manifest, status FROM capabilities ORDER BY id LIMIT 50").fetchall()
        return {"dataset": self.source.dataset, "capabilities": [
            {"id": key, "name": json.loads(manifest)["name"], "purpose": json.loads(manifest)["purpose"], "status": status}
            for key, manifest, status in rows
        ]}

    async def run_capability(self, capability_id: str, inputs: dict, *, entry_point="runtime") -> dict:
        """Run an approved read-only connector with a ticket_id input and source references."""
        row = self._read(capability_id)
        trace = {}
        if row is None:
            result = {"status": "blocked", "reason": "Missing approved capability", "dataset": self.source.dataset}
        elif row["status"] != "approved":
            result = {"status": "disabled" if row["status"] == "disabled" else "approval_required", "dataset": self.source.dataset}
        elif row["source_revision"] != self.source_revision:
            result = {"status": "source_changed", "reason": "Retest and approve against the current contract", "dataset": self.source.dataset}
        elif not self._has_approval(row):
            result = {"status": "approval_required", "reason": "No administrator approval matches this exact manifest", "dataset": self.source.dataset}
        else:
            try:
                manifest = ConnectorManifest.model_validate_json(row["manifest"])
                result = await self.source.execute(manifest, inputs, trace=trace)
            except (ValueError, ValidationError):
                result = {"status": "invalid_input", "dataset": self.source.dataset}
        self._record_execution(row, inputs, result, trace, entry_point)
        return result

    def _has_approval(self, row) -> bool:
        try:
            manifest = ConnectorManifest.model_validate_json(row["manifest"])
        except ValidationError:
            return False
        serialized = json.dumps(manifest.model_dump(), sort_keys=True, separators=(",", ":"))
        manifest_hash = hashlib.sha256(serialized.encode()).hexdigest()
        if row["id"] != manifest.name + "_" + manifest_hash[:12]:
            return False
        with closing(sqlite3.connect(self.database)) as db:
            event = db.execute("""SELECT 1 FROM approvals WHERE capability_id=? AND approved_by=?
                AND administrator_uid=? AND manifest_sha256=? AND source_revision=? LIMIT 1""",
                               (row["id"], row["approved_by"], self.database.stat().st_uid,
                                manifest_hash, self.source_revision)).fetchone()
        return event is not None

    def _record_execution(self, row, inputs, result, trace, entry_point):
        try:
            safe_inputs = TicketInput.model_validate(inputs).model_dump()
        except ValidationError:
            safe_inputs = {"invalid_input": True}
        data = result.get("data", {})
        now = datetime.now(timezone.utc)
        receipt = {"recorded_at": now.isoformat(), "entry_point": entry_point, "dataset": self.source.dataset,
                   "capability_id": row["id"] if row else None, "approval_state": row["status"] if row else None,
                   "source_revision": self.source_revision, "inputs": safe_inputs, "observed_status": result["status"],
                   "http_request": trace, "evidence": {"issue_ids": [issue["id"] for issue in data.get("related_issues", [])],
                                                        "source_refs": data.get("source_refs", [])}}
        self.receipt_directory.mkdir(exist_ok=True, mode=0o700)
        path = self.receipt_directory / f"execution-{now.strftime('%Y%m%dT%H%M%S%fZ')}-{uuid4().hex[:8]}.json"
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as handle:
            handle.write(json.dumps(receipt, indent=2) + "\n")

    async def validate_candidate(self, candidate: dict) -> dict:
        tests = {}
        report = {"dataset": self.source.dataset, "tested_at": datetime.now(timezone.utc).isoformat(), "tests": tests}
        try:
            manifest = ConnectorManifest.model_validate(candidate)
            self.source.validate_manifest(manifest)
        except (ValueError, ValidationError):
            tests["manifest_allowlist"] = {"status": "FAIL", "reason": "Manifest must match the typed GET contract and field allowlist"}
            return {**report, "status": "FAIL", "capability_id": None}
        serialized = json.dumps(manifest.model_dump(), sort_keys=True, separators=(",", ":"))
        capability_id = manifest.name + "_" + hashlib.sha256(serialized.encode()).hexdigest()[:12]
        report["capability_id"] = capability_id
        tests["manifest_allowlist"] = {"status": "PASS"}

        for number, expected in enumerate(self.validation_cases["known"], start=1):
            observed = await self.source.execute(manifest, {"ticket_id": expected["ticket_id"]})
            data = observed.get("data", {})
            issue_ids = [issue["id"] for issue in data.get("related_issues", [])]
            passed = (observed.get("status") == "ok" and observed.get("dataset") == self.validation_cases["dataset"]
                      and data.get("ticket_id") == expected["ticket_id"] and issue_ids == expected["issue_ids"]
                      and data.get("source_refs") == expected["source_refs"])
            tests[f"known_record_{number}"] = {"status": "PASS" if passed else "FAIL", "observed_status": observed["status"], "issue_ids": issue_ids}
        for label, expected_status in (("missing", "not_found"), ("forbidden", "forbidden")):
            observed = await self.source.execute(manifest, {"ticket_id": self.validation_cases[label]})
            tests[label] = {"status": "PASS" if observed["status"] == expected_status else "FAIL", "observed_status": observed["status"]}

        for label, change in (("arbitrary_host", {"base_url": "http://169.254.169.254"}), ("mutation", {"method": "POST"}),
                              ("undocumented_path", {"path_template": "/undocumented/{ticket_id}"})):
            try:
                invalid = ConnectorManifest.model_validate({**manifest.model_dump(), **change})
                self.source.validate_manifest(invalid)
                tests[label] = {"status": "FAIL"}
            except (ValueError, ValidationError):
                tests[label] = {"status": "PASS", "observed_status": "rejected"}
        try:
            await self.source.execute(manifest, {"ticket_id": "../secret?url=http://example.test"})
            tests["path_injection"] = {"status": "FAIL"}
        except ValidationError:
            tests["path_injection"] = {"status": "PASS", "observed_status": "rejected"}
        bad_mapping = ConnectorManifest.model_validate({**manifest.model_dump(), "output_mapping": {
            "ticket_id": "ticket_subject", "related_issues": "related_issues", "source_refs": "source_refs"}})
        try:
            wrong = await self.source.execute(bad_mapping, {"ticket_id": self.validation_cases["known"][0]["ticket_id"]})
            tests["wrong_mapping"] = {"status": "PASS" if wrong["status"] == "invalid_response" else "FAIL", "observed_status": wrong["status"]}
        except (ValueError, ValidationError):
            tests["wrong_mapping"] = {"status": "PASS", "observed_status": "rejected"}

        report["status"] = "PASS" if all(test["status"] == "PASS" for test in tests.values()) else "FAIL"
        previous = self._read(capability_id)
        approval_current = previous and previous["status"] == "approved" and previous["source_revision"] == self.source_revision
        status = "approved" if approval_current and report["status"] == "PASS" else "tested" if report["status"] == "PASS" else "proposed"
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("""INSERT INTO capabilities (id, manifest, status, report, source_revision, updated_at)
                VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET
                status=excluded.status, report=excluded.report, source_revision=excluded.source_revision, updated_at=excluded.updated_at""",
                       (capability_id, serialized, status, json.dumps(report), self.source_revision, report["tested_at"]))
        return report

    def _approval_review(self, row) -> dict:
        mandatory = {"manifest_allowlist", "missing", "forbidden", "arbitrary_host", "mutation",
                     "undocumented_path", "path_injection", "wrong_mapping"}
        mandatory.update(f"known_record_{number}" for number in range(1, len(self.validation_cases["known"]) + 1))
        if (not row or row["status"] != "tested" or row["source_revision"] != self.source_revision
                or not self.source.inspection_authorized):
            raise ApprovalDenied("Only a tested candidate for the current approved source can be approved")
        manifest = ConnectorManifest.model_validate_json(row["manifest"])
        self.source.validate_manifest(manifest)
        serialized = json.dumps(manifest.model_dump(), sort_keys=True, separators=(",", ":"))
        manifest_hash = hashlib.sha256(serialized.encode()).hexdigest()
        report = json.loads(row["report"])
        if (row["id"] != manifest.name + "_" + manifest_hash[:12] or report.get("capability_id") != row["id"]
                or report.get("status") != "PASS" or set(report.get("tests", {})) != mandatory
                or any(test.get("status") != "PASS" for test in report["tests"].values())):
            raise ApprovalDenied("The exact manifest must have every mandatory validation check passing")
        return {"capability_id": row["id"], "dataset": self.source.dataset, "manifest": manifest.model_dump(),
                "manifest_sha256": manifest_hash, "source_revision": self.source_revision,
                "validation": report, "validation_sha256": hashlib.sha256(row["report"].encode()).hexdigest()}

    def approve(self, capability_id: str, approver: str | None = None) -> dict:
        """Authorize the OS administrator and require interactive human confirmation, never trust a label."""
        if approver is not None and (not approver.strip() or len(approver) > 100):
            raise ValueError("Optional approver label must contain 1–100 characters")
        snapshot = self._read(capability_id)
        review = self._approval_review(snapshot)
        administrator = confirm_approval(self.database, review)
        approved_at = datetime.now(timezone.utc).isoformat()
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.row_factory = sqlite3.Row
            current = db.execute("SELECT * FROM capabilities WHERE id = ?", (capability_id,)).fetchone()
            if not current or dict(current) != snapshot:
                raise ApprovalDenied("Candidate changed during review; review the current tested version again")
            self._approval_review(dict(current))
            db.execute("UPDATE capabilities SET status='approved', approved_by=?, updated_at=? WHERE id=?",
                       (administrator["username"], approved_at, capability_id))
            db.execute("""INSERT INTO approvals (capability_id, approved_by, administrator_uid, approver_label,
                manifest_sha256, source_revision, validation_sha256, approved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                       (capability_id, administrator["username"], administrator["uid"], approver,
                        review["manifest_sha256"], self.source_revision, review["validation_sha256"], approved_at))
        return {"capability_id": capability_id, "status": "approved", "approved_by": administrator["username"],
                "administrator_uid": administrator["uid"], "approved_at": approved_at,
                "manifest_sha256": review["manifest_sha256"], "source_revision": self.source_revision}

    def disable(self, capability_id: str) -> dict:
        with closing(sqlite3.connect(self.database)) as db, db:
            changed = db.execute("UPDATE capabilities SET status='disabled' WHERE id=?", (capability_id,)).rowcount
        if not changed:
            raise ValueError("Unknown capability")
        return {"capability_id": capability_id, "status": "disabled"}
