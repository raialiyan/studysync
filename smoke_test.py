#!/usr/bin/env python3
"""StudySync Docker end-to-end smoke test. Only targets the loopback server.

Requires: Python 3.10+, websockets>=14,<17.
Does not delete any existing workspaces or users. Creates a unique temporary
workspace and attempts to remove that workspace on exit; test users remain.
"""
import json
import sys
import uuid
import urllib.error
import urllib.request
from contextlib import ExitStack
from urllib.parse import urlparse

API = 'http://127.0.0.1:8000'
WEB = 'http://127.0.0.1:5173'
WS = 'ws://127.0.0.1:8000'
PASSWORD = 'StudySyncTesting123!'
passed = 0


def req(method, path, *, token=None, body=None, expected=200, url=API):
    headers = {'Accept': 'application/json'}
    data = None
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if body is not None:
        data = json.dumps(body).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(url + path, headers=headers, method=method, data=data)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            status = response.status
            raw = response.read()
            content_type = response.headers.get('Content-Type','')
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read()
        content_type = exc.headers.get('Content-Type','')
    except urllib.error.URLError as exc:
        raise AssertionError(f'{url}{path} unreachable: {exc.reason}') from exc
    if status != expected:
        message = raw.decode('utf-8','replace')[:350]
        raise AssertionError(f'{method} {path}: expected HTTP {expected}, got {status}: {message}')
    if 'application/json' in content_type and raw:
        return json.loads(raw)
    return raw.decode('utf-8','replace') if raw else None


def check(label, callback):
    global passed
    callback()
    passed += 1
    print(f'  PASS  {label}', flush=True)


def ensure(condition, explanation):
    if not condition:
        raise AssertionError(explanation)


def register_and_login(suffix):
    email = f'studysync-smoke-{suffix}-{uuid.uuid4().hex[:12]}@example.com'
    req('POST','/register',body={'email':email,'password':PASSWORD},expected=201)
    login = req('POST','/login',body={'email':email,'password':PASSWORD})
    token = login['access_token']
    user_id = req('GET','/users/me',token=token)['id']
    return email, token, user_id


