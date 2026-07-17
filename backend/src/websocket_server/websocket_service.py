from fastapi import WebSocketDisconnect, WebSocket
from uuid import UUID
from websockets.asyncio.server import ServerConnection

from src.database.db import AsyncSession


class WebSocketService:
    def __init__(self, session: AsyncSession, websocket: WebSocket):
        self.session = session   
        self.websocket = websocket     

    async def authenticate():
        pass

    async def connect():
        pass

    async def send_history():
        pass

    async def send_viewers_count():
        pass

    async def process_message():
        pass

    async def disconnect():
        pass

    async def chat(self, stream_id: UUID):
        await self.connect()

        await self.send_history()

        await self.send_viewers_count()

        await manager.connect(stream_id, self.websocket)

        try:
            while True:
                payload = await self.websocket.receive_json()

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
            await manager.disconnect(stream_id, self.websocket)