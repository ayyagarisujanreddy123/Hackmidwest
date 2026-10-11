"""Bounded Bedrock configuration and credential-safe operational diagnostics."""

import re


DEFAULT_MODEL = "us.amazon.nova-micro-v1:0"


class ModelBlocked(RuntimeError):
    """A deliberately safe setup message, rather than a raw SDK exception."""


def configured_session(*, profile=None, region=None):
    import os
    import boto3
    from botocore.exceptions import MissingDependencyException

    session = boto3.Session(
        profile_name=profile or os.environ.get("AWS_PROFILE"),
        region_name=region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION"),
    )
    if not session.region_name:
        raise ModelBlocked("Configure AWS_REGION or pass --region")
    try:
        credentials = session.get_credentials()
    except MissingDependencyException:
        raise ModelBlocked("AWS console login requires botocore[crt]; install requirements-workflow.txt") from None
    if credentials is None:
        raise ModelBlocked("No AWS credentials available; sign in with an existing approved AWS profile")
    return session


def client_config():
    from botocore.config import Config
    return Config(connect_timeout=5, read_timeout=45, retries={"max_attempts": 0})


def bedrock_model(*, model_id=None, region=None, profile=None, session=None, max_tokens=1600):
    import os
    from strands.models import BedrockModel

    # https://strandsagents.com/docs/user-guide/sdk/model-providers/amazon-bedrock/
    return BedrockModel(
        model_id=model_id or os.environ.get("STRANDS_MODEL_ID", DEFAULT_MODEL),
        boto_session=session or configured_session(profile=profile, region=region),
        max_tokens=max_tokens, temperature=0, boto_client_config=client_config(),
    )


def safe_failure(error):
    kind = type(error).__name__
    reason = "Operation failed; raw exception details omitted to protect credentials"
    if isinstance(error, ModelBlocked):
        reason = str(error)
    elif kind == "ModuleNotFoundError":
        reason = "Install requirements-workflow.txt"
    elif kind in {"ProfileNotFound", "NoCredentialsError", "LoginTokenLoadError", "TokenRetrievalError", "CredentialRetrievalError"}:
        reason = "AWS authentication is unavailable or expired; sign in to the configured profile"
    elif kind == "MissingDependencyException":
        reason = "AWS console login requires botocore[crt]; install requirements-workflow.txt"
    elif kind in {"EndpointConnectionError", "ConnectTimeoutError", "ReadTimeoutError"}:
        reason = "Could not reach the AWS endpoint from this execution environment"
    elif kind == "TimeoutError":
        reason = "Workflow deadline exceeded; no automatic paid retry"
    result = {"status": "BLOCKED" if kind in {
        "ModelBlocked", "ProfileNotFound", "NoCredentialsError", "LoginTokenLoadError", "TokenRetrievalError",
        "CredentialRetrievalError", "MissingDependencyException", "ModuleNotFoundError",
        "EndpointConnectionError", "ConnectTimeoutError", "ReadTimeoutError", "TimeoutError",
    } else "FAIL", "error_type": kind, "reason": reason}
    response = getattr(error, "response", {})
    detail = response.get("Error", {}) if isinstance(response, dict) else {}
    known_codes = {"AccessDeniedException", "ValidationException", "ThrottlingException", "ResourceNotFoundException",
                   "ExpiredToken", "ExpiredTokenException", "UnrecognizedClientException", "InvalidSignatureException",
                   "ServiceUnavailableException", "ModelNotReadyException", "ModelTimeoutException", "ModelErrorException"}
    if detail.get("Code") in known_codes:
        message = str(detail.get("Message", ""))
        message = re.sub(r"arn:aws[^\s,\"']*|\b\d{12}\b", "[redacted AWS identity]", message)
        message = re.sub(r"(?i)bearer\s+\S+|\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|[A-Za-z0-9_/+=-]{40,}", "[redacted]", message)
        result.update(aws_error_code=detail["Code"], aws_message=message[:500])
    return result


async def check_bedrock(runtime, *, profile=None, region=None, model_id=None):
    """Execute catalog lookup, a real inference request, and a Strands source-inspection tool."""
    from pydantic import BaseModel
    from strands import Agent, tool

    session = configured_session(profile=profile, region=region)
    selected = model_id or DEFAULT_MODEL
    checks = {}
    result = {"model_id": selected, "region": session.region_name, "checks": checks}
    try:
        catalog = session.client("bedrock", config=client_config()).list_foundation_models(
            byProvider="Amazon", byOutputModality="TEXT"
        )
        checks["catalog"] = {"status": "PASS", "nova_models": [
            {"model_id": item["modelId"], "lifecycle": item.get("modelLifecycle", {}).get("status"),
             "inference_types": item.get("inferenceTypesSupported", [])}
            for item in catalog["modelSummaries"] if item["modelId"].startswith("amazon.nova")
        ], "scope": "Catalog visibility; invocation eligibility is tested only for the selected model"}
    except Exception as error:
        checks["catalog"] = safe_failure(error)
    try:
        response = session.client("bedrock-runtime", config=client_config()).converse(
            modelId=selected,
            messages=[{"role": "user", "content": [{"text": "Reply with exactly: BEDROCK_WORKING"}]}],
            inferenceConfig={"maxTokens": 32, "temperature": 0},
        )
        observed = "".join(item.get("text", "") for item in response["output"]["message"]["content"]).strip()
        checks["inference"] = {"status": "PASS" if observed == "BEDROCK_WORKING" else "FAIL",
                               "observed": observed[:200], "usage": response.get("usage", {}),
                               "metrics": response.get("metrics", {})}
        if checks["inference"]["status"] != "PASS":
            return {**result, "status": "FAIL"}

        class SourceIdentity(BaseModel):
            dataset: str
            source_revision: str
            operation_count: int

        calls = []

        @tool
        def inspect_source_contract() -> dict:
            """Inspect the administrator-configured source label, current fingerprint, and allowed GET count."""
            if calls:
                raise ValueError("Source inspection is limited to one call for this readiness check")
            identity = {"dataset": runtime.source.dataset, "source_revision": runtime.source_revision,
                        "operation_count": len(runtime.source.operations)}
            calls.append({"tool": "inspect_source_contract", "result": identity})
            return identity

        agent = Agent(name="source-readiness", model=bedrock_model(session=session, model_id=selected, max_tokens=512),
                      tools=[inspect_source_contract], callback_handler=None, retry_strategy=None)
        answer = await agent.invoke_async(
            "Call inspect_source_contract exactly once. Return the exact dataset, source_revision, and operation_count "
            "from that tool result. Do not guess the fingerprint or claim success without invoking the tool.",
            structured_output_model=SourceIdentity, limits={"turns": 3, "output_tokens": 1000, "total_tokens": 5000},
        )
        decoded = answer.structured_output.model_dump() if answer.structured_output is not None else None
        passed = len(calls) == 1 and decoded == calls[0]["result"]
        checks["strands_tool"] = {"status": "PASS" if passed else "FAIL", "calls": calls,
                                  "model_answer": decoded, "usage": dict(answer.metrics.accumulated_usage),
                                  "stop_reason": answer.stop_reason}
        return {**result, "status": "PASS" if passed and checks["catalog"]["status"] == "PASS" else "PARTIAL" if passed else "FAIL"}
    except Exception as error:
        checks["inference" if "inference" not in checks else "strands_tool"] = safe_failure(error)
        return {**result, "status": "BLOCKED" if checks[list(checks)[-1]]["status"] == "BLOCKED" else "FAIL"}
