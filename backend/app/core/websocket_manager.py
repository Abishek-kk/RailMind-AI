from fastapi import WebSocket
from typing import List, Dict, Any
import logging

logger = logging.getLogger("railmind")

class ConnectionManager:
    def __init__(self):
        # Keeps active WebSocket channels stored securely in memory
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accepts an incoming client handshake connection stream."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New client connected to Live Stream. Active Channels: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Safely tears down tracking references for disconnected sessions."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected from Live Stream. Remaining Channels: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Sends a direct payload to a specific client channel console."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to transmit direct frame channel message: {e}")
            self.disconnect(websocket)

    async def broadcast_detection(self, payload: Dict[str, Any]):
        """
        Asynchronously broadcasts live frames, skeletal metadata, and 
        critical risk scores to all connected dashboard displays simultaneously.
        """
        if not self.active_connections:
            return

        # Create a shallow copy list iteration loop to prevent mutate-on-yield runtime errors
        disconnected_clients = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except Exception as e:
                logger.error(f"Broadcast failure to connection pipeline frame channel: {e}")
                disconnected_clients.append(connection)

        # Clean out dropped connection links cleanly outside standard tracking loops
        for connection in disconnected_clients:
            self.disconnect(connection)

manager = ConnectionManager()