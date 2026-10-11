"""Start, stop, and inspect the Mac-hosted finance MCP and HTTPS tunnel."""

import argparse
import asyncio
import json
import os
from pathlib import Path
import plistlib
import re
import secrets
import shutil
import socket
import subprocess
import sys

from finance_server import read_private_token


BACKEND = Path(__file__).resolve().parent
RUNTIME = BACKEND / "state" / "mac-finance"
TOKEN_FILE = RUNTIME / "mcp.token"
AGENTS = Path.home() / "Library" / "LaunchAgents"
DOMAIN = f"gui/{os.getuid()}"
LABELS = {"mcp": "ai.contextforge.finance-mcp", "tunnel": "ai.contextforge.finance-tunnel"}


def launchctl(*arguments: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["/bin/launchctl", *arguments], check=check, capture_output=True, text=True)


def service_state(label: str) -> dict:
    result = launchctl("print", f"{DOMAIN}/{label}", check=False)
    match = re.search(r"^\s*pid = (\d+)$", result.stdout, re.MULTILINE)
    return {"loaded": result.returncode == 0, "running": bool(match) and "state = running" in result.stdout,
            "pid": int(match[1]) if match else None}


def start() -> None:
    python = BACKEND / ".venv" / "bin" / "python"
    tunnel = shutil.which("cloudflared")
    if not python.is_file() or not tunnel:
        raise RuntimeError("Install the project venv and Cloudflare's cloudflared before starting.")
    if not service_state(LABELS["mcp"])["loaded"]:
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", 8003))
            except OSError:
                raise RuntimeError("Port 8003 is already occupied; no existing process was stopped.") from None
    os.umask(0o077)
    RUNTIME.mkdir(mode=0o700, parents=True, exist_ok=True)
    AGENTS.mkdir(parents=True, exist_ok=True)
    if not TOKEN_FILE.exists():
        with TOKEN_FILE.open("x") as stream:
            stream.write(secrets.token_urlsafe(32) + "\n")
    read_private_token(TOKEN_FILE)
    commands = {
        "mcp": [str(python), str(BACKEND / "finance_server.py"), "--token-file", str(TOKEN_FILE)],
        "tunnel": [tunnel, "tunnel", "--no-autoupdate", "--url", "http://127.0.0.1:8003",
                   "--http-host-header", "127.0.0.1:8003", "--protocol", "http2"],
    }
    started = []
    try:
        for role, command in commands.items():
            label = LABELS[role]
            if service_state(label)["loaded"]:
                continue
            # Per-user launchd jobs survive Terminal closure; the token stays out of the plist.
            # Source: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html
            configuration = {"Label": label, "ProgramArguments": command, "WorkingDirectory": str(BACKEND),
                             "RunAtLoad": True, "KeepAlive": True, "ThrottleInterval": 30,
                             "StandardOutPath": str(RUNTIME / f"{role}.log"),
                             "StandardErrorPath": str(RUNTIME / f"{role}.log")}
            path = AGENTS / f"{label}.plist"
            if path.exists() and plistlib.loads(path.read_bytes()) != configuration:
                raise RuntimeError(f"Existing {label} configuration differs; no file was overwritten.")
            path.write_bytes(plistlib.dumps(configuration))
            launchctl("enable", f"{DOMAIN}/{label}")
            launchctl("bootstrap", DOMAIN, str(path))
            started.append(label)
    except Exception:
        for label in reversed(started):
            launchctl("bootout", f"{DOMAIN}/{label}", check=False)
            launchctl("disable", f"{DOMAIN}/{label}", check=False)
        raise
    status()


def stop() -> None:
    for label in reversed(list(LABELS.values())):
        launchctl("disable", f"{DOMAIN}/{label}")
        launchctl("bootout", f"{DOMAIN}/{label}", check=False)
    status()


def host_status() -> dict:
    services = {role: service_state(label) for role, label in LABELS.items()}
    log = RUNTIME / "tunnel.log"
    content = log.read_text() if log.exists() else ""
    urls = list(re.finditer(r"https://[a-z0-9-]+\.trycloudflare\.com", content))
    current = content[urls[-1].end():] if urls else ""
    expired = current.rfind("Tunnel not found")
    registered = current.rfind("Registered tunnel connection")
    tunnel_status = ("not_running" if not services["tunnel"]["running"] else
                     "expired" if expired > registered else "connected" if registered >= 0 else "starting")
    return {"services": services, "local_endpoint": "http://127.0.0.1:8003/mcp",
            "public_endpoint": urls[-1].group() + "/mcp" if urls and services["tunnel"]["running"] and tunnel_status != "expired" else None,
            "tunnel_status": tunnel_status,
            "token_file": str(TOKEN_FILE), "logs": str(RUNTIME),
            "hostname_changes_when_tunnel_restarts": True}


def status() -> None:
    print(json.dumps(host_status(), indent=2))


def doctor() -> None:
    from finance_diagnostics import run_doctor
    snapshot = host_status()
    report = asyncio.run(run_doctor(TOKEN_FILE, snapshot["public_endpoint"]))
    report["tunnel_status"] = snapshot["tunnel_status"]
    print(json.dumps(report, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


def reload_finance() -> None:
    if not service_state(LABELS["mcp"])["loaded"]:
        raise RuntimeError("Finance service is not loaded. Run start first.")
    launchctl("kickstart", "-k", f"{DOMAIN}/{LABELS['mcp']}")
    status()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["start", "stop", "status", "copy-token", "doctor", "reload"])
    args = parser.parse_args()
    if sys.platform != "darwin":
        raise SystemExit("This host manager requires macOS; finance_server.py also runs directly.")
    try:
        if args.action == "copy-token":
            subprocess.run(["/usr/bin/pbcopy"], input=read_private_token(TOKEN_FILE), text=True, check=True)
            print("Finance MCP token copied privately. Paste only into DevRev's PAT field.")
        else:
            {"start": start, "stop": stop, "status": status, "doctor": doctor, "reload": reload_finance}[args.action]()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        if isinstance(error, subprocess.CalledProcessError):
            raise SystemExit(f"launchctl failed with exit {error.returncode}; inspect the private service logs.") from None
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
