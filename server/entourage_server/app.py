"""Durable API with opt-in server-owned execution alongside the legacy path."""

from contextlib import asynccontextmanager
from contextlib import suppress
import asyncio
import sqlite3
from typing import Literal

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
import httpx

from .api import router
from .body_limit import BodyLimit
from .config import Settings
from .storage import StoreError
from .execution_store import ExecutionStore
from .agent import Ollama, Worker
from .llama_cpp import LlamaCpp
from .access import AccessControl
from .worker_lock import worker_lock
from .journal_refresh import JournalRefresh


class HealthResponse(BaseModel):
    status: Literal["ok", "unavailable"] = "ok"
    api_version: Literal["v1"] = "v1"
    stage: Literal["persistence", "execution"] = "persistence"
    execution_enabled: bool = False
    model: str | None = None
    capabilities: list[str] = Field(default_factory=lambda: ["conversations", "history_import", "queued_turns"])


def create_app(settings: Settings | None = None, model=None) -> FastAPI:
    config = settings if settings is not None else Settings.from_environment()
    store = ExecutionStore(config.database_path)

    @asynccontextmanager
    async def lifespan(app):
        store.initialize()
        if not config.execution_enabled:
            yield
            return
        with worker_lock(config.database_path):
            store.recover()
            async with httpx.AsyncClient(timeout=httpx.Timeout(120), trust_env=False) as client:
                refresh = JournalRefresh(store, config.journal_timezone)
                stop_refresh = asyncio.Event()
                refresh_task = asyncio.create_task(refresh.run(stop_refresh))
                transport = LlamaCpp if config.inference_provider == "llama_cpp" else Ollama
                worker = Worker(store, config, model or transport(config, client), refresh)
                app.state.worker = worker
                task = asyncio.create_task(worker.run())
                app.state.worker_task = task
                try:
                    yield
                finally:
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        await task
                    stop_refresh.set()
                    await refresh_task

    app = FastAPI(
        title="Entourage Agent Server",
        version="0.3.0",
        description="Durable conversations and opt-in server-owned agent execution.",
        lifespan=lifespan,
    )
    app.state.settings = config
    app.state.store = store
    app.state.worker = None
    app.state.worker_task = None
    app.add_middleware(BodyLimit)
    app.add_middleware(AccessControl, token=config.api_token, origins=config.allowed_origins,
                       tailscale_login=config.tailscale_login, trust_local=config.trust_local)
    app.add_middleware(CORSMiddleware, allow_origins=list(config.allowed_origins),
                       allow_methods=["GET", "PUT", "POST"], allow_headers=["Authorization", "Content-Type", "X-Device-Key"])
    app.include_router(router)

    @app.exception_handler(StoreError)
    async def store_error(_request: Request, error: StoreError):
        return JSONResponse(status_code=error.status, content={"error": {"code": error.code, "message": error.message}})

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, _error: RequestValidationError):
        # Do not echo submitted conversation text in error responses/logs.
        return JSONResponse(status_code=422, content={"error": {"code": "invalid_request", "message": "Request does not match the API schema."}})

    @app.exception_handler(HTTPException)
    async def http_error(_request: Request, error: HTTPException):
        return JSONResponse(status_code=error.status_code, headers=error.headers,
                            content={"error": {"code": "http_error", "message": str(error.detail)}})

    @app.exception_handler(sqlite3.OperationalError)
    async def database_error(_request: Request, _error: sqlite3.OperationalError):
        return JSONResponse(status_code=503, content={"error": {"code": "storage_unavailable", "message": "Storage is temporarily unavailable."}})

    @app.get("/api/v1/health", response_model=HealthResponse)
    def health(response: Response) -> HealthResponse:
        """Process liveness only; does not test Ollama or promise chat readiness."""
        unavailable = config.execution_enabled and (app.state.worker_task is None or app.state.worker_task.done())
        if unavailable:
            response.status_code = 503
        return HealthResponse(status="unavailable" if unavailable else "ok", stage="execution" if config.execution_enabled else "persistence",
                              execution_enabled=config.execution_enabled, model=config.model if config.execution_enabled else None,
                              capabilities=["conversations", "history_import", "queued_turns"] +
                              (["agent_execution", "device_tools"] if config.execution_enabled else []))

    return app
