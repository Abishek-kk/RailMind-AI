from fastapi import WebSocket
from typing import List, Dict, Any
import logging

logger = logging.getLogger("railmind")

class ConnectionManager:
    def __init__(self):
        # Keeps active WebSocket channels stored securely in memory
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.websocket_channels: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, channel: str = "alerts"):
        """Accepts an incoming client handshake connection stream."""
        await websocket.accept()
        self.active_connections.setdefault(channel, []).append(websocket)
        self.websocket_channels[websocket] = channel
        logger.info(
            f"New client connected to channel '{channel}'. "
            f"Active clients on channel: {len(self.active_connections[channel])}"
        )

    def disconnect(self, websocket: WebSocket):
        """Safely tears down tracking references for disconnected sessions."""
        channel = self.websocket_channels.pop(websocket, None)
        if not channel:
            return

        connections = self.active_connections.get(channel)
        if not connections:
            return

        if websocket in connections:
            connections.remove(websocket)
            logger.info(
                f"Client disconnected from channel '{channel}'. "
                f"Remaining clients on channel: {len(connections)}"
            )

        if not connections:
            self.active_connections.pop(channel, None)

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Sends a direct payload to a specific client channel console."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to transmit direct frame channel message: {e}")
            self.disconnect(websocket)

    async def broadcast_detection(self, payload: Dict[str, Any], channel: str = "alerts"):
        """
        Asynchronously broadcasts live frames, skeletal metadata, and 
        critical risk scores to all connected dashboard displays simultaneously.
        """
        connections = list(self.active_connections.get(channel, []))
        if not connections:
            return

        disconnected_clients: List[WebSocket] = []
        
        for connection in connections:
            try:
                await connection.send_json(payload)
            except Exception as e:
                logger.error(f"Broadcast failure to connection pipeline frame channel '{channel}': {e}")
                disconnected_clients.append(connection)

        for connection in disconnected_clients:
            self.disconnect(connection)

manager = ConnectionManager()