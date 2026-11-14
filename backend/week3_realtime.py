"""Workspace-scoped single-process change notifications.

REST mutations commit before notifying; browser messages cannot forge refreshes.
For multiple workers use a shared broker rather than in-memory connections.
"""
import asyncio
import os
from collections import defaultdict

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from database import SessionLocal
from models import Membership, User

load_dotenv()
router = APIRouter()
# Each WebSocket is paired with its JWT and event loop.
connections: dict[int, dict[WebSocket, tuple[str, asyncio.AbstractEventLoop]]] = defaultdict(dict)


def authenticated_member(token: str, workspace_id: int) -> bool:
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        return False
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"], options={"require": ["sub", "exp"]})
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        return False
    with SessionLocal() as db:
        return bool(db.get(User, user_id) and db.scalar(select(Membership.id).where(
            Membership.workspace_id == workspace_id, Membership.user_id == user_id)))


async def _deliver(socket: WebSocket, token: str, workspace_id: int):
    # Check permissions at delivery time, not only at initial connection.
    if not authenticated_member(token, workspace_id):
        try:
            await socket.close(code=1008, reason="Membership revoked or session expired")
        except Exception:
            pass
        connections[workspace_id].pop(socket, None)
        return
    try:
        await socket.send_json({"type": "refresh", "workspace_id": workspace_id})
    except Exception:
        connections[workspace_id].pop(socket, None)


def publish_workspace_change(workspace_id: int):
    """Called from synchronous REST endpoints only AFTER db.commit().

    Threadsafe scheduling returns immediately. No browser can originate a broadcast.
    This is best-effort and intentionally single-process.
    """
    for socket, (token, loop) in list(connections.get(workspace_id, {}).items()):
        if loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(_deliver(socket, token, workspace_id), loop)
            except RuntimeError:
                pass


@router.websocket("/ws/workspaces/{workspace_id}")
async def workspace_events(websocket: WebSocket, workspace_id: int):
    await websocket.accept()
    token = None
    try:
        first = await asyncio.wait_for(websocket.receive_json(), timeout=10)
        token = first.get("token") if isinstance(first, dict) else None
        if not isinstance(token, str) or not authenticated_member(token, workspace_id):
            await websocket.close(code=1008, reason="Authentication required")
            return
        connections[workspace_id][websocket] = (token, asyncio.get_running_loop())
        await websocket.send_json({"type": "connected"})
        while True:
            # Clients can ping; they are NOT allowed to publish refresh events.
            msg = await websocket.receive_json()
            if not authenticated_member(token, workspace_id):
                await websocket.close(code=1008, reason="Session expired or membership revoked")
                return
            if isinstance(msg, dict) and msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except (WebSocketDisconnect, asyncio.TimeoutError, ValueError, RuntimeError):
        pass
    finally:
        connections[workspace_id].pop(websocket, None)
        if not connections[workspace_id]:
            connections.pop(workspace_id, None)
