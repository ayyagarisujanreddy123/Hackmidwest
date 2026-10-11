"""Real MCP HTTP protocol tests with an explicitly invented provider fixture."""

from contextlib import asynccontextmanager
import json
from pathlib import Path
import os
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import httpx

from finance import FinanceTools
from server import create_app
from test_finance import FixtureSource


class FinanceMCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_separate_finance_port_keeps_host_validation_and_excludes_workflow(self):
        with patch.dict(os.environ, {"MCP_TOKEN": "fixture-token", "CONTEXTFORGE_ENABLE_WORKFLOW": "1"}):
            app = create_app(finance=FinanceTools(FixtureSource()), port=8003,
                             server_name="Yahoo Finance Mac", enable_workflow=False)
            async with app.app.router.lifespan_context(app.app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                        base_url="http://127.0.0.1:8003", headers={"Authorization": "Bearer fixture-token",
                        "Accept": "application/json, text/event-stream"}) as client:
                    result = await self.rpc(client, "tools/list")
                    names = {tool["name"] for tool in result["tools"]}
                    self.assertIn("get_finance_news", names)
                    self.assertNotIn("propose_connector", names)
                    self.assertNotIn("run_capability", names)
                    for host in ["127.0.0.1:8000", "attacker.example"]:
                        response = await client.post("/mcp", headers={"Host": host}, json={
                            "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
                        self.assertEqual(response.status_code, 421)

    @asynccontextmanager
    async def client_scope(self, *, finance=True):
        with patch.dict(os.environ, {"MCP_TOKEN": "offline-test-token",
                        "CONTEXTFORGE_ENABLE_FINANCE": "0", "CONTEXTFORGE_ENABLE_WORKFLOW": "0"}):
            app = create_app(finance=FinanceTools(FixtureSource()) if finance else None)
            async with app.app.router.lifespan_context(app.app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                        base_url="http://127.0.0.1:8000", headers={"Authorization": "Bearer offline-test-token",
                        "Accept": "application/json, text/event-stream"}) as client:
                    yield client

    async def rpc(self, client, method, params=None):
        response = await client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                     "method": method, "params": params or {}})
        self.assertEqual(response.status_code, 200)
        return response.json()["result"]

    async def test_discovery_contains_original_and_finance_tools(self):
        async with self.client_scope() as client:
            result = await self.rpc(client, "tools/list")
            names = {tool["name"] for tool in result["tools"]}
            self.assertTrue({"ping", "inspect_demo_capability", "get_stock_quote", "get_company_profile"} <= names)

    async def test_authenticated_tool_call_returns_structured_provider_data(self):
        async with self.client_scope() as client:
            result = await self.rpc(client, "tools/call", {"name": "get_stock_quote", "arguments": {"symbol": "FIXTURE.TEST"}})
            self.assertFalse(result.get("isError", False))
            self.assertEqual(result["structuredContent"]["data"]["price"], 42.5)

    async def test_unauthenticated_requests_are_rejected(self):
        async with self.client_scope() as client:
            for token in [None, "wrong-test-token"]:
                client.headers.pop("Authorization", None)
                if token:
                    client.headers["Authorization"] = "Bearer " + token
                response = await client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
                self.assertEqual(response.status_code, 401)

    async def test_url_cannot_be_used_as_a_symbol(self):
        async with self.client_scope() as client:
            result = await self.rpc(client, "tools/call", {"name": "get_stock_quote", "arguments": {"symbol": "http://127.0.0.1"}})
            self.assertTrue(result["isError"])

    async def test_original_ping_response_is_preserved(self):
        async with self.client_scope() as client:
            result = await self.rpc(client, "tools/call", {"name": "ping", "arguments": {}})
            self.assertEqual(result["content"][0]["text"], "pong - ContextForge MCP tool is reachable")

    async def test_finance_disabled_preserves_two_original_tools(self):
        async with self.client_scope(finance=False) as client:
            result = await self.rpc(client, "tools/list")
            self.assertEqual({tool["name"] for tool in result["tools"]}, {"ping", "inspect_demo_capability"})

    async def test_every_finance_tool_is_discovered_and_callable(self):
        inputs = {
            "get_stock_quote": {"symbol": "FIXTURE.TEST"},
            "get_company_profile": {"symbol": "FIXTURE.TEST"},
            "search_finance_symbols": {"query": "Fixture", "limit": 1},
            "get_price_history": {"symbol": "FIXTURE.TEST", "limit": 1},
            "get_financial_statement": {"symbol": "FIXTURE.TEST", "periods": 1},
            "get_finance_news": {"symbol": "FIXTURE.TEST", "limit": 1},
            "get_price_history_range": {"symbol": "FIXTURE.TEST", "start_date": "2026-10-01", "end_date": "2026-10-03"},
            "get_price_history_batch": {"symbols": ["FIXTURE.TEST"]},
            "export_price_history_csv": {"symbols": ["FIXTURE.TEST"]},
        }
        async with self.client_scope() as client:
            discovered = await self.rpc(client, "tools/list")
            self.assertEqual({tool["name"] for tool in discovered["tools"]}, set(inputs) | {"ping", "inspect_demo_capability"})
            for name, arguments in inputs.items():
                with self.subTest(tool=name):
                    result = await self.rpc(client, "tools/call", {"name": name, "arguments": arguments})
                    self.assertFalse(result.get("isError"))
                    self.assertEqual(result["structuredContent"]["status"], "ok")

    async def test_invalid_limits_and_operations_are_rejected(self):
        invalid = [
            ("get_finance_news", {"symbol": "FIXTURE.TEST", "limit": 0}),
            ("get_finance_news", {"symbol": "FIXTURE.TEST", "limit": 11}),
            ("get_finance_news", {"symbol": "FIXTURE.TEST", "limit": True}),
            ("search_finance_symbols", {"query": " "}),
            ("get_price_history", {"symbol": "FIXTURE.TEST", "limit": 367}),
            ("get_price_history", {"symbol": "FIXTURE.TEST", "period": "max"}),
            ("get_price_history", {"symbol": "FIXTURE.TEST", "interval": "1m"}),
            ("get_financial_statement", {"symbol": "FIXTURE.TEST", "statement": "execute_code"}),
            ("get_financial_statement", {"symbol": "FIXTURE.TEST", "frequency": "trailing"}),
            ("get_financial_statement", {"symbol": "FIXTURE.TEST", "periods": 5}),
        ]
        async with self.client_scope() as client:
            for name, arguments in invalid:
                with self.subTest(tool=name, arguments=arguments):
                    result = await self.rpc(client, "tools/call", {"name": name, "arguments": arguments})
                    self.assertTrue(result["isError"])

    async def test_new_history_and_csv_input_boundaries_are_enforced_over_mcp(self):
        invalid = [
            ("get_price_history_range", {"symbol": "FIXTURE.TEST", "start_date": "2026-02-30", "end_date": "2026-03-01"}),
            ("get_price_history_range", {"symbol": "FIXTURE.TEST", "start_date": "2026-10-03", "end_date": "2026-10-01"}),
            ("get_price_history_range", {"symbol": "FIXTURE.TEST", "start_date": "2025-01-01", "end_date": "2026-01-03"}),
            ("get_price_history_range", {"symbol": "FIXTURE.TEST", "start_date": "20261001", "end_date": "2026-10-03"}),
            ("export_price_history_csv", {"symbols": []}),
            ("export_price_history_csv", {"symbols": ["FIXTURE.TEST"] * 6}),
            ("export_price_history_csv", {"symbols": "FIXTURE.TEST"}),
            ("export_price_history_csv", {"symbols": ["https://example.com/AAPL"]}),
            ("export_price_history_csv", {"symbols": ["FIXTURE.TEST"], "start_date": "2026-10-01"}),
            ("export_price_history_csv", {"symbols": ["FIXTURE.TEST"], "start_date": "2026-10-01", "end_date": "2026-10-03", "period": "1mo"}),
            ("get_price_history_batch", {"symbols": ["FIXTURE.TEST"], "limit": True}),
            ("get_price_history_batch", {"symbols": ["FIXTURE.TEST"], "interval": "1m"}),
        ]
        async with self.client_scope() as client:
            for name, arguments in invalid:
                with self.subTest(tool=name, arguments=arguments):
                    result = await self.rpc(client, "tools/call", {"name": name, "arguments": arguments})
                    self.assertTrue(result["isError"])

    async def test_finance_annotations_and_maximum_history_limit_are_discovered(self):
        async with self.client_scope() as client:
            discovered = await self.rpc(client, "tools/list")
            tools = {item["name"]: item for item in discovered["tools"]}
            for name in ["get_price_history", "get_price_history_range", "get_price_history_batch", "export_price_history_csv"]:
                self.assertTrue(tools[name]["annotations"]["readOnlyHint"])
                self.assertFalse(tools[name]["annotations"]["destructiveHint"])
                self.assertEqual(tools[name]["inputSchema"]["properties"]["limit"]["maximum"], 366)
            result = await self.rpc(client, "tools/call", {"name": "get_price_history", "arguments": {"symbol": "FIXTURE.TEST", "limit": 366}})
            self.assertFalse(result["isError"])

    async def test_duplicate_authorization_headers_do_not_authorize_a_csv_call(self):
        async with self.client_scope() as client:
            response = await client.post("/mcp", headers=[("Authorization", "Bearer offline-test-token"),
                ("Authorization", "Bearer offline-test-token")], json={"jsonrpc": "2.0", "id": 1,
                "method": "tools/call", "params": {"name": "export_price_history_csv", "arguments": {"symbols": ["FIXTURE.TEST"]}}})
            self.assertEqual(response.status_code, 401)

    async def test_missing_token_still_refuses_startup(self):
        with patch.dict(os.environ, {"MCP_TOKEN": ""}):
            with self.assertRaisesRegex(RuntimeError, "MCP_TOKEN"):
                create_app()

    async def test_finance_coexists_with_workflow_without_approving_connectors(self):
        from capability_runtime import CapabilityRuntime
        from connectors import SourceAdapter
        from synthetic_source import create_app as create_synthetic_app

        backend = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as directory, patch.dict(os.environ, {"MCP_TOKEN": "offline-test-token"}):
            source = SourceAdapter(base_url="http://127.0.0.1:8001", contract_path=backend / "demo/source_contract.json",
                                   allowed_hosts=("127.0.0.1",), transport=httpx.ASGITransport(app=create_synthetic_app()))
            runtime = CapabilityRuntime(Path(directory) / "capabilities.sqlite3", source,
                       validation_cases_path=backend / "demo/validation_cases.json", receipt_directory=Path(directory) / "receipts")
            report = await runtime.validate_candidate({"name": "get_ticket_engineering_issues",
                     "purpose": "Retrieve engineering issues related to a specific support ticket",
                     "operation_id": "get_ticket_engineering_issues", "method": "GET",
                     "path_template": "/tickets/{ticket_id}/engineering-issues",
                     "output_mapping": {"ticket_id": "ticket_id", "related_issues": "related_issues", "source_refs": "source_refs"}})
            self.assertEqual(report["status"], "PASS")
            app = create_app(workflow=runtime, finance=FinanceTools(FixtureSource()))
            async with app.app.router.lifespan_context(app.app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8000",
                        headers={"Authorization": "Bearer offline-test-token", "Accept": "application/json, text/event-stream"}) as client:
                    discovered = await self.rpc(client, "tools/list")
                    names = {tool["name"] for tool in discovered["tools"]}
                    self.assertTrue({"propose_connector", "list_capabilities", "run_capability", "get_stock_quote"} <= names)
                    self.assertFalse(any("approve" in name for name in names))
                    result = await self.rpc(client, "tools/call", {"name": "run_capability", "arguments": {
                                            "capability_id": report["capability_id"], "inputs": {"ticket_id": "DEMO-101"}}})
                    self.assertEqual(json.loads(result["content"][0]["text"])["status"], "approval_required")
                    quote = await self.rpc(client, "tools/call", {"name": "get_stock_quote", "arguments": {"symbol": "FIXTURE.TEST"}})
                    self.assertEqual(quote["structuredContent"]["status"], "ok")
            with sqlite3.connect(runtime.database) as database:
                self.assertEqual(database.execute("SELECT COUNT(*) FROM approvals").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
