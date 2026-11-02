"""Single-process authenticated workspace change notifications for StudySync."""
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
connections: dict[int, set[WebSocket]] = defaultdict(set)


def authenticated_member(token: str, workspace_id: int) -> bool:
    secret = os.getenv('JWT_SECRET_KEY')
    if not secret:
        return False
    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'], options={'require': ['sub', 'exp']})
        user_id = int(payload['sub'])
    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        return False
    with SessionLocal() as db:
        return bool(db.get(User, user_id) and db.scalar(select(Membership.id).where(
            Membership.workspace_id == workspace_id, Membership.user_id == user_id)))


@router.websocket('/ws/workspaces/{workspace_id}')
async def workspace_events(websocket: WebSocket, workspace_id: int):
    await websocket.accept()
    try:
        first = await asyncio.wait_for(websocket.receive_json(), timeout=10)
        token = first.get('token') if isinstance(first, dict) else None
        if not isinstance(token, str) or not authenticated_member(token, workspace_id):
            await websocket.close(code=1008, reason='Authentication required')
            return
        connections[workspace_id].add(websocket)
        await websocket.send_json({'type': 'connected'})
        while True:
            data = await websocket.receive_json()
            if not authenticated_member(token, workspace_id):
                await websocket.close(code=1008, reason='Session expired or membership revoked')
                return
            if isinstance(data, dict) and data.get('type') == 'refresh':
                # Client sends this ONLY after a successful REST API mutation/commit.
                stale = []
                for other in list(connections[workspace_id]):
                    if other is websocket:
                        continue
                    try:
                        await other.send_json({'type': 'refresh', 'workspace_id': workspace_id})
                    except Exception:
                        stale.append(other)
                for other in stale:
                    connections[workspace_id].discard(other)
    except (WebSocketDisconnect, asyncio.TimeoutError, ValueError, RuntimeError):
        pass
    finally:
        connections[workspace_id].discard(websocket)
        if not connections[workspace_id]:
            connections.pop(workspace_id, None)
