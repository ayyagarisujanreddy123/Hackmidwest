"""Read-only checks that distinguish credentials, MCP transport, and Yahoo."""

from datetime import datetime, timezone
from pathlib import Path

import httpx

from finance import FINANCE_TOOL_NAMES
from finance_server import read_private_token


class DiagnosticFailure(Exception):
    """Only fixed, non-sensitive messages may be stored in this exception."""


async def _probe(client, role, endpoint, token, checks, *, provider=False):
    stage = role + "_transport"
    headers = {"Authorization": "Bearer " + token, "Accept": "application/json, text/event-stream"}

    async def rpc(method, params):
        response = await client.post(endpoint, headers=headers,
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        if response.status_code == 401:
            raise DiagnosticFailure("The server rejected the saved MCP token. Check the connection selected for DevRev resync.")
        if response.status_code != 200:
            raise DiagnosticFailure("The MCP endpoint returned an unexpected HTTP status.")
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("result"), dict):
            raise DiagnosticFailure("The endpoint did not return a valid MCP result.")
        return payload["result"]

    try:
        unauthorized = await client.post(endpoint, headers={"Accept": headers["Accept"]},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
        checks.append({"stage": stage, "status": "PASS", "message": "Endpoint is reachable."})
        stage = role + "_auth"
        if unauthorized.status_code != 401:
            raise DiagnosticFailure("Unauthenticated requests were not rejected with HTTP 401.")
        await rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "finance-doctor", "version": "1"}})
        checks.append({"stage": stage, "status": "PASS", "message": "Saved token accepted; missing token rejected."})
        stage = role + "_mcp"
        discovered = await rpc("tools/list", {})
        names = {tool["name"] for tool in discovered["tools"]}
        if names != set(FINANCE_TOOL_NAMES) | {"ping", "inspect_demo_capability"}:
            raise DiagnosticFailure("Tool inventory differs from this build. Reload the finance service and resync DevRev tools.")
        ping = await rpc("tools/call", {"name": "ping", "arguments": {}})
        if ping.get("isError") or not any(item.get("text") == "pong - ContextForge MCP tool is reachable" for item in ping.get("content", [])):
            raise DiagnosticFailure("MCP ping did not return the expected response.")
        checks.append({"stage": stage, "status": "PASS", "message": "Initialize, discovery and ping succeeded.",
                       "tool_count": len(names)})
        if provider:
            stage = "yahoo_provider"
            quote = await rpc("tools/call", {"name": "get_stock_quote", "arguments": {"symbol": "AAPL"}})
            result = quote.get("structuredContent", {})
            status = result.get("status")
            if quote.get("isError") or status != "ok" or not result.get("data"):
                reason = {"rate_limited": "Yahoo Finance is rate-limiting requests; retry later.",
                          "no_data": "Yahoo Finance returned no usable quote."}.get(status, "Yahoo Finance could not return a quote.")
                raise DiagnosticFailure(reason)
            checks.append({"stage": stage, "status": "PASS", "message": "AAPL quote returned usable provider data.",
                           "retrieved_at": result["retrieved_at"], "cached": result.get("cached", False)})
    except DiagnosticFailure as error:
        checks.append({"stage": stage, "status": "FAIL", "message": str(error)})
    except httpx.RequestError:
        checks.append({"stage": stage, "status": "FAIL", "message": "Endpoint connection failed or timed out."})
    except (ValueError, KeyError, TypeError):
        checks.append({"stage": stage, "status": "FAIL", "message": "Endpoint returned malformed MCP data."})


async def run_doctor(token_file: Path, public_endpoint: str | None, *, transport=None) -> dict:
    checks = []
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "checks": checks}
    try:
        token = read_private_token(token_file)
    except (RuntimeError, OSError):
        checks.append({"stage": "token_file", "status": "FAIL", "message": "Private token file is missing or unsafe. It must be owner-only, mode 600, with a valid bounded secret."})
    else:
        checks.append({"stage": "token_file", "status": "PASS", "message": "Private token file is safe and readable."})
        # Never follow redirects with a credential-bearing request.
        async with httpx.AsyncClient(timeout=10, follow_redirects=False, transport=transport) as client:
            await _probe(client, "local", "http://127.0.0.1:8003/mcp", token, checks, provider=True)
            if public_endpoint:
                await _probe(client, "public", public_endpoint, token, checks)
            else:
                checks.append({"stage": "public_transport", "status": "FAIL", "message": "No current public URL was found for a running tunnel."})
    report["status"] = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    return report
