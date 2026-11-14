
import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { apiRequest, getToken, logout } from "../api";

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

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  if (loading) {
    return <p>Loading workspaces...</p>;
  }

  return (
    <div>
      <h2>My Workspaces</h2>

      <button onClick={handleLogout}>Logout</button>

      {error && (
        <p role="alert" style={{ color: "red" }}>{error}</p>
      )}

      <h3>Create Workspace</h3>

      <form onSubmit={createWorkspace}>
        <input
          type="text"
          placeholder="Workspace name"
          value={workspaceName}
          onChange={(e) => setWorkspaceName(e.target.value)}
          required
          maxLength={255}
        />

        <button type="submit">Create</button>
      </form>

      <h3>Your Workspaces</h3>

      {workspaces.length === 0 && (
        <p>No workspaces yet. Create your first one!</p>
      )}

      {workspaces.map((workspace) => (
        <div className="card" key={workspace.id}>
          <h4>{workspace.name}</h4>

          <button
            onClick={() => selectWorkspace(workspace)}
          >
            Open Workspace
          </button>
        </div>
      ))}

      {selectedWorkspace && (
        <section>
          <hr />

          <h3>{selectedWorkspace.name}</h3>
          <div className="card" style={{ maxWidth: 650, margin: "16px auto", padding: 18, textAlign: "left" }}>
            <h4>Workspace members</h4>
            <p style={{ fontSize: 14 }}>Invite an existing StudySync user by their registered email. Only the workspace owner can add or remove members.</p>
            {members.length === 0 ? <p>No members loaded.</p> : (
              <ul style={{ paddingLeft: 20 }}>
                {members.map(member => (
                  <li key={member.user_id} style={{ marginBottom: 8 }}>
                    {member.email} — {member.role}
                    {members.some(m => m.user_id === myUserId && m.role === "owner") && member.role !== "owner" && (
                      <button type="button" disabled={memberBusy} onClick={() => removeMember(member)} style={{ marginLeft: 10 }}>Remove</button>
                    )}
                  </li>
                ))}
              </ul>
            )}
            {members.some(m => m.user_id === myUserId && m.role === "owner") && (
              <form onSubmit={addMember} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <input type="email" aria-label="New member email" placeholder="Registered user's email"
                  value={memberEmail} onChange={e => setMemberEmail(e.target.value)} required
                  style={{ flex: "1 1 210px", minWidth: 0, padding: 8 }} />
                <button type="submit" disabled={memberBusy}>{memberBusy ? "Adding..." : "Add Member"}</button>
              </form>
            )}
            {memberSuccess && <p role="status" style={{ color: "#6ac69a" }}>{memberSuccess}</p>}
          </div>
          <h4>Modules</h4>

          <form onSubmit={createModule}>
            <input
              type="text"
              placeholder="Module name"
              value={moduleName}
              onChange={(e) => setModuleName(e.target.value)}
              required
              maxLength={255}
            />

            <button type="submit">
              Add Module
            </button>
          </form>

          {modules.length === 0 && (
            <p>No modules yet.</p>
          )}

          {modules.map((module) => (
            <div className="card" key={module.id}>
              <strong>{module.name}</strong>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}

export default Workspaces;
