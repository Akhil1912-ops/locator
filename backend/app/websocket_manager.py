from typing import Dict, Set
from fastapi import WebSocket
import json
from datetime import datetime, timezone


class WebSocketManager:
    """
    Manages WebSocket connections for real-time bus location updates.
    bus_number -> Set of WebSocket connections
    """
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, bus_number: str):
        """Add a new WebSocket connection for a bus"""
        await websocket.accept()
        if bus_number not in self.active_connections:
            self.active_connections[bus_number] = set()
        self.active_connections[bus_number].add(websocket)
        print(f"WebSocket connected for bus {bus_number}. Total connections: {len(self.active_connections.get(bus_number, set()))}")
    
    def disconnect(self, websocket: WebSocket, bus_number: str):
        """Remove a WebSocket connection"""
        if bus_number in self.active_connections:
            self.active_connections[bus_number].discard(websocket)
            if len(self.active_connections[bus_number]) == 0:
                del self.active_connections[bus_number]
        print(f"WebSocket disconnected for bus {bus_number}")
    
    async def broadcast_location(self, bus_number: str, location_data: dict):
        """Broadcast location update to all connected passengers for a bus"""
        if bus_number not in self.active_connections:
            return
        
        # Calculate last_seen_seconds
        recorded_at = location_data.get("recorded_at")
        if isinstance(recorded_at, str):
            try:
                recorded_at = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
            except:
                recorded_at = datetime.now(timezone.utc)
        elif isinstance(recorded_at, datetime):
            if recorded_at.tzinfo is None:
                recorded_at = recorded_at.replace(tzinfo=timezone.utc)
        else:
            recorded_at = datetime.now(timezone.utc)
        
        now = datetime.now(timezone.utc)
        last_seen_seconds = int((now - recorded_at).total_seconds())
        
        message = {
            "type": "location_update",
            "bus_number": bus_number,
            "latitude": location_data["latitude"],
            "longitude": location_data["longitude"],
            "recorded_at": location_data["recorded_at"].isoformat() if isinstance(location_data["recorded_at"], datetime) else location_data["recorded_at"],
            "last_seen_seconds": last_seen_seconds,
            "status": "online" if last_seen_seconds < 120 else "stale",
        }
        
        # Send to all connected clients
        disconnected = set()
        for connection in self.active_connections[bus_number]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to WebSocket: {e}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn, bus_number)
    
    async def broadcast_delay(self, bus_number: str, delay_data: dict):
        """Broadcast delay update to all connected passengers"""
        if bus_number not in self.active_connections:
            return
        
        message = {
            "type": "delay_update",
            "bus_number": bus_number,
            "delay_minutes": delay_data.get("delay_minutes", 0),
            "current_stop": delay_data.get("current_stop"),
            "next_stop": delay_data.get("next_stop"),
        }
        
        disconnected = set()
        for connection in self.active_connections[bus_number]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending delay update: {e}")
                disconnected.add(connection)
        
        for conn in disconnected:
            self.disconnect(conn, bus_number)
    
    def get_connection_count(self, bus_number: str) -> int:
        """Get number of connected passengers for a bus"""
        return len(self.active_connections.get(bus_number, set()))


# Global WebSocket manager instance
websocket_manager = WebSocketManager()

