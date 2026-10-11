"""Interactive approval by an explicitly configured local OS administrator."""

import json
import os
from pathlib import Path
import pwd
import stat
import sys


class ApprovalDenied(RuntimeError):
    """Safe, actionable administrative refusal; never contains credentials."""


def policy_path(database: Path) -> Path:
    owner = pwd.getpwuid(database.stat().st_uid)
    return Path(owner.pw_dir) / ".contextforge" / "approval-policy.json"


def registry_owner(database: Path) -> dict:
    uid = os.getuid()
    database_stat = database.lstat()
    if (uid != os.geteuid() or not stat.S_ISREG(database_stat.st_mode)
            or database_stat.st_uid != uid or stat.S_IMODE(database_stat.st_mode) != 0o600):
        raise ApprovalDenied("Approval requires the registry owner's OS identity and a private regular database")
    return {"username": pwd.getpwuid(uid).pw_name, "uid": uid}


def require_terminal():
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ApprovalDenied("Approval requires a human's interactive Terminal; piped or headless approval is denied")


def initialize_administrator(database: Path) -> dict:
    """The registry owner explicitly registers their own OS identity; never activates a connector."""
    administrator = registry_owner(database)
    require_terminal()
    path = policy_path(database)
    if path.exists() or path.is_symlink():
        raise ApprovalDenied("Administrator policy already exists; inspect it rather than overwriting it")
    expected = f"AUTHORIZE ADMIN {administrator['uid']}"
    try:
        supplied = input(f"Register {administrator['username']} as the local approval administrator? Type {expected}: ")
    except (EOFError, KeyboardInterrupt):
        raise ApprovalDenied("Administrator registration was cancelled") from None
    if supplied != expected:
        raise ApprovalDenied("Administrator role was not explicitly authorized")
    path.parent.mkdir(mode=0o700, exist_ok=True)
    directory = path.parent.lstat()
    if (not stat.S_ISDIR(directory.st_mode) or directory.st_uid != administrator["uid"]
            or stat.S_IMODE(directory.st_mode) != 0o700):
        raise ApprovalDenied("Administrator policy directory must be owner-controlled with mode 700")
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), "w") as handle:
        handle.write(json.dumps({"version": 1, "administrator_uids": [administrator["uid"]]}) + "\n")
    return {"status": "ADMINISTRATOR_CONFIGURED", **require_administrator(database)}


def require_administrator(database: Path) -> dict:
    """Trust OS identity and the registry owner's private policy, never an approver label."""
    administrator = registry_owner(database)
    uid = administrator["uid"]
    path = policy_path(database)
    try:
        directory = path.parent.lstat()
        if (not stat.S_ISDIR(directory.st_mode) or directory.st_uid != uid
                or stat.S_IMODE(directory.st_mode) != 0o700):
            raise ApprovalDenied("Administrator policy directory must be owner-controlled with mode 700")
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor) as handle:
            metadata = os.fstat(handle.fileno())
            if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != uid
                    or stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_size > 8192):
                raise ApprovalDenied("Administrator policy must be an owner-controlled regular file with mode 600")
            policy = json.load(handle)
    except (OSError, ValueError):
        raise ApprovalDenied("Configure the registry owner's private administrator policy before approving") from None
    if (not isinstance(policy, dict) or policy.get("version") != 1
            or not isinstance(policy.get("administrator_uids"), list)
            or any(type(value) is not int for value in policy["administrator_uids"])
            or uid not in policy["administrator_uids"]):
        raise ApprovalDenied("This OS identity is not explicitly authorized as a ContextForge administrator")
    return administrator


def confirm_approval(database: Path, review: dict) -> dict:
    administrator = require_administrator(database)
    require_terminal()
    print(json.dumps({"administrator": administrator, "review": review}, indent=2))
    expected = "APPROVE " + review["capability_id"]
    try:
        supplied = input(f"Review the manifest and tests above. Type {expected} to activate: ")
    except (EOFError, KeyboardInterrupt):
        raise ApprovalDenied("Human approval was cancelled") from None
    if supplied != expected:
        raise ApprovalDenied("Human approval was not confirmed; connector remains inactive")
    # Recheck authorization after the human prompt in case it was revoked while reviewing.
    return require_administrator(database)
