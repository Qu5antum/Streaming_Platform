import asyncio
import logging
from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("conection_manager")


class ConnectionManager:
    def __init__(self):
        # Store active connections in a set for O(1) tracking
        self.active_connections: set[ServerConnection] = set()

    async def connect(self, websocket: ServerConnection):
        """Accept and register a new WebSocket connection."""
        self.active_connections.add(websocket)

        logger.info(f"New client connected. Total connected: {len(self.active_connections)}")

    async def disconnect(self, websocket: ServerConnection):
        """Remove a disconnected client from the manager."""
        self.active_connections.remove(websocket)

        logger.info(f"Client disconnected. Total connected: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: ServerConnection):
        """Send a direct message to a single specific client."""
        try:
            await websocket.send(message)
        except ConnectionClosed:
            await self.disconnect(websocket)

    async def broadcast(self, message: str):
        """Broadcast a message to all currently connected clients simultaneously."""
        if not self.active_connections:
            return

        logger.info(f"Broadcasting message to {len(self.active_connections)} clients")
        
        # Use asyncio.gather to send messages concurrently across connections
        tasks = [
            self.send_personal_message(message, connection)
            for connection in self.active_connections
        ]

        await asyncio.gather(*tasks, return_exceptions=True)
