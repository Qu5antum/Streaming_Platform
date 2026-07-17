from fastapi import WebSocketDisconnect, WebSocket
from uuid import UUID
import logging
from datetime import datetime, timezone

from src.services.stream_message_service import StreamMessageService
from src.services.stream_metric_serivce import StreamMetricService
from .websocket_conection_manager import ConnectionManager
from src.api.schemas.stream_message_schema import MessageRequest
from src.database.models import User

logger = logging.getLogger("websocket_service")


class WebSocketService:
    def __init__(
        self,
        websocket: WebSocket,
        stream_id: UUID,
        manager: ConnectionManager,
        message_service: StreamMessageService,
        metric_service: StreamMetricService,
    ):
        self.websocket = websocket
        self.stream_id = stream_id
        self.manager = manager
        self.message_service = message_service
        self.metric_service = metric_service

        self.user: User | None = None
        self.connected_at: datetime | None = None

    async def authenticate(self):
        self.user = None # add jwt autorization

    async def connect(self):
        await self.authenticate()

        await self.manager.connect(
            stream_id=self.stream_id,
            websocket=self.websocket,
            user=self.user,
        )

        self.connected_at = datetime.now(timezone.utc)

        await self.metric_service.viewer_connected(
            self.stream_id
        )

        await self.metric_service.register_view(
            self.stream_id
        )

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
        metrics = await self.metric_service.get_live_stream_metrics(
            self.stream_id
        )

        await self.manager.broadcast(
            self.stream_id,
            {
                "type": "viewer_count",
                "data": {
                    "count": metrics["current_viewers"]
                },
            },
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

        await self.metric_service.viewer_discconnected(
            self.stream_id,
        )

        if self.connected_at:

            seconds = int(
                (datetime.now(timezone.utc) - self.connected_at).total_seconds()
            )

            await self.metric_service.register_watch_session(
                self.stream_id,
                seconds,
            )

    async def chat(self):
        await self.connect()
        await self.send_history()
        await self.send_viewers_count()

        try:
            while True:
                payload = await self.websocket.receive_json()

                await self.process_message(payload)

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
            await self.disconnect()
            await self.send_viewers_count()