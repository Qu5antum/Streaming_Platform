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
        """Отправка сообщения конкретному пользователю с защитой от обрыва связи."""
        try:
            await websocket.send_json(message)  
        except Exception:
            pass

    async def broadcast(self, stream_id: UUID, message: str):
        """Broadcast a message to all currently connected clients simultaneously."""
        connections = self.active_connections.get(stream_id)

        if not connections:
            return
        
        logger.info(f"Broadcasting message to {len(connections)} clients in stream {stream_id}")

        await asyncio.gather(
            *[
                self.send_personal_message(message, ws)
                for ws in list(connections)
            ],
            return_exceptions=True 
        )
