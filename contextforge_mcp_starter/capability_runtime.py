"""Measured connector tests and an SQLite registry with CLI-only approval."""

from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3

from pydantic import ValidationError

from connectors import ConnectorManifest, SourceAdapter


class CapabilityRuntime:
    def __init__(self, database, source: SourceAdapter, *, validation_cases_path):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.source = source
        self.validation_cases = json.loads(Path(validation_cases_path).read_text())
        source_config = {"contract": source.contract, "base_url": source.base_url, "allowed_hosts": sorted(source.allowed_hosts)}
        self.source_revision = hashlib.sha256(json.dumps(source_config, sort_keys=True).encode()).hexdigest()
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS capabilities (
                id TEXT PRIMARY KEY, manifest TEXT NOT NULL, status TEXT NOT NULL,
                report TEXT, source_revision TEXT NOT NULL, approved_by TEXT,
                updated_at TEXT NOT NULL)""")
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

    async def run_capability(self, capability_id: str, inputs: dict) -> dict:
        """Run an approved read-only connector with a ticket_id input and source references."""
        row = self._read(capability_id)
        if row is None:
            return {"status": "blocked", "reason": "Missing approved capability", "dataset": self.source.dataset}
        if row["status"] != "approved":
            return {"status": "disabled" if row["status"] == "disabled" else "approval_required", "dataset": self.source.dataset}
        if row["source_revision"] != self.source_revision:
            return {"status": "source_changed", "reason": "Retest and approve against the current contract", "dataset": self.source.dataset}
        try:
            manifest = ConnectorManifest.model_validate_json(row["manifest"])
            return await self.source.execute(manifest, inputs)
        except (ValueError, ValidationError):
            return {"status": "invalid_input", "dataset": self.source.dataset}

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

    def approve(self, capability_id: str, approver: str) -> dict:
        if not approver.strip() or len(approver) > 100:
            raise ValueError("A human approver label is required")
        with closing(sqlite3.connect(self.database)) as db, db:
            row = db.execute("SELECT status, report, source_revision FROM capabilities WHERE id = ?", (capability_id,)).fetchone()
            if not row or row[0] != "tested" or json.loads(row[1])["status"] != "PASS" or row[2] != self.source_revision:
                raise ValueError("Only a candidate that passed the current source tests can be approved")
            db.execute("UPDATE capabilities SET status='approved', approved_by=?, updated_at=? WHERE id=?", (approver, datetime.now(timezone.utc).isoformat(), capability_id))
        return {"capability_id": capability_id, "status": "approved", "approved_by": approver}

    def disable(self, capability_id: str) -> dict:
        with closing(sqlite3.connect(self.database)) as db, db:
            changed = db.execute("UPDATE capabilities SET status='disabled' WHERE id=?", (capability_id,)).rowcount
        if not changed:
            raise ValueError("Unknown capability")
        return {"capability_id": capability_id, "status": "disabled"}
