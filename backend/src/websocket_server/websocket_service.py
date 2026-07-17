from fastapi import WebSocketDisconnect, WebSocket
from uuid import UUID
from websockets.asyncio.server import ServerConnection
import logging

from src.database.db import AsyncSession
from src.services.stream_message_service import StreamMessageService
from .websocket_conection_manager import ConnectionManager
from src.api.schemas.stream_message_schema import MessageResponse, MessageRequest

logger = logging.getLogger("websocket_service")


class WebSocketService:
    def __init__(
        self,
        websocket: WebSocket,
        stream_id: UUID,
        message_service: StreamMessageService,
        manager: ConnectionManager,
    ):
        self.websocket = websocket
        self.stream_id = stream_id
        self.message_service = message_service
        self.manager = manager

        self.user = None 

    async def authenticate(self):
        self.user = None # add jwt autorization

    async def connect(self):
        pass

    async def send_history(self):
        messages = await self.message_service.get_messages_by_stream_id(
            self.stream_id
        )

        await self.websocket.send_json(
            {
                "type": "history",
                "data": [
                    message.model_dump(mode="json")
                    for message in messages
                ],
            }
        )

    async def send_viewers_count(self):
        await self.websocket.send_json(
            {
                "type": "viewer_count",
                "data": {
                    "count": self.manager.get_viewers_count(
                        self.stream_id
                    )
                },
            }
        )

    async def process_message(self, payload):
        message = await self.message_service.add_new_message(
            stream_id=self.stream_id,
            user=self.user,
            message=MessageRequest(**payload),
        )

        await self.manager.broadcast(
            self.stream_id,
            {
                "type": "chat_message",
                "data": message.model_dump(mode="json"),
            },
        )

    async def disconnect(self):
        await self.manager.disconnect(
            self.stream_id,
            self.websocket,
        )

    async def chat(self):
        await self.connect()

        await self.send_history()

        await self.send_viewers_count()

        await self.manager.connect(self.stream_id, self.websocket)

        try:
            while True:
                payload = await self.websocket.receive_json()

                message = await self.message_service.add_new_message(
                    stream_id=self.stream_id,
                    user=self.user,
                    message=MessageRequest(**payload),
                )

                await self.manager.broadcast(
                    self.stream_id,
                    {
                        "type": "chat_message",
                        "data": MessageResponse.model_validate(message).model_dump(mode="json"),
                    },
                )

        except WebSocketDisconnect:
            logger.info(
                "Client disconnected",
                extra={"stream_id": str(self.stream_id)}
            )

        except Exception:
            logger.exception(
                "Unexpected websocket error",
                extra={"stream_id": str(self.stream_id)}
            )

        finally:
            await self.manager.disconnect(self.stream_id, self.websocket)