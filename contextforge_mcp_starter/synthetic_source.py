"""Loopback-only REST source containing explicitly approved synthetic demo records."""

import json
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn


DEMO_DIRECTORY = Path(__file__).resolve().parent / "demo"
DATASET = "SYNTHETIC_CONTEXTFORGE_DEMO_V1"


def create_app():
    records = json.loads((DEMO_DIRECTORY / "records.json").read_text())
    if records["dataset"] != DATASET:
        raise ValueError("This demonstration source accepts only labeled synthetic records")

    async def ticket_issues(request):
        ticket_id = request.path_params["ticket_id"]
        if ticket_id == "DEMO-403":
            return JSONResponse({"dataset": DATASET, "status": "forbidden"}, status_code=403)
        record = records["tickets"].get(ticket_id)
        if record is None:
            return JSONResponse({"dataset": DATASET, "status": "not_found"}, status_code=404)
        return JSONResponse({"dataset": DATASET, **record})

    return Starlette(
        routes=[Route("/tickets/{ticket_id}/engineering-issues", ticket_issues, methods=["GET"])],
        middleware=[Middleware(
            TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"]
        )],
    )


if __name__ == "__main__":
    uvicorn.run(create_app(), host="127.0.0.1", port=8001, log_level="warning")
