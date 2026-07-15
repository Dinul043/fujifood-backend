"""
WebSocket Manager — Real-time communication for FujiFood.

Manages connections for:
  - Tenant admins (restaurant dashboard) — receives new orders, status updates
  - Customers (order tracking) — receives order status changes

Design:
  - Connections stored by tenant_id (admin) or user_id (customer)
  - Automatic cleanup on disconnect
  - Broadcast to all connections of a user/tenant
"""
from typing import Dict, Set
from fastapi import WebSocket
import json


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # Admin connections: tenant_id → set of WebSocket connections
        self.admin_connections: Dict[int, Set[WebSocket]] = {}
        # Customer connections: user_id → set of WebSocket connections
        self.customer_connections: Dict[int, Set[WebSocket]] = {}

    # ─── Admin (Restaurant Dashboard) ─────────────────────────────

    async def connect_admin(self, websocket: WebSocket, tenant_id: int):
        """Connect admin dashboard for real-time order notifications."""
        await websocket.accept()
        if tenant_id not in self.admin_connections:
            self.admin_connections[tenant_id] = set()
        self.admin_connections[tenant_id].add(websocket)

    def disconnect_admin(self, websocket: WebSocket, tenant_id: int):
        """Disconnect admin dashboard."""
        if tenant_id in self.admin_connections:
            self.admin_connections[tenant_id].discard(websocket)
            if not self.admin_connections[tenant_id]:
                del self.admin_connections[tenant_id]

    async def notify_admin(self, tenant_id: int, event: str, data: dict):
        """Send notification to all admin connections for a tenant."""
        if tenant_id not in self.admin_connections:
            return
        message = {"event": event, "data": data}
        disconnected = set()
        for ws in self.admin_connections[tenant_id]:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.add(ws)
        for ws in disconnected:
            self.admin_connections[tenant_id].discard(ws)

    # ─── Customer (Order Tracking) ────────────────────────────────

    async def connect_customer(self, websocket: WebSocket, user_id: int):
        """Connect customer for order status updates."""
        await websocket.accept()
        if user_id not in self.customer_connections:
            self.customer_connections[user_id] = set()
        self.customer_connections[user_id].add(websocket)

    def disconnect_customer(self, websocket: WebSocket, user_id: int):
        """Disconnect customer."""
        if user_id in self.customer_connections:
            self.customer_connections[user_id].discard(websocket)
            if not self.customer_connections[user_id]:
                del self.customer_connections[user_id]

    async def notify_customer(self, user_id: int, event: str, data: dict):
        """Send notification to a specific customer."""
        if user_id not in self.customer_connections:
            return
        message = {"event": event, "data": data}
        disconnected = set()
        for ws in self.customer_connections[user_id]:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.add(ws)
        for ws in disconnected:
            self.customer_connections[user_id].discard(ws)


# Singleton instance
ws_manager = WebSocketManager()