def main():
    global passed
    try:
        from websockets.sync.client import connect
    except ImportError as exc:
        print('MISSING DEPENDENCY: install websockets with python -m pip install "websockets>=14,<17"')
        raise SystemExit(2) from exc
    workspace_id = None
    owner_token = None
    task_id = None
    try:
        print('StudySync Docker smoke-test — localhost only', flush=True)
        check('FastAPI health endpoint', lambda: ensure(req('GET','/health')['status'] == 'ok','Health did not return ok'))
        check('React HTML served by frontend container', lambda: ensure('<html' in req('GET','/',url=WEB).lower(),'Expected HTML from frontend'))
        check('FastAPI OpenAPI schema', lambda: ensure('/register' in req('GET','/openapi.json')['paths'],'OpenAPI routes missing'))
        owner_email, owner_token, owner_id = register_and_login('owner')
        passed += 1; print('  PASS  Owner registration, login and JWT identity', flush=True)
        member_email, member_token, member_id = register_and_login('member')
        passed += 1; print('  PASS  Second user registration and login', flush=True)
        outsider_email, outsider_token, outsider_id = register_and_login('outsider')
        passed += 1; print('  PASS  Third user registration and login', flush=True)
        req('GET','/workspaces',expected=401)
        passed += 1; print('  PASS  Protected API denies unauthenticated request', flush=True)
        workspace = req('POST','/workspaces',token=owner_token,body={'name':'Docker Smoke '+uuid.uuid4().hex[:8]},expected=201)
        workspace_id = workspace['id']
        ensure(any(w['id']==workspace_id for w in req('GET','/workspaces',token=owner_token)),'Owner cannot list workspace')
        req('GET',f'/workspaces/{workspace_id}',token=outsider_token,expected=404)
        passed += 1; print('  PASS  Create workspace, list workspace, isolate outsiders', flush=True)
        req('POST',f'/workspaces/{workspace_id}/members',token=owner_token,body={'email':member_email},expected=201)
        members = req('GET',f'/workspaces/{workspace_id}/members',token=member_token)
        ensure(any(x['user_id']==member_id for x in members),'Invited user missing from workspace')
        req('POST',f'/workspaces/{workspace_id}/members',token=member_token,body={'email':outsider_email},expected=403)
        passed += 1; print('  PASS  Add member and enforce owner-only permissions', flush=True)
        module = req('POST',f'/workspaces/{workspace_id}/modules',token=owner_token,body={'name':'Software Engineering'},expected=201)
        module_id = module['id']
        ensure(any(m['id']==module_id for m in req('GET',f'/workspaces/{workspace_id}/modules',token=member_token)),'Module not visible to member')
        passed += 1; print('  PASS  Create and list a persistent module', flush=True)
        # Two real authenticated socket connections, then a server-side REST mutation.
        with ExitStack() as stack:
            sockets=[]
            for token in (owner_token,member_token):
                sock = stack.enter_context(connect(f'{WS}/ws/workspaces/{workspace_id}', open_timeout=10, close_timeout=2))
                sock.send(json.dumps({'token':token}))
                ensure(json.loads(sock.recv(timeout=8))['type']=='connected','WebSocket authentication failed')
                sockets.append(sock)
            passed += 1; print('  PASS  Two authenticated WebSocket connections', flush=True)
            item=req('POST',f'/modules/{module_id}/tasks',token=owner_token,body={'title':'Test Docker deployment','description':'Automatic verification'},expected=201)
            task_id=item['id']
            ensure(item['status']=='todo','Task not initially todo')
            for sock in sockets:
                ensure(json.loads(sock.recv(timeout=8)).get('type')=='refresh','Task creation did not notify socket')
            passed += 1; print('  PASS  Create task and push real-time event to both clients', flush=True)
            req('PATCH',f'/tasks/{task_id}',token=member_token,body={'status':'done'})
            for sock in sockets:
                ensure(json.loads(sock.recv(timeout=8)).get('type')=='refresh','Task status not broadcast')
            ensure(req('GET',f'/tasks/{task_id}',token=owner_token)['status']=='done','Task status not saved')
            passed += 1; print('  PASS  Member changes status; database saved; WebSockets notify', flush=True)
            comment=req('POST',f'/tasks/{task_id}/comments',token=member_token,body={'content':'Hello from automated test'},expected=201)
            for sock in sockets:
                ensure(json.loads(sock.recv(timeout=8)).get('type')=='refresh','Comment not broadcast')
            comments=req('GET',f'/tasks/{task_id}/comments',token=owner_token)
            ensure(any(c['id']==comment['id'] and c['content']=='Hello from automated test' for c in comments),'Comment not persistent')
            passed += 1; print('  PASS  Comment persisted and real-time update delivered', flush=True)
            req('DELETE',f'/comments/{comment["id"]}',token=owner_token,expected=403)
            req('GET',f'/tasks/{task_id}',token=outsider_token,expected=404)
            req('PATCH',f'/tasks/{task_id}',token=owner_token,body={'assigned_to_id':outsider_id},expected=422)
            passed += 1; print('  PASS  Comment ownership, outsider isolation, assignee validation', flush=True)
            tasks=req('GET',f'/modules/{module_id}/tasks',token=member_token)
            ensure(any(t['id']==task_id and t['status']=='done' for t in tasks),'Task lost during re-fetch')
            activity=req('GET',f'/workspaces/{workspace_id}/activity',token=owner_token)
            kinds={a['event_type'] for a in activity}
            ensure({'task_created','task_status_changed','comment_added'} <= kinds,'Activity feed missing events')
            passed += 1; print('  PASS  Re-fetch persisted task and activity history', flush=True)
        # Cleanup the test workspace, not any existing user data.
        req('DELETE',f'/workspaces/{workspace_id}',token=owner_token,expected=204)
        workspace_id=None
        passed += 1; print('  PASS  Delete temporary workspace and associated data', flush=True)
        print(f'\nSUCCESS — {passed} automated checks passed.\nTest accounts remain in Docker database; original workspaces were untouched.', flush=True)
    finally:
        if workspace_id is not None and owner_token:
            try:
                req('DELETE',f'/workspaces/{workspace_id}',token=owner_token,expected=204)
                print('Cleaned up temporary workspace after test.',flush=True)
            except Exception as e:
                print(f'NOTICE: Temporary workspace {workspace_id} could not be removed: {e}',flush=True)

if __name__=='__main__':
    try:
        main()
    except Exception as e:
        print(f'\nFAILED after {passed} successful checks: {type(e).__name__}: {e}',file=sys.stderr,flush=True)
        raise SystemExit(1)
