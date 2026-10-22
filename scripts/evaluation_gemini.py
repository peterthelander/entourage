"""Evaluation credential loading; inference uses the production Gemini adapter."""

import os
from pathlib import Path

from entourage_server.gemini import Gemini as GeminiEvaluation, GeminiHTTPError


def evaluation_key(root: Path):
    key = (os.environ.get("ENTOURAGE_GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY") or "").strip()
    if not key:
        path = root / "server/data/gemini-api-key.txt"
        key = path.read_text(encoding="utf-8").strip() if path.exists() else ""
    if not key:
        raise ValueError("Gemini evaluation requires the existing private API key.")
    return key
