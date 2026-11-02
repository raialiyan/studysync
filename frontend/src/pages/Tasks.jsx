import { useCallback, useEffect, useRef, useState } from 'react';
import { apiRequest, getToken } from '../api';

const statuses = ['todo', 'in_progress', 'done'];
const labels = { todo: 'To do', in_progress: 'In progress', done: 'Done' };
const socketUrl = `ws://${window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname}:8000`;

export default function Tasks() {
  const [workspaces, setWorkspaces] = useState([]);
  const [workspaceId, setWorkspaceId] = useState('');
  const [modules, setModules] = useState([]);
  const [moduleId, setModuleId] = useState('');
  const [members, setMembers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [activity, setActivity] = useState([]);
  const [comments, setComments] = useState({});
  const [newComments, setNewComments] = useState({});
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [assignee, setAssignee] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [connection, setConnection] = useState('Disconnected');
  const socketRef = useRef(null);

  useEffect(() => {
    apiRequest('/workspaces').then(setWorkspaces).catch(e => setError(e.message));
  }, []);

  const loadWorkspace = useCallback(async (id) => {
    if (!id) return;
    const [moduleData, memberData, eventData] = await Promise.all([
      apiRequest(`/workspaces/${id}/modules`),
      apiRequest(`/workspaces/${id}/members`),
      apiRequest(`/workspaces/${id}/activity`),
    ]);
    setModules(moduleData);
    setMembers(memberData);
    setActivity(eventData);
  }, []);

  const loadTasks = useCallback(async (id) => {
    if (!id) return;
    setTasks(await apiRequest(`/modules/${id}/tasks`));
  }, []);

  useEffect(() => {
    setModuleId(''); setTasks([]); setComments({}); setModules([]); setMembers([]); setActivity([]);
    if (workspaceId) loadWorkspace(workspaceId).catch(e => setError(e.message));
  }, [workspaceId, loadWorkspace]);

  useEffect(() => {
    setComments({}); setTasks([]);
    if (moduleId) loadTasks(moduleId).catch(e => setError(e.message));
  }, [moduleId, loadTasks]);

  useEffect(() => {
    if (!workspaceId) return;
    let disposed = false;
    let retryId;
    let ws;
    function connect() {
      if (disposed) return;
      ws = new WebSocket(`${socketUrl}/ws/workspaces/${workspaceId}`);
      socketRef.current = ws;
      setConnection('Connecting');
      ws.onopen = () => ws.send(JSON.stringify({ token: getToken() }));
      ws.onmessage = async (event) => {
        let message;
        try { message = JSON.parse(event.data); } catch { return; }
        if (disposed) return;
        if (message.type === 'connected') setConnection('Connected');
        if (message.type === 'refresh') {
          try {
            await loadWorkspace(workspaceId);
            if (moduleId) await loadTasks(moduleId);
            setComments({});
          } catch (e) { setError(e.message); }
        }
      };
      ws.onclose = (e) => {
        if (disposed) return;
        setConnection('Disconnected');
        // Don't reconnect an unauthorised or expired session.
        if (e.code !== 1008) retryId = setTimeout(connect, 3000);
      };
      ws.onerror = () => setConnection('Connection error');
    }
    connect();
    return () => {
      disposed = true;
      clearTimeout(retryId);
      ws?.close();
      if (socketRef.current === ws) socketRef.current = null;
    };
  }, [workspaceId, moduleId, loadWorkspace, loadTasks]);

  async function mutate(action) {
    setError(''); setBusy(true);
    try {
      const value = await action();
      if (workspaceId) await loadWorkspace(workspaceId);
      if (moduleId) await loadTasks(moduleId);
      if (socketRef.current?.readyState === WebSocket.OPEN)
        socketRef.current.send(JSON.stringify({ type: 'refresh' }));
      return value;
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
    return null;
  }

  async function createTask(event) {
    event.preventDefault();
    const result = await mutate(() => apiRequest(`/modules/${moduleId}/tasks`, {
      method: 'POST',
      body: JSON.stringify({ title, description: description || null, assigned_to_id: assignee ? Number(assignee) : null }),
    }));
    if (result) { setTitle(''); setDescription(''); setAssignee(''); }
  }

  async function patchTask(id, data) {
    await mutate(() => apiRequest(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(data) }));
  }

  async function deleteTask(id) {
    if (!window.confirm('Delete this task and its comments?')) return;
    await mutate(() => apiRequest(`/tasks/${id}`, { method: 'DELETE' }));
  }

  async function showComments(taskId) {
    try {
      const value = await apiRequest(`/tasks/${taskId}/comments`);
      setComments(prev => ({ ...prev, [taskId]: value }));
    } catch (e) { setError(e.message); }
  }

  async function addComment(taskId) {
    const content = (newComments[taskId] || '').trim();
    if (!content) return;
    const created = await mutate(() => apiRequest(`/tasks/${taskId}/comments`, {
      method: 'POST', body: JSON.stringify({ content }),
    }));
    if (created) {
      setNewComments(prev => ({ ...prev, [taskId]: '' }));
      await showComments(taskId);
    }
  }

  async function deleteComment(taskId, commentId) {
    await mutate(() => apiRequest(`/comments/${commentId}`, { method: 'DELETE' }));
    await showComments(taskId);
  }

  return (
    <div style={{ maxWidth: 950, margin: '0 auto' }}>
      <h2>Tasks and collaboration</h2>
      <p>Real-time connection: {connection}</p>
      {error && <p role="alert" style={{ color: 'crimson' }}>{error}</p>}
      <label>Workspace{' '}
        <select value={workspaceId} onChange={e => setWorkspaceId(e.target.value)}>
          <option value="">Select workspace</option>
          {workspaces.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
        </select>
      </label>{' '}
      <label>Module{' '}
        <select value={moduleId} disabled={!workspaceId} onChange={e => setModuleId(e.target.value)}>
          <option value="">Select module</option>
          {modules.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
        </select>
      </label>
      {workspaceId && modules.length === 0 && <p>No modules yet. Create one on the Workspaces page.</p>}
      {moduleId && <>
        <h3>Create task</h3>
        <form onSubmit={createTask} style={{ display: 'grid', gap: 8, marginBottom: 24 }}>
          <input aria-label="Task title" placeholder="Task title" required maxLength={255} value={title} onChange={e => setTitle(e.target.value)} />
          <input aria-label="Task description" placeholder="Description (optional)" maxLength={1000} value={description} onChange={e => setDescription(e.target.value)} />
          <label>Assign to{' '}
            <select value={assignee} onChange={e => setAssignee(e.target.value)}>
              <option value="">Unassigned</option>
              {members.map(m => <option key={m.user_id} value={m.user_id}>{m.email}</option>)}
            </select>
          </label>
          <button disabled={busy} type="submit">Create task</button>
        </form>
        <h3>Tasks ({tasks.length})</h3>
        {tasks.length === 0 && <p>No tasks in this module yet.</p>}
        {tasks.map(task => <div key={task.id} className="card" style={{ marginBottom: 12 }}>
          <h4>{task.title}</h4>
          {task.description && <p>{task.description}</p>}
          <label>Status{' '}
            <select disabled={busy} value={task.status} onChange={e => patchTask(task.id, { status: e.target.value })}>
              {statuses.map(s => <option key={s} value={s}>{labels[s]}</option>)}
            </select>
          </label>{' '}
          <label>Assigned to{' '}
            <select disabled={busy} value={task.assigned_to_id ?? ''} onChange={e => patchTask(task.id, { assigned_to_id: e.target.value ? Number(e.target.value) : null })}>
              <option value="">Unassigned</option>
              {members.map(m => <option key={m.user_id} value={m.user_id}>{m.email}</option>)}
            </select>
          </label>{' '}
          <button disabled={busy} onClick={() => {
            const edited = window.prompt('New task title', task.title);
            if (edited !== null) patchTask(task.id, { title: edited });
          }}>Rename</button>{' '}
          <button disabled={busy} onClick={() => {
            const edited = window.prompt('New description', task.description || '');
            if (edited !== null) patchTask(task.id, { description: edited });
          }}>Edit description</button>{' '}
          <button disabled={busy} onClick={() => deleteTask(task.id)}>Delete</button>
          <div style={{ marginTop: 12 }}>
            <button onClick={() => showComments(task.id)}>View / refresh comments</button>
            {(comments[task.id] || []).map(c => <div key={c.id} style={{ padding: 5 }}>
              <span>{members.find(m => m.user_id === c.user_id)?.email || `User ${c.user_id}`}: {c.content}</span>{' '}
              <button disabled={busy} onClick={() => deleteComment(task.id, c.id)}>Delete</button>
            </div>)}
            <input aria-label={`Comment on ${task.title}`} placeholder="Write a comment" maxLength={2000}
              value={newComments[task.id] || ''} onChange={e => setNewComments(p => ({ ...p, [task.id]: e.target.value }))} />{' '}
            <button disabled={busy} onClick={() => addComment(task.id)}>Comment</button>
          </div>
        </div>)}
      </>}
      {workspaceId && <section>
        <h3>Workspace activity</h3>
        {activity.length === 0 && <p>No activity recorded yet.</p>}
        <ul>{activity.slice(0, 20).map(a => <li key={a.id}>
          {a.event_type.replaceAll('_', ' ')} — {a.entity_type} #{a.entity_id} ({new Date(a.created_at).toLocaleString()})
        </li>)}</ul>
      </section>}
    </div>
  );
}
