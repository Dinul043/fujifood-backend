"""
WebSocket Routes — Real-time connection endpoints.

Endpoints:
  WS /ws/admin/{tenant_id}     → Restaurant admin dashboard (new orders, status updates)
  WS /ws/customer/{user_id}    → Customer order tracking (status changes)
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket_manager import ws_manager

router = APIRouter()


@router.websocket("/ws/admin/{tenant_id}")
async def ws_admin_dashboard(websocket: WebSocket, tenant_id: int):
    """
    WebSocket for restaurant admin dashboard.
    
    Receives events:
      - new_order: When a new order is placed
      - order_cancelled: When customer cancels an order
    
    Heartbeat: Client sends "ping", server responds "pong"
    """
    await ws_manager.connect_admin(websocket, tenant_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect_admin(websocket, tenant_id)


@router.websocket("/ws/customer/{user_id}")
async def ws_customer_tracking(websocket: WebSocket, user_id: int):
    """
    WebSocket for customer order tracking.
    
    Receives events:
      - order_status_updated: When admin changes order status
    
    Heartbeat: Client sends "ping", server responds "pong"
    """
    await ws_manager.connect_customer(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect_customer(websocket, user_id)
