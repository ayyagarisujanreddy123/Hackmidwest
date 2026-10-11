"""Restricted GET executor for an administrator-configured, approved source."""

import json
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

import httpx
import jsonschema
from pydantic import BaseModel, ConfigDict, Field, ValidationError


OUTPUT_FIELDS = {"ticket_id", "related_issues", "source_refs"}


class ConnectorManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    purpose: str = Field(min_length=1, max_length=250)
    operation_id: str = Field(min_length=1, max_length=100)
    method: Literal["GET"]
    path_template: str = Field(min_length=1, max_length=200)
    output_mapping: dict[str, str] = Field(min_length=3, max_length=3)


class TicketInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    ticket_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class RelatedIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str
    title: str
    source_ref: str = Field(min_length=1)


class TicketEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    ticket_id: str
    related_issues: list[RelatedIssue] = Field(max_length=20)
    source_refs: list[str] = Field(min_length=1, max_length=30)


class SourceAdapter:
    """Administrator supplies the source and contract; models supply neither hosts nor code."""

    def __init__(self, *, base_url, contract_path, allowed_hosts=(), transport=None):
        parsed = urlsplit(base_url)
        if (parsed.scheme not in ("http", "https") or parsed.hostname not in allowed_hosts
                or parsed.username or parsed.password or parsed.query or parsed.fragment):
            raise ValueError("Source URL is outside the administrator host allowlist")
        if parsed.scheme == "http" and parsed.hostname not in ("127.0.0.1", "localhost"):
            raise ValueError("Remote sources require HTTPS")
        self.base_url = base_url.rstrip("/")
        self.allowed_hosts = tuple(allowed_hosts)
        self.transport = transport
        self.contract = json.loads(Path(contract_path).read_text())
        self.dataset = self.contract["x-contextforge-dataset"]
        self.inspection_authorized = self.contract.get("x-contextforge-read-only-inspection-authorized") is True
        self.operations = {
            operation["operationId"]: {"path": path, **operation}
            for path, methods in self.contract["paths"].items()
            if (operation := methods.get("get", {})).get("x-contextforge-allowed") is True
        }

    def _operation_schema(self, operation_id: str, path_template: str) -> dict:
        operation = self.operations.get(operation_id)
        if not operation or path_template != operation["path"]:
            raise ValueError("Operation or path is outside the approved GET allowlist")
        if (not path_template.startswith("/") or path_template.startswith("//")
                or path_template.count("{ticket_id}") != 1
                or any(char in path_template for char in ("?", "#", ".."))):
            raise ValueError("Path is outside the supported GET allowlist")
        return operation["responses"]["200"]["content"]["application/json"]["schema"]

    def validate_manifest(self, manifest: ConnectorManifest) -> dict:
        schema = self._operation_schema(manifest.operation_id, manifest.path_template)
        if set(manifest.output_mapping) != OUTPUT_FIELDS or not set(manifest.output_mapping.values()) <= set(schema["properties"]):
            raise ValueError("Output mapping is outside the documented field allowlist")
        return schema

    async def _get_response(self, path: str, schema: dict, *, trace=None) -> dict:
        status = {"dataset": self.dataset}
        if trace is not None:
            trace.update(method="GET", path=path, started_at=datetime.now(timezone.utc).isoformat(),
                         transport="network" if self.transport is None else type(self.transport).__name__)
        try:
            async with httpx.AsyncClient(transport=self.transport, timeout=5, follow_redirects=False, trust_env=False) as client:
                async with client.stream("GET", self.base_url + path) as response:
                    if trace is not None:
                        trace.update(http_status=response.status_code, response_received=True)
                    if response.status_code in (401, 403, 404):
                        return {**status, "status": "not_found" if response.status_code == 404 else "forbidden", "http_status": response.status_code}
                    if response.status_code != 200:
                        return {**status, "status": "upstream_error", "http_status": response.status_code}
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        if len(body) + len(chunk) > 65536:
                            return {**status, "status": "response_too_large"}
                        body.extend(chunk)
            if trace is not None:
                trace["response_sha256"] = hashlib.sha256(body).hexdigest()
            raw = json.loads(body)
            jsonschema.validate(raw, schema)
            return {**status, "status": "ok", "data": raw, "http_status": 200}
        except httpx.TimeoutException:
            return {**status, "status": "upstream_timeout"}
        except httpx.HTTPError:
            return {**status, "status": "upstream_error"}
        except (ValueError, TypeError, jsonschema.ValidationError):
            return {**status, "status": "invalid_response"}

    async def inspect_operation(self, operation_id: str, inputs: dict) -> dict:
        """Inspect an administrator-authorized GET API without a connector or activation approval.

        Return access evidence only; no business answer or generated output mapping.
        """
        report = {"dataset": self.dataset, "operation_id": operation_id,
                  "source_inspection_authorized": self.inspection_authorized,
                  "connector_activation": "requires_human_approval"}
        if not self.inspection_authorized or operation_id not in self.operations:
            return {**report, "status": "permission_block", "reason": "Source inspection or operation is not administrator-authorized"}
        ticket = TicketInput.model_validate(inputs)
        path_template = self.operations[operation_id]["path"]
        schema = self._operation_schema(operation_id, path_template)
        response = await self._get_response(path_template.replace("{ticket_id}", ticket.ticket_id), schema)
        observed = response["status"]
        if observed == "ok" and response["data"]["ticket_id"] != ticket.ticket_id:
            observed = "invalid_response"
        return {**report, "status": "permission_block" if observed == "forbidden" else observed,
                "observed_status": observed, "http_status": response.get("http_status")}

    async def execute(self, manifest: ConnectorManifest, inputs: dict, *, trace=None) -> dict:
        if not self.inspection_authorized:
            return {"dataset": self.dataset, "status": "forbidden"}
        schema = self.validate_manifest(manifest)
        ticket = TicketInput.model_validate(inputs)
        path = manifest.path_template.replace("{ticket_id}", ticket.ticket_id)
        response = await self._get_response(path, schema, trace=trace)
        if response["status"] != "ok":
            return response
        status = {"dataset": self.dataset}
        try:
            raw = response["data"]
            mapped = TicketEvidence.model_validate({key: raw[field] for key, field in manifest.output_mapping.items()})
            if mapped.ticket_id != ticket.ticket_id or any(not ref for ref in mapped.source_refs):
                return {**status, "status": "invalid_response"}
            if any(issue.source_ref not in mapped.source_refs for issue in mapped.related_issues):
                return {**status, "status": "invalid_response"}
            return {**status, "status": "ok", "data": mapped.model_dump()}
        except (ValueError, KeyError, TypeError, ValidationError):
            return {**status, "status": "invalid_response"}
