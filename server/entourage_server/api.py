"""Conversation, turn, and device APIs for the single-owner agent service."""

from uuid import UUID

from fastapi import APIRouter, Header, Query, Request, Response

from .models import (Conversation, ConversationInput, ConversationPage, HistoryImport,
                     ImportPreview, ImportReceipt, MessagePage, Turn, TurnInput, preview_import,
                     DeviceRegistration, DeviceResult)
from .storage import StoreError, SINGLE_CHAT_ID

router = APIRouter(prefix="/api/v1")


@router.put("/chat", response_model=Conversation)
def shared_chat(request: Request):
    """Resolve the same single thread for every browser and device."""
    return request.app.state.store.single_chat()


@router.put("/chat/imports/{import_id}", response_model=ImportReceipt)
def import_shared_history(import_id: UUID, body: HistoryImport, request: Request, response: Response):
    store = request.app.state.store
    store.single_chat()
    result, created = store.import_history(SINGLE_CHAT_ID, str(import_id), body, append=True)
    response.status_code = 201 if created else 200
    return result


@router.put("/conversations/{conversation_id}", response_model=Conversation)
def create_conversation(conversation_id: UUID, body: ConversationInput, request: Request, response: Response):
    result, created = request.app.state.store.create_conversation(str(conversation_id), body.title)
    response.status_code = 201 if created else 200
    return result


@router.get("/conversations", response_model=ConversationPage)
def list_conversations(request: Request, after: int = Query(0, ge=0, le=2**63 - 1), limit: int = Query(50, ge=1, le=100)):
    return request.app.state.store.list_conversations(after, limit)


@router.get("/conversations/{conversation_id}/messages", response_model=MessagePage)
def list_messages(conversation_id: UUID, request: Request, after: int = Query(0, ge=0, le=2**63 - 1), limit: int = Query(50, ge=1, le=100)):
    return request.app.state.store.list_messages(str(conversation_id), after, limit)


@router.put("/conversations/{conversation_id}/turns/{turn_id}", response_model=Turn,
            description="Persist a turn. Runs on the server when execution is enabled.")
def create_turn(conversation_id: UUID, turn_id: UUID, body: TurnInput, request: Request, response: Response):
    task = request.app.state.worker_task
    if request.app.state.settings.execution_enabled and (task is None or task.done()):
        raise StoreError(503, "worker_unavailable", "Agent worker is unavailable. Restart the service.")
    if request.app.state.settings.execution_enabled and not request.app.state.store.has_device(str(body.device_id)):
        raise StoreError(403, "device_unregistered", "Register the requesting device first.")
    _, created = request.app.state.store.create_turn(str(conversation_id), str(turn_id), body.text, str(body.device_id))
    response.status_code = 202 if created else 200
    return request.app.state.store.get_turn(str(turn_id))


@router.get("/turns/{turn_id}", response_model=Turn)
def get_turn(turn_id: UUID, request: Request):
    return request.app.state.store.get_turn(str(turn_id))


@router.put("/turns/{turn_id}/cancellation", response_model=Turn)
async def cancel_turn(turn_id: UUID, request: Request):
    request.app.state.store.cancel(str(turn_id))
    worker = request.app.state.worker
    if worker is not None:
        worker.cancel(str(turn_id))
    return request.app.state.store.get_turn(str(turn_id))


@router.put("/devices/{device_id}")
def register_device(device_id: UUID, body: DeviceRegistration, request: Request):
    request.app.state.store.register_device(str(device_id), body.key)
    return {"id": str(device_id)}


@router.put("/turns/{turn_id}/device-results/{request_id}")
def device_result(turn_id: UUID, request_id: UUID, body: DeviceResult, request: Request,
                  x_device_key: str = Header(min_length=32, max_length=200)):
    request.app.state.store.submit_device(str(turn_id), str(request_id), str(body.device_id), x_device_key, body.content)
    return {"accepted": True}


@router.get("/conversations/{conversation_id}/active-turn", response_model=Turn | None)
def active_turn(conversation_id: UUID, request: Request):
    return request.app.state.store.active_turn(str(conversation_id))


@router.get("/conversations/{conversation_id}/latest-turn", response_model=Turn | None)
def latest_turn(conversation_id: UUID, request: Request):
    return request.app.state.store.latest_turn(str(conversation_id))


@router.post("/import-preview", response_model=ImportPreview)
def import_preview(body: HistoryImport):
    """Classify legacy browser history without writing any data."""
    return preview_import(body)


@router.put("/conversations/{conversation_id}/imports/{import_id}", response_model=ImportReceipt)
def import_history(conversation_id: UUID, import_id: UUID, body: HistoryImport, request: Request, response: Response):
    """Explicit import only; original browser storage is not changed or deleted."""
    result, created = request.app.state.store.import_history(str(conversation_id), str(import_id), body)
    response.status_code = 201 if created else 200
    return result
