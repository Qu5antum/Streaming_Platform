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
    await manager.connect(stream_id, websocket)

    try:
        while True:
            payload = await websocket.receive_json()

            message = await message_service.add_new_message(
                stream_id=stream_id,
                user=None,  # заменить после добавления авторизации
                message=MessageRequest(**payload),
            )

            await manager.broadcast(
                stream_id,
                {
                    "type": "chat_message",
                    "data": MessageResponse.model_validate(message).model_dump(mode="json"),
                },
            )

    except WebSocketDisconnect:
        logger.info(
            "Client disconnected",
            extra={"stream_id": str(stream_id)}
        )

    except Exception:
        logger.exception(
            "Unexpected websocket error",
            extra={"stream_id": str(stream_id)}
        )

    finally:
        await manager.disconnect(stream_id, websocket)


