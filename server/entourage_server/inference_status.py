"""Read-only llama.cpp model verification, separate from process liveness."""

from typing import Literal

import httpx
from pydantic import BaseModel


class InferenceStatus(BaseModel):
    status: Literal["ready", "configured", "model_mismatch", "unavailable"]
    configured_model: str
    loaded_model: str | None = None
    message: str | None = None


async def inference_status(settings, client):
    if not settings.execution_enabled:
        return InferenceStatus(status="unavailable", configured_model=settings.model,
                               message="Agent execution is disabled on the server.")
    if settings.inference_provider != "llama_cpp":
        return InferenceStatus(status="configured", configured_model=settings.model)
    try:
        response = await client.get(settings.llama_cpp_upstream.rstrip("/") + "/v1/models", timeout=5)
        response.raise_for_status()
        data = response.json()["data"]
        if not isinstance(data, list) or not data:
            raise ValueError("No loaded model")
        for item in data:
            identity = item.get("id")
            aliases = item.get("aliases", [])
            if not isinstance(identity, str) or not identity or not isinstance(aliases, list):
                raise ValueError("Malformed model metadata")
            if settings.model == identity or settings.model in aliases:
                return InferenceStatus(status="ready", configured_model=settings.model, loaded_model=identity)
        return InferenceStatus(status="model_mismatch", configured_model=settings.model,
                               loaded_model=data[0]["id"] if len(data) == 1 else None,
                               message="The configured model does not match the inference server. Update the agent's model setting and restart the agent.")
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
        return InferenceStatus(status="unavailable", configured_model=settings.model,
                               message="Cannot verify the inference server. Check that it is running and reachable.")
