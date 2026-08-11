"""FastAPI backend for the Vista Assistant chat app.

The chat endpoint is Server-Sent Events. Two headers matter behind the Databricks Apps
proxy: text/event-stream and X-Accel-Buffering: no. Without the latter the proxy buffers
the whole response and the client sees one burst instead of a stream.
"""
from __future__ import annotations

import json
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

# Add the scripts directory to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from scripts.config import CFG

from . import supervisor

app = FastAPI(title="Meridian Vista Assistant")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")


class ChatRequest(BaseModel):
    question: str
    history: list[dict] | None = None


SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@app.post("/api/chat")
def chat(req: ChatRequest):
    def gen():
        # An initial comment flushes headers through the proxy immediately, so the UI
        # can show its "thinking" state without waiting for the first model token.
        yield ": open\n\n"
        try:
            for ev in supervisor.stream(req.question, req.history):
                yield f"data: {json.dumps(ev)}\n\n"
        except Exception as e:  # never leave the stream hanging
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream", headers=SSE_HEADERS)


@app.get("/api/config")
def config():
    """Surfaces what the app is wired to - handy for the demo and for debugging."""
    return {
        "supervisor_endpoint": supervisor.ENDPOINT or None,
        "genie_space_id": os.environ.get("GENIE_SPACE_ID"),
        "catalog": CFG.catalog,
        "schema": CFG.schema,
        "fq_schema": CFG.fq_schema,
        "volume": CFG.docs_path,
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "endpoint_configured": bool(supervisor.ENDPOINT)}


if os.path.isdir(STATIC_DIR):
    @app.get("/")
    def index():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    # Registered last so it never shadows the /api/* routes above.
    @app.get("/{path:path}")
    def static_or_index(path: str):
        candidate = os.path.normpath(os.path.join(STATIC_DIR, path))
        # keep the traversal inside STATIC_DIR
        if candidate.startswith(os.path.normpath(STATIC_DIR)) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
