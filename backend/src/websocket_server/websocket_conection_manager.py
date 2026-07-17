import asyncio
import logging
from uuid import UUID
from typing import Dict, Set
from websockets.asyncio.server import ServerConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("conection_manager")


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID, Set['ServerConnection']] = {}

    async def connect(self, stream_id: UUID, websocket: 'ServerConnection'):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()    

        if stream_id not in self.active_connections:
            self.active_connections[stream_id] = set()

        self.active_connections[stream_id].add(websocket)      

        viewers_count = len(self.active_connections[stream_id])
        logger.info(f"New client connected to stream {stream_id}. Channel viewers: {viewers_count}")

    async def disconnect(self, stream_id: UUID, websocket: 'ServerConnection'):
        """Remove a disconnected client from the manager."""
        if stream_id in self.active_connections:
            self.active_connections[stream_id].discard(websocket)

            if not self.active_connections[stream_id]:
                del self.active_connections[stream_id]

        logger.info(f"Client disconnected. Active streams remaining: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: 'ServerConnection'):
        """Sending a message to a specific user with protection against connection loss."""
        try:
            await websocket.send_json(message)  
            return True
        except Exception:
            return False

    async def broadcast(self, stream_id: UUID, message: str):
        """Broadcast a message to all currently connected clients simultaneously."""
        connections = list(self.active_connections.get(stream_id, ()))

        if not connections:
            return

        results = await asyncio.gather(
            *(self.send_personal_message(message, ws) for ws in connections)
        )

        for ws, success in zip(connections, results):
            if not success:
                await self.disconnect(stream_id, ws)
