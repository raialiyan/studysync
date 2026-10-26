
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
    setError("");

    try {
      const data = await apiRequest(
        `/workspaces/${workspace.id}/modules`
      );
      setModules(data);
    } catch (err) {
      setError(err.message);
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
