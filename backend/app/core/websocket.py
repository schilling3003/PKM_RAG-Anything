"""
WebSocket connection manager for real-time updates.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket connection manager."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_info: Optional[Dict[str, Any]] = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Store connection info
        self.connection_info[websocket] = {
            "connected_at": datetime.utcnow(),
            "client_info": client_info or {},
            "subscriptions": set()
        }
        
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "message": "Connected to AI PKM Tool",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        if websocket in self.connection_info:
            del self.connection_info[websocket]
            
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any], subscription_filter: Optional[str] = None):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        message_text = json.dumps(message)
        disconnected_connections = []
        
        for connection in self.active_connections:
            try:
                # Check subscription filter
                if subscription_filter:
                    conn_info = self.connection_info.get(connection, {})
                    subscriptions = conn_info.get("subscriptions", set())
                    if subscription_filter not in subscriptions:
                        continue
                
                await connection.send_text(message_text)
                
            except Exception as e:
                logger.error(f"Failed to send broadcast message: {e}")
                disconnected_connections.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)
    
    async def subscribe(self, websocket: WebSocket, subscription: str):
        """Subscribe a connection to specific message types."""
        if websocket in self.connection_info:
            self.connection_info[websocket]["subscriptions"].add(subscription)
            logger.info(f"WebSocket subscribed to: {subscription}")
    
    async def unsubscribe(self, websocket: WebSocket, subscription: str):
        """Unsubscribe a connection from specific message types."""
        if websocket in self.connection_info:
            self.connection_info[websocket]["subscriptions"].discard(subscription)
            logger.info(f"WebSocket unsubscribed from: {subscription}")
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all active connections."""
        info = []
        for connection, data in self.connection_info.items():
            info.append({
                "connected_at": data["connected_at"].isoformat(),
                "client_info": data["client_info"],
                "subscriptions": list(data["subscriptions"])
            })
        return info


# Global connection manager instance
manager = ConnectionManager()


# Message broadcasting functions
async def broadcast_document_processing_update(document_id: str, status: str, progress: int = 0, 
                                             current_step: str = "", error: Optional[str] = None):
    """Broadcast document processing update."""
    message = {
        "type": "document_processing_update",
        "data": {
            "document_id": document_id,
            "status": status,
            "progress": progress,
            "current_step": current_step,
            "error": error
        }
    }
    await manager.broadcast(message, "document_processing")


async def broadcast_search_update(query: str, results_count: int, processing_time: float):
    """Broadcast search completion update."""
    message = {
        "type": "search_completed",
        "data": {
            "query": query,
            "results_count": results_count,
            "processing_time": processing_time
        }
    }
    await manager.broadcast(message, "search")


async def broadcast_knowledge_graph_update(node_count: int, edge_count: int):
    """Broadcast knowledge graph update."""
    message = {
        "type": "knowledge_graph_update",
        "data": {
            "node_count": node_count,
            "edge_count": edge_count
        }
    }
    await manager.broadcast(message, "knowledge_graph")


async def broadcast_system_status(status: str, message: str):
    """Broadcast system status update."""
    message = {
        "type": "system_status",
        "data": {
            "status": status,
            "message": message
        }
    }
    await manager.broadcast(message, "system")


async def handle_websocket_message(websocket: WebSocket, message: Dict[str, Any]):
    """Handle incoming WebSocket messages."""
    try:
        message_type = message.get("type")
        
        if message_type == "subscribe":
            subscription = message.get("subscription")
            if subscription:
                await manager.subscribe(websocket, subscription)
                await manager.send_personal_message({
                    "type": "subscription_confirmed",
                    "subscription": subscription
                }, websocket)
        
        elif message_type == "unsubscribe":
            subscription = message.get("subscription")
            if subscription:
                await manager.unsubscribe(websocket, subscription)
                await manager.send_personal_message({
                    "type": "unsubscription_confirmed",
                    "subscription": subscription
                }, websocket)
        
        elif message_type == "ping":
            await manager.send_personal_message({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
        
        else:
            logger.warning(f"Unknown WebSocket message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await manager.send_personal_message({
            "type": "error",
            "message": "Failed to process message"
        }, websocket)