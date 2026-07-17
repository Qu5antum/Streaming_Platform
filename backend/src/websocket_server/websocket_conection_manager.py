from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict
from uuid import UUID
import asyncio
from fastapi import WebSocket
import logging

from src.database.models import User

logger = logging.getLogger("websocket_connection_manager")


@dataclass(slots=True)
class ClientConnection:
    websocket: WebSocket
    user: User
    connected_at: datetime


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID, set[ClientConnection]] = {}

    async def connect(self, stream_id: UUID, websocket: WebSocket, user: User) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()

        connection = ClientConnection(
            websocket=websocket,
            user=user,
            connected_at=datetime.now(timezone.utc),
        )

        self.active_connections.setdefault(stream_id, set()).add(connection)

        logger.info(
            "Client connected",
            extra={
                "stream_id": str(stream_id),
                "viewers": len(self.active_connections[stream_id]),
                "user_id": str(user.id),
            },
        )

    async def disconnect(self, stream_id: UUID, websocket: WebSocket) -> None:
        """Remove a disconnected client."""
        connections = self.active_connections.get(stream_id)

        if not connections:
            return

        connection = next(
            (
                conn
                for conn in connections
                if conn.websocket is websocket
            ),
            None,
        )

        if connection:
            connections.remove(connection)

        if not connections:
            self.active_connections.pop(stream_id, None)

        logger.info(
            "Client disconnected",
            extra={
                "stream_id": str(stream_id),
                "viewers": len(self.active_connections.get(stream_id, ())),
            },
        )

    async def send_personal_message(self, websocket: WebSocket, message: dict) -> bool:
        """Send a message to one client."""
        try:
            await websocket.send_json(message)
            return True

        except Exception:
            logger.exception("Failed to send websocket message")
            return False

    async def broadcast(self, stream_id: UUID, message: dict) -> None:
        """Send a message to every client in a stream."""
        connections = list(self.active_connections.get(stream_id, ()))

        if not connections:
            return

        results = await asyncio.gather(
            *(
                self.send_personal_message(
                    connection.websocket,
                    message,
                )
                for connection in connections
            )
        )

        for connection, success in zip(connections, results):
            if not success:
                await self.disconnect(
                    stream_id,
                    connection.websocket,
                )

    def get_viewers_count(self, stream_id: UUID) -> int:
        """Return current number of viewers."""
        return len(self.active_connections.get(stream_id, ()))