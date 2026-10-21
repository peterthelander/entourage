"""Versioned API schemas. Device credentials and model settings are server concerns."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConversationInput(Input):
    title: str = Field(default="New conversation", min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Title must not be blank.")
        return value


class Conversation(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    sequence: int


class ConversationPage(BaseModel):
    items: list[Conversation]
    next_after: int | None


class TurnInput(Input):
    text: str = Field(min_length=1, max_length=16000)
    device_id: UUID

    @field_validator("text")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message must not be blank.")
        return value


class Turn(BaseModel):
    id: UUID
    conversation_id: UUID
    device_id: UUID
    status: Literal["queued", "running", "waiting_for_device", "completed", "failed", "needs_review"]
    revision: int
    created_at: datetime
    partial_answer: str
    answer: str | None
    error: str | None
    device_requests: list["DeviceRequest"] = Field(default_factory=list)


class DeviceRequest(BaseModel):
    id: UUID
    device_id: UUID
    name: str
    arguments: dict
    expires_at: float
    result: str | None


class DeviceRegistration(Input):
    key: str = Field(min_length=32, max_length=200)


class DeviceResult(Input):
    device_id: UUID
    content: str = Field(max_length=32000)


class Message(BaseModel):
    sequence: int
    conversation_id: UUID
    turn_id: UUID | None
    role: Literal["user", "assistant", "tool"]
    kind: Literal["user", "assistant", "tool", "error"]
    text: str
    created_at: datetime
    legacy_id: str | None


class MessagePage(BaseModel):
    items: list[Message]
    next_after: int | None


class LegacyMessage(Input):
    id: str = Field(min_length=1, max_length=200)
    role: Literal["user", "assistant"]
    text: str = Field(max_length=16000)
    createdAt: AwareDatetime | None = None


class HistoryImport(Input):
    messages: list[LegacyMessage] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def unique_ids(self) -> "HistoryImport":
        ids = [message.id for message in self.messages]
        if len(ids) != len(set(ids)):
            raise ValueError("Legacy message IDs must be unique.")
        return self


class ImportPreview(BaseModel):
    total: int
    users: int
    assistants: int
    tools: int
    errors: int
    skipped: int


class ImportReceipt(BaseModel):
    id: UUID
    conversation_id: UUID
    imported_count: int


def legacy_kind(message: LegacyMessage) -> str | None:
    if message.id == "welcome":
        return None
    if message.role == "user":
        return "user"
    if message.id.startswith("error-"):
        return "error"
    if message.id.startswith("toolresult-"):
        return "tool"
    return "assistant"


def preview_import(body: HistoryImport) -> ImportPreview:
    kinds = [legacy_kind(message) for message in body.messages]
    return ImportPreview(total=len(kinds), users=kinds.count("user"),
                         assistants=kinds.count("assistant"), tools=kinds.count("tool"),
                         errors=kinds.count("error"), skipped=kinds.count(None))
