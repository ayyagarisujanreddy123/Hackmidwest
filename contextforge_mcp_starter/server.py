"""Bearer-authenticated MCP gateway with an opt-in approved-source workflow."""

import hmac
import os

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
import uvicorn


class BearerTokenAuthMiddleware:
    """Authenticate HTTP without buffering ASGI messages or streams.

    Sources: https://www.starlette.io/middleware/#pure-asgi-middleware
    https://docs.python.org/3.12/library/hmac.html#hmac.compare_digest
    """

    def __init__(self, app: ASGIApp, token: str) -> None:
        self.app = app
        self._expected_token = token.encode("utf-8")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = [
                value for name, value in scope.get("headers", [])
                if name.lower() == b"authorization"
            ]
            scheme, _, supplied_token = (
                headers[0].partition(b" ") if len(headers) == 1 else (b"", b"", b"")
            )
            if scheme.lower() != b"bearer" or not hmac.compare_digest(supplied_token, self._expected_token):
                response = JSONResponse(
                    {"error": "Unauthorized"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"},
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


def ping() -> str:
    """Check whether DevRev Computer can invoke a tool on this server."""
    return "pong - ContextForge MCP tool is reachable"

def inspect_demo_capability() -> dict:
    """Return the only capability of this disposable test server."""
    return {"capability": "connectivity-test", "status": "working", "sample_records": 0}


def create_app(*, workflow=None) -> BearerTokenAuthMiddleware:
    token = os.environ.get("MCP_TOKEN")
    if not token:
        raise RuntimeError("MCP_TOKEN environment variable is required before starting the server.")
    if not token.isascii() or not token.isprintable() or any(char.isspace() for char in token):
        raise RuntimeError("MCP_TOKEN must be a single ASCII token without spaces or line breaks.")

    server = FastMCP(
        "ContextForge Connectivity Test",
        host="127.0.0.1",
        port=8000,
        json_response=True,
        stateless_http=True,
        transport_security=TransportSecuritySettings(
            allowed_hosts=["127.0.0.1:8000", "localhost:8000"],
            allowed_origins=[],
        ),
    )
    server.add_tool(ping)
    server.add_tool(inspect_demo_capability)
    if workflow is None and os.environ.get("CONTEXTFORGE_ENABLE_WORKFLOW") == "1":
        from capability_runtime import CapabilityRuntime
        workflow = CapabilityRuntime.from_environment()
    if workflow is not None:
        server.add_tool(workflow.list_capabilities, name="list_capabilities")
        server.add_tool(workflow.run_capability, name="run_capability")
    return BearerTokenAuthMiddleware(server.streamable_http_app(), token)


if __name__ == "__main__":
    try:
        app = create_app()
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
