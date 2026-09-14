import { useEffect, useState, type FormEvent } from "react";
import { ApiError, api } from "../api";
import type { Project, UserMe } from "../types";
import { ProjectView } from "./ProjectView";

export function Dashboard({
  user,
  onLogout,
}: {
  user: UserMe;
  onLogout: () => void;
}) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<Project | null>(null);
  const [name, setName] = useState("");
  const [brief, setBrief] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      setProjects(await api.projects());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load projects");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function create(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (!name.trim()) return;
    setBusy(true);
    try {
      const project = await api.createProject(name.trim(), brief.trim());
      setName("");
      setBrief("");
      await load();
      setSelected(project);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create project");
    } finally {
      setBusy(false);
    }
  }

  if (selected) {
    return (
      <ProjectView
        project={selected}
        onBack={() => {
          setSelected(null);
          void load();
        }}
      />
    );
  }

  return (
    <>
      <div className="topbar">
        <h1>
          YTB <span className="sub">YouTube&rsquo;s Brain — projects</span>
        </h1>
        <div className="actions">
          <span className="muted">{user.email}</span>
          <button className="ghost" onClick={onLogout}>
            Log out
          </button>
        </div>
      </div>
      <div className="container">
        {error && <div className="error-box">{error}</div>}
        <div className="card">
          <h2>New project</h2>
          <form onSubmit={create} className="row">
            <input
              type="text"
              placeholder="Project name"
              value={name}
              className="grow"
              onChange={(e) => setName(e.target.value)}
            />
            <input
              type="text"
              placeholder="Brief (optional)"
              value={brief}
              className="grow"
              onChange={(e) => setBrief(e.target.value)}
            />
            <button type="submit" disabled={busy || !name.trim()}>
              Create
            </button>
          </form>
        </div>

        <div className="card">
          <h2>Your projects</h2>
          {projects.length === 0 ? (
            <p className="muted">No projects yet. Create one to get started.</p>
          ) : (
            projects.map((p) => (
              <div
                key={p.id}
                className="project-item"
                onClick={() => setSelected(p)}
                style={{ cursor: "pointer" }}
              >
                <div className="grow">
                  <div className="name">{p.name}</div>
                  {p.brief && <div className="brief">{p.brief}</div>}
                </div>
                <span className="badge">#{p.id}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}