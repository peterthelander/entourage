"""Read server configuration at startup; never expose it through the public API."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    inference_provider: str = "ollama"
    llama_cpp_upstream: str = "http://127.0.0.1:8080"
    ollama_upstream: str = "http://127.0.0.1:11434"
    model: str = "qwen3.5:4b"
    database_path: Path = Path(__file__).resolve().parents[1] / "data" / "entourage.sqlite3"
    execution_enabled: bool = False
    api_token: str = ""
    tailscale_login: str = ""
    trust_local: bool = False
    allowed_origins: tuple[str, ...] = ("http://localhost:8081", "http://127.0.0.1:8081")
    device_timeout_seconds: int = 120
    journal_timezone: str | None = None
    context_tokens: int = 8192
    max_output_tokens: int = 1536
    context_session_gap_minutes: int = 60
    knowledge_enabled: bool = False
    gemini_api_key: str = field(default="", repr=False)
    web_search_model: str = "gemini-2.5-flash-lite"

    def __post_init__(self) -> None:
        if type(self.knowledge_enabled) is not bool:
            raise ValueError("knowledge_enabled must be a boolean.")
        if self.inference_provider not in ("ollama", "llama_cpp", "gemini"):
            raise ValueError("ENTOURAGE_INFERENCE_PROVIDER must be ollama, llama_cpp or gemini.")
        if not self.web_search_model or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._" for c in self.web_search_model):
            raise ValueError("ENTOURAGE_WEB_SEARCH_MODEL must be a model ID without a path.")
        self.validate_origin(self.llama_cpp_upstream, "ENTOURAGE_LLAMA_CPP_UPSTREAM")
        url = urlsplit(self.ollama_upstream)
        if (
            url.scheme not in ("http", "https")
            or not url.hostname
            or url.username is not None
            or url.password is not None
            or url.path not in ("", "/")
            or "?" in self.ollama_upstream
            or "#" in self.ollama_upstream
            or any(char.isspace() for char in self.ollama_upstream)
        ):
            raise ValueError("ENTOURAGE_OLLAMA_UPSTREAM must be an HTTP(S) origin without credentials or a path.")
        # Accessing port validates malformed and out-of-range ports.
        if url.port == 0:
            raise ValueError("Ollama port must be greater than zero.")
        if self.inference_provider == "gemini" and self.execution_enabled and not self.gemini_api_key.strip():
            raise ValueError("Gemini inference requires a server-side API key.")
        if not self.model.strip():
            raise ValueError("ENTOURAGE_MODEL must not be empty.")
        if self.execution_enabled and not self.trust_local and len(self.api_token) < 32:
            raise ValueError("Execution requires ENTOURAGE_API_TOKEN with at least 32 characters.")
        if self.device_timeout_seconds < 1:
            raise ValueError("Device timeout must be positive.")
        if type(self.context_tokens) is not int or not 2048 <= self.context_tokens <= 262144:
            raise ValueError("ENTOURAGE_CONTEXT_TOKENS must be an integer from 2048 to 262144.")
        if (type(self.max_output_tokens) is not int or self.max_output_tokens < 1
                or self.max_output_tokens > self.context_tokens // 2):
            raise ValueError("ENTOURAGE_MAX_OUTPUT_TOKENS must be positive and at most half the context window.")
        if type(self.context_session_gap_minutes) is not int or not 1 <= self.context_session_gap_minutes <= 1440:
            raise ValueError("ENTOURAGE_CONTEXT_SESSION_GAP_MINUTES must be an integer from 1 to 1440.")

    @classmethod
    def from_environment(cls) -> "Settings":
        knowledge_flag = os.environ.get("ENTOURAGE_KNOWLEDGE_ENABLED", "0")
        if knowledge_flag not in ("0", "1"):
            raise ValueError("ENTOURAGE_KNOWLEDGE_ENABLED must be 0 or 1.")
        key = (os.environ.get("ENTOURAGE_GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY", "")).strip()
        key_file = Path(__file__).resolve().parents[1] / "data" / "gemini-api-key.txt"
        if not key and key_file.exists():
            key = key_file.read_text(encoding="utf-8").strip()
        return cls(
            gemini_api_key=key,
            web_search_model=os.environ.get("ENTOURAGE_WEB_SEARCH_MODEL", cls.web_search_model),
            inference_provider=os.environ.get("ENTOURAGE_INFERENCE_PROVIDER", cls.inference_provider),
            llama_cpp_upstream=os.environ.get("ENTOURAGE_LLAMA_CPP_UPSTREAM", cls.llama_cpp_upstream),
            ollama_upstream=os.environ.get("ENTOURAGE_OLLAMA_UPSTREAM") or cls.ollama_upstream,
            model=os.environ.get("ENTOURAGE_MODEL", cls.model),
            journal_timezone=os.environ.get("ENTOURAGE_JOURNAL_TIMEZONE") or None,
            context_tokens=int(os.environ.get("ENTOURAGE_CONTEXT_TOKENS", cls.context_tokens)),
            max_output_tokens=int(os.environ.get("ENTOURAGE_MAX_OUTPUT_TOKENS", cls.max_output_tokens)),
            context_session_gap_minutes=int(os.environ.get(
                "ENTOURAGE_CONTEXT_SESSION_GAP_MINUTES", cls.context_session_gap_minutes)),
            knowledge_enabled=knowledge_flag == "1",
            database_path=Path(os.environ["ENTOURAGE_DATABASE_PATH"]) if os.environ.get("ENTOURAGE_DATABASE_PATH") else cls.database_path,
            execution_enabled=os.environ.get("ENTOURAGE_EXECUTION_ENABLED", "0") == "1",
            api_token=os.environ.get("ENTOURAGE_API_TOKEN", ""),
            tailscale_login=os.environ.get("ENTOURAGE_TAILSCALE_LOGIN", ""),
            allowed_origins=tuple(value.strip() for value in os.environ.get(
                "ENTOURAGE_ALLOWED_ORIGINS", ",".join(cls.allowed_origins)).split(",") if value.strip()),
        )

    @staticmethod
    def validate_origin(value, name):
        url = urlsplit(value)
        if (url.scheme not in ("http", "https") or not url.hostname or url.username is not None
                or url.password is not None or url.path not in ("", "/") or "?" in value
                or "#" in value or any(char.isspace() for char in value) or url.port == 0):
            raise ValueError(f"{name} must be an HTTP(S) origin without credentials or a path.")
