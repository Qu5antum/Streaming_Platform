from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from uuid import UUID
import logging

from src.database.db import AsyncSession, get_session
from src.database.models import User, UserRole
from src.api.dependencies.require_role_dependency import require_roles
from src.services.stream_message_service import StreamMessageService
from src.api.schemas.stream_message_schema import MessageRequest, MessageResponse
from src.websocket_server.websocket_conection_manager import ConnectionManager

logger = logging.getLogger("Websocket")

manager = ConnectionManager()


message_route = APIRouter(
    prefix="/api",
    tags=["Messages"]
)

async def get_stream_message_service(session: AsyncSession = Depends(get_session)):
    return StreamMessageService(session=session)


@message_route.post()


@message_route.get("/stream/{stream_id}/messages", response_model=list[MessageResponse], status_code=200)
async def get_all_messages(
    stream_id: UUID,
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.USER)),
    message_service: StreamMessageService = Depends(get_stream_message_service)
):
    return await message_service.get_messages_by_stream_id(stream_id=stream_id)


@message_route.websocket("/ws/streams/{stream_id}")
async def stream_chat(
    websocket: WebSocket,
    stream_id: UUID,
    message_service: StreamMessageService = Depends(get_stream_message_service),
):
    


