from backend.src import redis
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from uuid import UUID
import logging

from src.database.db import AsyncSession, get_session
from src.database.models import User, UserRole
from src.api.dependencies.require_role_dependency import require_roles
from src.services.stream_message_service import StreamMessageService
from src.api.schemas.stream_message_schema import MessageRequest, MessageResponse
from src.websocket_server.websocket_conection_manager import ConnectionManager
from src.redis.redis_service import RedisService
from src.websocket_server.websocket_service import WebSocketService
from src.services.stream_metric_serivce import StreamMetricService

logger = logging.getLogger("Websocket")

manager = ConnectionManager()
redis_service = RedisService()


message_route = APIRouter(
    prefix="/api",
    tags=["Messages"]
)

async def get_stream_message_service(session: AsyncSession = Depends(get_session)):
    return StreamMessageService(session=session, redis_service=redis_service)

async def get_stream_metric_service(session: AsyncSession = Depends(get_session)):
    return StreamMetricService(session=session, redis_service=redis_service)


@message_route.post("/stream/{stream_id}/message/new", response_model=MessageResponse, status_code=201)
async def new_message(
    stream_id: UUID,
    message_request: MessageRequest,
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.USER)),
    message_service: StreamMessageService = Depends(get_stream_message_service)
):
    return await message_service.add_new_message(stream_id=stream_id, user=user, message=message_request)


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
    metric_service: StreamMetricService = Depends(get_stream_metric_service),
):
    await WebSocketService(
        websocket=websocket,
        stream_id=stream_id,
        manager=manager,
        message_service=message_service,
        metric_service=metric_service,
    ).chat()
