
import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { apiRequest, getToken } from "../api";

function Workspaces() {
  const navigate = useNavigate();

  const [workspaces, setWorkspaces] = useState([]);
  const [workspaceName, setWorkspaceName] = useState("");
  const [selectedWorkspace, setSelectedWorkspace] = useState(null);

  const [modules, setModules] = useState([]);
  const [moduleName, setModuleName] = useState("");
  const [members, setMembers] = useState([]);
  const [memberEmail, setMemberEmail] = useState("");
  const [myUserId, setMyUserId] = useState(null);
  const [memberBusy, setMemberBusy] = useState(false);
  const [memberSuccess, setMemberSuccess] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadWorkspaces = useCallback(async () => {
    try {
      const data = await apiRequest("/workspaces");
      setWorkspaces(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!getToken()) {
      navigate("/login", { replace: true });
      return;
    }

    loadWorkspaces();
    apiRequest("/users/me").then(user => setMyUserId(user.id)).catch(err => setError(err.message));
  }, [navigate, loadWorkspaces]);

  async function createWorkspace(event) {
    event.preventDefault();
    setError("");

    try {
      await apiRequest("/workspaces", {
        method: "POST",
        body: JSON.stringify({ name: workspaceName }),
      });

      setWorkspaceName("");
      await loadWorkspaces();

    } catch (err) {
      setError(err.message);
    }
  }

  async function selectWorkspace(workspace) {
    setSelectedWorkspace(workspace);
    setModules([]);
    setMembers([]);
    setMemberEmail("");
    setMemberSuccess("");
    setError("");

    try {
      const data = await apiRequest(
        `/workspaces/${workspace.id}/modules`
      );
      setModules(data);
      const memberData = await apiRequest(`/workspaces/${workspace.id}/members`);
      setMembers(memberData);
    } catch (err) {
      setError(err.message);
    }
  }

  async function addMember(event) {
    event.preventDefault();
    if (!selectedWorkspace || memberBusy) return;
    setError("");
    setMemberSuccess("");
    setMemberBusy(true);
    try {
      await apiRequest(`/workspaces/${selectedWorkspace.id}/members`, {
        method: "POST",
        body: JSON.stringify({ email: memberEmail.trim() }),
      });
      const updated = await apiRequest(`/workspaces/${selectedWorkspace.id}/members`);
      setMembers(updated);
      setMemberEmail("");
      setMemberSuccess("Member added. Ask them to refresh their Workspaces page.");
    } catch (err) {
      setError(err.message);
    } finally {
      setMemberBusy(false);
    }
  }

  async function removeMember(member) {
    if (!selectedWorkspace || memberBusy || member.role === "owner") return;
    if (!window.confirm(`Remove ${member.email} from this workspace?`)) return;
    setError("");
    setMemberSuccess("");
    setMemberBusy(true);
    try {
      await apiRequest(`/workspaces/${selectedWorkspace.id}/members/${member.user_id}`, {method: "DELETE"});
      const updated = await apiRequest(`/workspaces/${selectedWorkspace.id}/members`);
      setMembers(updated);
      setMemberSuccess("Member removed.");
    } catch (err) {
      setError(err.message);
    } finally {
      setMemberBusy(false);
    }
  }

  async function createModule(event) {
    event.preventDefault();

    if (!selectedWorkspace) return;

    setError("");

    try {
      await apiRequest(
        `/workspaces/${selectedWorkspace.id}/modules`,
        {
          method: "POST",
          body: JSON.stringify({ name: moduleName }),
        }
      );

      setModuleName("");

      const data = await apiRequest(
        `/workspaces/${selectedWorkspace.id}/modules`
      );

      setModules(data);

    } catch (err) {
      setError(err.message);
    }
  }


  const isOwner=members.some(m=>m.user_id===myUserId&&m.role==='owner');
  return <div className="page-content"><div className="eyebrow">YOUR COLLABORATIVE SPACE <span className="eyebrow-dot"/> WORKSPACES</div>
  <div className="page-heading"><div><h1>Workspaces<span className="heading-accent">.</span></h1><p>Keep your study groups and course modules beautifully organised.</p></div><span className="count-pill">{loading?'…':workspaces.length} spaces</span></div>
  {error&&<div className="notice error" role="alert">{error}</div>}
  <div className="two-column-layout"><section><div className="panel"><div className="panel-heading"><div><span className="eyebrow">START SOMETHING NEW</span><h2>Create workspace</h2></div><span className="panel-symbol">＋</span></div><form onSubmit={createWorkspace} className="inline-form"><input aria-label="Workspace name" placeholder="e.g. Software Engineering Group" maxLength={255} required value={workspaceName} onChange={e=>setWorkspaceName(e.target.value)}/><button className="btn btn-primary" type="submit">Create <span>↗</span></button></form></div>
  <div className="section-heading compact"><div><span className="eyebrow">ALL YOUR SPACES</span><h2>My workspaces</h2></div></div>
  {loading?<div className="panel muted">Loading your workspaces…</div>:workspaces.length===0?<div className="empty-block"><span className="empty-icon">▤</span><h3>Nothing here yet</h3><p>Create a workspace above and your group can get started.</p></div>:<div className="stack-list">{workspaces.map((space,i)=><button key={space.id} className={'space-row '+(selectedWorkspace?.id===space.id?'selected':'')} onClick={()=>selectWorkspace(space)}><span className={'tile-icon color-'+(i%4)}>{space.name?.charAt(0)?.toUpperCase()||'W'}</span><span className="space-row-copy"><strong>{space.name}</strong><small>Workspace · Open details</small></span><span className="space-row-arrow">↗</span></button>)}</div>}</section>
  <section>{selectedWorkspace?<><div className="panel"><div className="panel-heading"><div><span className="eyebrow">SELECTED WORKSPACE</span><h2>{selectedWorkspace.name}</h2><p className="muted">Manage the people and modules in your space.</p></div><span className="panel-symbol">✳</span></div>
  <div className="subheading"><h3>Modules <span className="mini-counter">{modules.length}</span></h3></div><form onSubmit={createModule} className="inline-form"><input aria-label="Module name" placeholder="Add a module (e.g. COMP30040)" maxLength={255} required value={moduleName} onChange={e=>setModuleName(e.target.value)}/><button className="btn btn-secondary" type="submit">Add +</button></form>
  <div className="module-list">{modules.map(m=><div key={m.id} className="module-row"><span className="module-icon">▦</span><strong>{m.name}</strong><button className="link-button" onClick={()=>navigate('/tasks')} type="button">Open board ↗</button></div>)}{!modules.length&&<p className="muted empty-inline">No modules yet. Add one to start tracking tasks.</p>}</div></div>
  <div className="panel"><div className="panel-heading"><div><span className="eyebrow">STUDY TOGETHER</span><h2>Team members <span className="mini-counter">{members.length}</span></h2></div><span className="panel-symbol">♧</span></div><p className="muted">Add people who already have StudySync accounts.</p><div className="member-list">{members.map(m=><div className="member-row" key={m.user_id}><span className="avatar">{m.email?.charAt(0).toUpperCase()}</span><span className="member-copy"><strong>{m.email}</strong><small>{m.role}</small></span>{isOwner&&m.role!=='owner'&&<button disabled={memberBusy} type="button" className="link-button destructive" onClick={()=>removeMember(m)}>Remove</button>}</div>)}</div>{isOwner&&<form className="inline-form" onSubmit={addMember}><input type="email" aria-label="New member email" placeholder="teammate@university.ac.uk" required value={memberEmail} onChange={e=>setMemberEmail(e.target.value)}/><button className="btn btn-secondary" disabled={memberBusy} type="submit">{memberBusy?'Adding…':'Invite +'}</button></form>}{memberSuccess&&<div className="notice success" role="status">{memberSuccess}</div>}</div></>:<div className="panel selection-panel"><div className="selection-illustration" aria-hidden="true">✳</div><span className="eyebrow">YOUR WORKSPACE DETAILS</span><h2>Everything in its place.</h2><p>Choose a workspace on the left to manage modules, invite members and jump into your task board.</p><div className="selection-foot">↖ Select a workspace to get started</div></div>}</section></div></div>;
}
export default Workspaces;
