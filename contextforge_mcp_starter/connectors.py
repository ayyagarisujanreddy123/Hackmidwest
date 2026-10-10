"""Restricted GET executor for an administrator-configured, approved source."""

import json
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
        self.operations = {
            operation["operationId"]: {"path": path, **operation}
            for path, methods in self.contract["paths"].items()
            if (operation := methods.get("get", {})).get("x-contextforge-allowed") is True
        }

    def validate_manifest(self, manifest: ConnectorManifest) -> dict:
        operation = self.operations.get(manifest.operation_id)
        if not operation or manifest.path_template != operation["path"]:
            raise ValueError("Operation or path is outside the approved GET allowlist")
        if (not manifest.path_template.startswith("/") or manifest.path_template.startswith("//")
                or manifest.path_template.count("{ticket_id}") != 1
                or any(char in manifest.path_template for char in ("?", "#", ".."))):
            raise ValueError("Path is outside the supported GET allowlist")
        schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
        if set(manifest.output_mapping) != OUTPUT_FIELDS or not set(manifest.output_mapping.values()) <= set(schema["properties"]):
            raise ValueError("Output mapping is outside the documented field allowlist")
        return schema

    async def execute(self, manifest: ConnectorManifest, inputs: dict) -> dict:
        schema = self.validate_manifest(manifest)
        ticket = TicketInput.model_validate(inputs)
        path = manifest.path_template.replace("{ticket_id}", ticket.ticket_id)
        status = {"dataset": self.dataset}
        try:
            async with httpx.AsyncClient(transport=self.transport, timeout=5, follow_redirects=False, trust_env=False) as client:
                async with client.stream("GET", self.base_url + path) as response:
                    if response.status_code in (403, 404):
                        return {**status, "status": "forbidden" if response.status_code == 403 else "not_found"}
                    if response.status_code != 200:
                        return {**status, "status": "upstream_error", "http_status": response.status_code}
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        if len(body) + len(chunk) > 65536:
                            return {**status, "status": "response_too_large"}
                        body.extend(chunk)
            raw = json.loads(body)
            jsonschema.validate(raw, schema)
            mapped = TicketEvidence.model_validate({key: raw[field] for key, field in manifest.output_mapping.items()})
            if mapped.ticket_id != ticket.ticket_id or any(not ref for ref in mapped.source_refs):
                return {**status, "status": "invalid_response"}
            if any(issue.source_ref not in mapped.source_refs for issue in mapped.related_issues):
                return {**status, "status": "invalid_response"}
            return {**status, "status": "ok", "data": mapped.model_dump()}
        except httpx.TimeoutException:
            return {**status, "status": "upstream_timeout"}
        except httpx.HTTPError:
            return {**status, "status": "upstream_error"}
        except (ValueError, KeyError, TypeError, ValidationError, jsonschema.ValidationError):
            return {**status, "status": "invalid_response"}
