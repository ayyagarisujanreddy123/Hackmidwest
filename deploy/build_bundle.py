"""Package reviewed files and a private approval archive; never copy credentials."""

import argparse
from contextlib import closing
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import tarfile
import tempfile


FILES = (
    "contextforge_mcp_starter/server.py", "contextforge_mcp_starter/connectors.py",
    "contextforge_mcp_starter/capability_runtime.py", "contextforge_mcp_starter/approval.py",
    "contextforge_mcp_starter/strands_workflow.py", "contextforge_mcp_starter/aws_model.py",
    "contextforge_mcp_starter/synthetic_source.py", "contextforge_mcp_starter/demo_view.py",
    "contextforge_mcp_starter/requirements.txt", "contextforge_mcp_starter/requirements-workflow.txt",
    "contextforge_mcp_starter/demo/source_contract.json", "contextforge_mcp_starter/demo/records.json",
    "contextforge_mcp_starter/demo/validation_cases.json", "contextforge_mcp_starter/demo_ui/index.html",
    "contextforge_mcp_starter/demo_ui/workspace.css", "contextforge_mcp_starter/demo_ui/workspace.js",
    "deploy/build_bundle.py", "deploy/install_ec2.sh", "deploy/validate_migration.py", "deploy/README.md",
    "deploy/source.env.example", "deploy/contextforge-source.service.example",
    "deploy/contextforge-mcp.service.example", "deploy/contextforge-tunnel.service.example",
    "deploy/ec2-trust-policy.json", "deploy/nova-micro-policy.json.example",
)
ARCHIVE_FILES = {"migration/legacy-registry.sqlite3", "migration/candidates.json"}
MAX_BYTES = 64 * 1024 * 1024


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def registry_archive(database):
    """Use SQLite's backup API for a consistent, read-only snapshot of all approvals."""
    if database.is_symlink() or not database.is_file():
        raise ValueError("Registry must be an existing regular file")
    database = database.resolve()
    with tempfile.TemporaryDirectory(prefix="contextforge-archive-") as temporary:
        snapshot = Path(temporary) / "legacy.sqlite3"
        os.close(os.open(snapshot, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as source:
            with closing(sqlite3.connect(snapshot)) as target:
                source.backup(target)
        with closing(sqlite3.connect(snapshot.as_uri() + "?mode=ro", uri=True)) as saved:
            rows = saved.execute("SELECT id, manifest, source_revision, approved_by FROM capabilities WHERE status='approved' ORDER BY id").fetchall()
            candidates = []
            for capability_id, serialized, revision, approver in rows:
                manifest = json.loads(serialized)
                digest = sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())
                event = saved.execute("SELECT 1 FROM approvals WHERE capability_id=? AND approved_by=? AND administrator_uid=? AND manifest_sha256=? AND source_revision=?", (capability_id, approver, database.stat().st_uid, digest, revision)).fetchone()
                if not event or capability_id != manifest["name"] + "_" + digest[:12]:
                    raise ValueError("An approved manifest has no matching original approval")
                candidates.append({"capability_id": capability_id, "manifest": manifest, "manifest_sha256": digest, "source_revision": revision})
            approval_count = saved.execute("SELECT COUNT(*) FROM approvals").fetchone()[0]
        if not candidates:
            raise ValueError("No approved connector is available to preserve")
        historical = snapshot.read_bytes()
    metadata = {"approval_state_on_new_host": "requires_fresh_validation_and_human_approval",
                "archived_registry_sha256": sha256(historical), "archived_approval_count": approval_count,
                "candidates": candidates}
    return {"migration/legacy-registry.sqlite3": historical,
            "migration/candidates.json": (json.dumps(metadata, indent=2) + "\n").encode()}


def build(output, database):
    root = Path(__file__).resolve().parent.parent
    files = {}
    for name in FILES:
        path = root / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError("Bundle inputs must be regular files inside the repository")
        files[name] = path.read_bytes()
    files.update(registry_archive(database))
    manifest = {"format": 1, "files": {name: {"sha256": sha256(data), "size": len(data)} for name, data in files.items()}}
    files["bundle-manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    with os.fdopen(os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as handle:
        with tarfile.open(fileobj=handle, mode="w:gz") as archive:
            for name, data in files.items():
                entry = tarfile.TarInfo(name)
                entry.size, entry.mode = len(data), 0o600
                archive.addfile(entry, io.BytesIO(data))
    return {"bundle": str(output), "sha256": sha256(output.read_bytes()), "files": len(files)}


def extract(bundle, expected_hash, destination):
    if sha256(bundle.read_bytes()) != expected_hash:
        raise ValueError("Bundle checksum mismatch; nothing extracted")
    files = {}
    with tarfile.open(bundle, "r:gz") as archive:
        total = 0
        for entry in archive.getmembers():
            path = PurePosixPath(entry.name)
            total += entry.size
            if (not entry.isfile() or path.is_absolute() or ".." in path.parts
                    or str(path) != entry.name or "\\" in entry.name or entry.name in files
                    or entry.size < 0 or total > MAX_BYTES):
                raise ValueError("Unsafe or oversized bundle member; nothing extracted")
            with archive.extractfile(entry) as handle:
                files[entry.name] = handle.read()
    manifest = json.loads(files["bundle-manifest.json"])
    expected_names = set(FILES) | ARCHIVE_FILES
    if manifest.get("format") != 1 or set(manifest["files"]) != expected_names or set(files) != expected_names | {"bundle-manifest.json"}:
        raise ValueError("Unexpected bundle contents; nothing extracted")
    for name, recorded in manifest["files"].items():
        if sha256(files[name]) != recorded["sha256"] or len(files[name]) != recorded["size"]:
            raise ValueError("File checksum mismatch; nothing extracted")
    destination.mkdir(mode=0o700)  # Refuse an existing directory, registry, or symlink.
    for name, data in files.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as handle:
            handle.write(data)
    return {"extracted": str(destination), "files": len(files), "sha256": expected_hash}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    package = actions.add_parser("build")
    package.add_argument("--output", type=Path, required=True)
    package.add_argument("--registry", type=Path, required=True)
    unpack = actions.add_parser("extract")
    unpack.add_argument("bundle", type=Path)
    unpack.add_argument("--sha256", required=True)
    unpack.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output, args.registry) if args.action == "build" else extract(args.bundle, args.sha256, args.destination)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
