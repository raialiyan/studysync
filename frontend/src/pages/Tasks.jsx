import { useCallback, useEffect, useRef, useState } from 'react';
import { apiRequest, getToken } from '../api';

const statuses = ['todo', 'in_progress', 'done'];
const labels = { todo: 'To do', in_progress: 'In progress', done: 'Done' };
const socketUrl = (import.meta.env.VITE_WS_URL || (import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL.replace(/^http/, 'ws') : `ws://${window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname}:8000`)).replace(/\/$/, '');

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
  const [filter,setFilter]=useState('all');
  const [showComposer,setShowComposer]=useState(false);
  const [connection, setConnection] = useState('Disconnected');
  const socketRef = useRef(null);
  const moduleIdRef = useRef('');
  const openCommentsRef = useRef(new Set());
  useEffect(() => { moduleIdRef.current = moduleId; }, [moduleId]);

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
    openCommentsRef.current.clear();
    setModuleId(''); setTasks([]); setComments({}); setModules([]); setMembers([]); setActivity([]);
    if (workspaceId) loadWorkspace(workspaceId).catch(e => setError(e.message));
  }, [workspaceId, loadWorkspace]);

  useEffect(() => {
    openCommentsRef.current.clear();
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
            if (moduleIdRef.current) await loadTasks(moduleIdRef.current);
            const openTasks = [...openCommentsRef.current];
            const fetched = await Promise.all(openTasks.map(async taskId => {
              try { return [taskId, await apiRequest(`/tasks/${taskId}/comments`)]; }
              catch { return [taskId, []]; }
            }));
            if (!disposed) setComments(prev => ({ ...prev, ...Object.fromEntries(fetched) }));
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
  }, [workspaceId, loadWorkspace, loadTasks]);

  async function mutate(action) {
    setError(''); setBusy(true);
    try {
      const value = await action();
      if (workspaceId) await loadWorkspace(workspaceId);
      if (moduleId) await loadTasks(moduleId);
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
    openCommentsRef.current.add(taskId);
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

  const filteredTasks = tasks.filter(t=>filter==='all'||t.status===filter);
  const counts={all:tasks.length,todo:tasks.filter(t=>t.status==='todo').length,in_progress:tasks.filter(t=>t.status==='in_progress').length,done:tasks.filter(t=>t.status==='done').length};
  return <div className="page-content"><div className="eyebrow">FOCUS MODE <span className="eyebrow-dot"/> TASK BOARD</div><div className="page-heading"><div><h1>Task board<span className="heading-accent">.</span></h1><p>Every small step adds up. Stay focused and keep things moving.</p></div><span className={'connection-pill '+(connection==='Connected'?'online':'')}><i/>{connection==='Connected'?'Live collaboration':connection}</span></div>
  {error&&<div className="notice error" role="alert">{error}</div>}
  <div className="panel picker-panel"><div className="picker-field"><label htmlFor="task-workspace">WORKSPACE</label><select id="task-workspace" value={workspaceId} onChange={e=>setWorkspaceId(e.target.value)}><option value="">Choose a workspace</option>{workspaces.map(w=><option key={w.id} value={w.id}>{w.name}</option>)}</select></div><span className="picker-divider">/</span><div className="picker-field"><label htmlFor="task-module">MODULE</label><select id="task-module" value={moduleId} disabled={!workspaceId} onChange={e=>setModuleId(e.target.value)}><option value="">Choose a module</option>{modules.map(m=><option key={m.id} value={m.id}>{m.name}</option>)}</select></div></div>
  {!workspaceId?<div className="empty-block empty-large"><span className="empty-icon">▦</span><h2>Ready when you are.</h2><p>Choose a workspace above to see your tasks, teammates and live activity.</p></div>:modules.length===0?<div className="empty-block empty-large"><span className="empty-icon">▤</span><h2>First, make a module.</h2><p>Go to Workspaces and add a module to organise your tasks.</p><a href="/workspaces" className="btn btn-primary">Go to workspaces ↗</a></div>:!moduleId?<div className="empty-block empty-large"><span className="empty-icon">✳</span><h2>Pick a module.</h2><p>Select one of your modules above to open its task board.</p></div>:<>
  <div className="task-stats">{[['all','All tasks'],['todo','To do'],['in_progress','In progress'],['done','Completed']].map(([key,name])=><button key={key} className={'task-stat '+(filter===key?'active':'')} onClick={()=>setFilter(key)}><span>{name}</span><strong>{counts[key]}</strong><small>{key==='all'?'Your full board':key==='done'?'Keep it up!':'Click to filter'} <span>↗</span></small></button>)}</div>
  <div className="task-layout"><section><div className="section-heading compact"><div><span className="eyebrow">MAKE PROGRESS</span><h2>{filter==='all'?'All tasks':labels[filter]} <span className="mini-counter">{filteredTasks.length}</span></h2></div><button type="button" className="btn btn-primary" onClick={()=>setShowComposer(v=>!v)}>{showComposer?'Close form':'＋ New task'}</button></div>
  {showComposer&&<form onSubmit={createTask} className="panel composer"><h3>Create a task</h3><label>Task name<input aria-label="Task title" placeholder="What needs to get done?" required maxLength={255} value={title} onChange={e=>setTitle(e.target.value)}/></label><label>Description<input aria-label="Task description" placeholder="Add a little context (optional)" maxLength={1000} value={description} onChange={e=>setDescription(e.target.value)}/></label><label>Assign to<select value={assignee} onChange={e=>setAssignee(e.target.value)}><option value="">Unassigned</option>{members.map(m=><option key={m.user_id} value={m.user_id}>{m.email}</option>)}</select></label><button disabled={busy} className="btn btn-primary">{busy?'Saving…':'Create task →'}</button></form>}
  <div className="tasks-stack">{filteredTasks.map(t=><article key={t.id} className="task-item"><div className="task-item-top"><span className={'status-badge status-'+t.status}><i/>{labels[t.status]||t.status}</span><div className="task-tools"><button disabled={busy} title="Rename task" aria-label={'Rename '+t.title} onClick={()=>{const v=window.prompt('New task title',t.title);if(v!==null&&v.trim())patchTask(t.id,{title:v.trim()})}}>✎</button><button disabled={busy} title="Edit description" aria-label={'Edit description for '+t.title} onClick={()=>{const v=window.prompt('New description',t.description||'');if(v!==null)patchTask(t.id,{description:v})}}>☰</button><button disabled={busy} title="Delete task" aria-label={'Delete '+t.title} className="destructive" onClick={()=>deleteTask(t.id)}>×</button></div></div><h3>{t.title}</h3>{t.description&&<p className="task-description">{t.description}</p>}<div className="task-item-fields"><label>STATUS<select disabled={busy} value={t.status} onChange={e=>patchTask(t.id,{status:e.target.value})}>{statuses.map(s=><option key={s} value={s}>{labels[s]}</option>)}</select></label><label>ASSIGNEE<select disabled={busy} value={t.assigned_to_id??''} onChange={e=>patchTask(t.id,{assigned_to_id:e.target.value?Number(e.target.value):null})}><option value="">Unassigned</option>{members.map(m=><option key={m.user_id} value={m.user_id}>{m.email}</option>)}</select></label></div><div className="task-comments"><button className="comment-toggle" onClick={()=>showComments(t.id)}>♧ {comments[t.id]?'Comments · '+comments[t.id].length:'View comments'} <span>↗</span></button>{comments[t.id]&&<div className="comment-list">{comments[t.id].map(c=><div className="comment-row" key={c.id}><span className="avatar small">{(members.find(m=>m.user_id===c.user_id)?.email||'?').charAt(0).toUpperCase()}</span><div><strong>{members.find(m=>m.user_id===c.user_id)?.email||'Member'}</strong><p>{c.content}</p></div><button disabled={busy} title="Delete comment" className="comment-delete" onClick={()=>deleteComment(t.id,c.id)}>×</button></div>)}</div>}<div className="comment-form"><input aria-label={'Comment on '+t.title} placeholder="Write a comment…" maxLength={2000} value={newComments[t.id]||''} onChange={e=>setNewComments(p=>({...p,[t.id]:e.target.value}))} onKeyDown={e=>{if(e.key==='Enter'){e.preventDefault();addComment(t.id)}}}/><button disabled={busy||!(newComments[t.id]||'').trim()} type="button" onClick={()=>addComment(t.id)}>Send ↗</button></div></div></article>)}{!filteredTasks.length&&<div className="empty-block"><span className="empty-icon">✓</span><h3>All clear here</h3><p>{filter==='all'?'Create your first task to start making progress.':'No tasks in this category yet.'}</p>{!showComposer&&<button className="btn btn-primary" onClick={()=>setShowComposer(true)}>＋ Create task</button>}</div>}</div></section>
  <aside className="activity-panel panel"><span className="eyebrow">STAY IN THE LOOP</span><h2>Recent activity</h2><p className="muted">See what's happening in your study group.</p>{activity.length?<div className="activity-timeline">{activity.slice(0,20).map(a=><div className="activity-event" key={a.id}><span className="activity-pin"/><div><strong>{a.event_type.replaceAll('_',' ')}</strong><p>{a.entity_type} #{a.entity_id}</p><time>{new Date(a.created_at).toLocaleString()}</time></div></div>)}</div>:<div className="activity-empty">✦<p>Activity from your team will appear here.</p></div>}</aside></div></>}</div>;
}
