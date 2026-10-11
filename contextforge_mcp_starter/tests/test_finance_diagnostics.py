"""Doctor checks use an in-process MCP fixture; no real network or secrets."""

from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import httpx

from finance import FinanceTools
from finance_diagnostics import run_doctor
from server import create_app
from test_finance import FixtureSource


class DoctorTests(unittest.IsolatedAsyncioTestCase):
    @asynccontextmanager
    async def fixture(self, *, saved_token=None, public_unreachable=False, provider_error=None):
        token = "fixture-doctor-" + "x" * 32
        with TemporaryDirectory() as directory, patch.dict(os.environ, {"MCP_TOKEN": token}):
            path = Path(directory) / "token"
            path.write_text(saved_token or token)
            path.chmod(0o600)
            app = create_app(finance=FinanceTools(FixtureSource(error=provider_error)),
                             port=8003, enable_workflow=False)
            asgi = httpx.ASGITransport(app=app)

            async def dispatch(request):
                if public_unreachable and request.url.host == "fixture.trycloudflare.com":
                    raise httpx.ConnectError("private-network-message", request=request)
                request.headers["host"] = "127.0.0.1:8003"  # Fixture models tunnel Host forwarding.
                return await asgi.handle_async_request(request)

            async with app.app.router.lifespan_context(app.app):
                yield path, httpx.MockTransport(dispatch)

    async def test_healthy_local_public_auth_and_provider_all_pass(self):
        async with self.fixture() as (path, transport):
            report = await run_doctor(path, "https://fixture.trycloudflare.com/mcp", transport=transport)
        self.assertEqual(report["status"], "PASS")
        stages = {check["stage"]: check["status"] for check in report["checks"]}
        for stage in ["token_file", "local_auth", "local_mcp", "public_auth", "public_mcp", "yahoo_provider"]:
            self.assertEqual(stages[stage], "PASS")

    async def test_bad_saved_token_is_reported_without_exposing_it(self):
        saved = "different-private-fixture-" + "y" * 32
        async with self.fixture(saved_token=saved) as (path, transport):
            report = await run_doctor(path, "https://fixture.trycloudflare.com/mcp", transport=transport)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(check["stage"] == "local_auth" and check["status"] == "FAIL" for check in report["checks"]))
        self.assertNotIn(saved, json.dumps(report))

    async def test_unreachable_tunnel_is_separate_from_healthy_local_and_provider(self):
        async with self.fixture(public_unreachable=True) as (path, transport):
            report = await run_doctor(path, "https://fixture.trycloudflare.com/mcp", transport=transport)
        stages = {check["stage"]: check["status"] for check in report["checks"]}
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(stages["local_mcp"], "PASS")
        self.assertEqual(stages["yahoo_provider"], "PASS")
        self.assertEqual(stages["public_transport"], "FAIL")
        self.assertNotIn("private-network-message", json.dumps(report))

    async def test_provider_failure_is_separate_from_a_working_mcp_transport(self):
        async with self.fixture(provider_error=RuntimeError("private-provider-message")) as (path, transport):
            report = await run_doctor(path, "https://fixture.trycloudflare.com/mcp", transport=transport)
        stages = {check["stage"]: check["status"] for check in report["checks"]}
        self.assertEqual(stages["local_mcp"], "PASS")
        self.assertEqual(stages["public_mcp"], "PASS")
        self.assertEqual(stages["yahoo_provider"], "FAIL")
        self.assertNotIn("private-provider-message", json.dumps(report))

    async def test_unsafe_token_file_stops_before_any_request(self):
        async with self.fixture() as (path, transport):
            path.chmod(0o640)
            report = await run_doctor(path, None, transport=transport)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(len(report["checks"]), 1)
        self.assertEqual(report["checks"][0]["stage"], "token_file")

    async def test_redirects_do_not_forward_the_private_credential(self):
        async with self.fixture() as (path, healthy):
            hosts = []

            async def redirect(request):
                hosts.append(request.url.host)
                if request.url.host == "fixture.trycloudflare.com":
                    return httpx.Response(302, headers={"Location": "https://unexpected.example/mcp"})
                return await healthy.handle_async_request(request)

            report = await run_doctor(path, "https://fixture.trycloudflare.com/mcp", transport=httpx.MockTransport(redirect))
        self.assertEqual(report["status"], "FAIL")
        self.assertNotIn("unexpected.example", hosts)


if __name__ == "__main__":
    unittest.main()
