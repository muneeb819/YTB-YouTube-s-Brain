import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { ApiError, api, downloadUrl } from "../api";
import type { Asset, Job, Preflight, Project } from "../types";

type RightsStatus = "COMPLIANT" | "BLOCKED" | "UNKNOWN";

const VERDICT_BADGE: Record<string, string> = {
  PASS: "ok",
  REVIEW: "warn",
  REPAIR: "warn",
  BLOCK: "danger",
};

const STATE_BADGE: Record<string, string> = {
  COMPLETED: "ok",
  FAILED: "danger",
  QUEUED: "run",
  RUNNING: "run",
};

function describeProbe(a: Asset): string {
  const p = a.probe;
  if (p?.probe_error) return `probe error: ${p.probe_error}`;
  const dur = p?.format?.duration;
  const codecs = (p?.streams ?? [])
    .filter((s) => s.codec_type === "video" || s.codec_type === "audio")
    .map((s) => `${s.codec_type}:${s.codec_name}`)
    .join(", ");
  const parts: string[] = [];
  if (dur) parts.push(`${Number(dur).toFixed(2)}s`);
  if (codecs) parts.push(codecs);
  return parts.join(" · ") || "—";
}

export function ProjectView({
  project,
  onBack,
}: {
  project: Project;
  onBack: () => void;
}) {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [preflight, setPreflight] = useState<Preflight | null>(null);
  const [drafts, setDrafts] = useState<Partial<Record<number, RightsStatus>>>({});
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [renderAsset, setRenderAsset] = useState<number | null>(null);
  const [start, setStart] = useState("0");
  const [duration, setDuration] = useState("");
  const [rendering, setRendering] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [aiText, setAiText] = useState("");
  const [aiBusy, setAiBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      const [a, j, pf] = await Promise.all([
        api.assets(project.id),
        api.jobs(project.id),
        api.preflight(project.id),
      ]);
      setAssets(a);
      setJobs(j);
      setPreflight(pf);
      setRenderAsset((cur) => cur ?? (a[0]?.id ?? null));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load project data");
    }
  }, [project.id]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    // poll while any render job is still active
    const active = jobs.some((j) => j.state === "QUEUED" || j.state === "RUNNING");
    if (!active) return;
    const t = setInterval(() => void refresh(), 2500);
    return () => clearInterval(t);
  }, [jobs, refresh]);

  async function doUpload(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      await api.upload(project.id, file);
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function saveRights(id: number) {
    const status = drafts[id];
    if (!status) return;
    setError("");
    try {
      await api.setRights(id, status);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save rights status");
    }
  }

  async function doRender(e: FormEvent) {
    e.preventDefault();
    if (renderAsset == null) return;
    const startNum = Number(start);
    if (!Number.isFinite(startNum) || startNum < 0) {
      setError("Start must be a non-negative number of seconds.");
      return;
    }
    const durRaw = duration.trim();
    const durNum = durRaw ? Number(durRaw) : null;
    if (durNum != null && (!Number.isFinite(durNum) || durNum <= 0)) {
      setError("Duration must be greater than 0 seconds, or leave empty.");
      return;
    }
    setRendering(true);
    setError("");
    try {
      await api.render(project.id, renderAsset, startNum, durNum);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start render");
    } finally {
      setRendering(false);
    }
  }

  async function doGenerate(e: FormEvent) {
    e.preventDefault();
    if (!prompt.trim()) return;
    setAiBusy(true);
    setError("");
    try {
      const res = await api.generate(prompt.trim());
      setAiText(res.text);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "AI generation failed");
    } finally {
      setAiBusy(false);
    }
  }

  const activeJobs = jobs.filter(
    (j) => j.state === "QUEUED" || j.state === "RUNNING",
  ).length;

  return (
    <>
      <div className="topbar">
        <h1>
          <button className="ghost" onClick={onBack}>
            ←
          </button>{" "}
          {project.name} <span className="sub">project #{project.id}</span>
        </h1>
        <div className="actions">
          {preflight && (
            <span
              className={`badge ${VERDICT_BADGE[preflight.verdict] ?? ""}`}
              title="Project preflight verdict"
            >
              preflight: {preflight.verdict}
            </span>
          )}
          <span className="badge">{assets.length} asset{assets.length === 1 ? "" : "s"}</span>
          {activeJobs > 0 && (
            <span className="badge run">
              <span className="spinner" style={{ width: 14, height: 14, marginRight: 6 }} />
              {activeJobs} active
            </span>
          )}
        </div>
      </div>

      <div className="container">
        {error && <div className="error-box">{error}</div>}

        <div className="card">
          <h2>Preflight</h2>
          {!preflight ? (
            <p className="muted">Loading…</p>
          ) : preflight.assets.length === 0 ? (
            <p className="muted">
              No assets uploaded yet. Upload media below; note that without
              rights verification uploads are treated as UNKNOWN rights.
            </p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Asset</th>
                  <th>Rights</th>
                  <th>Verdict</th>
                </tr>
              </thead>
              <tbody>
                {preflight.assets.map((a) => (
                  <tr key={a.asset_id}>
                    <td>{a.filename}</td>
                    <td>{a.rights_status}</td>
                    <td>
                      <span className={`badge ${VERDICT_BADGE[a.verdict] ?? ""}`}>
                        {a.verdict}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card">
          <h2>Upload media</h2>
          <form onSubmit={doUpload} className="row">
            <input
              ref={fileRef}
              type="file"
              accept="video/*,audio/*,.mp4,.mov,.mkv,.avi,.webm,.mp3,.wav,.ogg,.m4a,.flac"
              className="grow"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <button type="submit" disabled={uploading || !file}>
              {uploading ? "Uploading…" : "Upload"}
            </button>
          </form>
        </div>

        <div className="card">
          <h2>Media assets</h2>
          {assets.length === 0 ? (
            <p className="muted">No assets yet.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>File</th>
                  <th>Type</th>
                  <th>Probe</th>
                  <th>Rights</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {assets.map((a) => (
                  <tr key={a.id}>
                    <td className="mono">{a.filename}</td>
                    <td>{a.mime_type}</td>
                    <td className="side-note">{describeProbe(a)}</td>
                    <td>
                      <select
                        value={drafts[a.id] ?? a.rights_status}
                        onChange={(e) =>
                          setDrafts((d) => ({
                            ...d,
                            [a.id]: e.target.value as RightsStatus,
                          }))
                        }
                      >
                        <option value="UNKNOWN">UNKNOWN</option>
                        <option value="COMPLIANT">COMPLIANT</option>
                        <option value="BLOCKED">BLOCKED</option>
                      </select>
                    </td>
                    <td className="row">
                      <button
                        className="ghost"
                        disabled={!drafts[a.id]}
                        onClick={() => void saveRights(a.id)}
                      >
                        Save
                      </button>
                      <a className="badge" href={downloadUrl("media", a.id)}>
                        download
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card">
          <h2>Render a clip</h2>
          <p className="side-note">
            Creates a trimmed stream-copy render with post-render verification. A
            COMPLIANT project passes immediately; otherwise a REVIEW approver is
            required before the job is queued. Duration is optional (whole file).
          </p>
          <form onSubmit={doRender} className="row">
            <select
              value={renderAsset ?? ""}
              className="grow"
              onChange={(e) => setRenderAsset(Number(e.target.value))}
              disabled={assets.length === 0}
            >
              {assets.length === 0 && <option value="">No assets available</option>}
              {assets.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.filename}
                </option>
              ))}
            </select>
            <input
              type="number"
              min={0}
              step="any"
              placeholder="start (s)"
              value={start}
              style={{ width: 120 }}
              onChange={(e) => setStart(e.target.value)}
            />
            <input
              type="number"
              min={0}
              step="any"
              placeholder="duration (s)"
              value={duration}
              style={{ width: 130 }}
              onChange={(e) => setDuration(e.target.value)}
            />
            <button
              type="submit"
              disabled={rendering || activeJobs > 0 || assets.length === 0}
            >
              {rendering ? "Queuing…" : "Render"}
            </button>
          </form>
        </div>

        <div className="card">
          <h2>Render jobs</h2>
          {jobs.length === 0 ? (
            <p className="muted">No jobs yet.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Type</th>
                  <th>State</th>
                  <th>Details</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((j) => (
                  <tr key={j.id}>
                    <td className="mono">#{j.id}</td>
                    <td>{j.type}</td>
                    <td>
                      <span className={`badge ${STATE_BADGE[j.state] ?? ""}`}>
                        {j.state}
                      </span>
                    </td>
                    <td className="side-note">
                      {j.error ? `error: ${j.error}` : ""}
                    </td>
                    <td>
                      {j.state === "COMPLETED" && j.output?.path && (
                        <a className="badge" href={downloadUrl("job", j.id)}>
                          download
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card">
          <h2>AI brief generation</h2>
          <form onSubmit={doGenerate} className="row">
            <input
              type="text"
              placeholder="Prompt (e.g. a doc-style explainer about how a neural net learns)"
              value={prompt}
              className="grow"
              onChange={(e) => setPrompt(e.target.value)}
            />
            <button type="submit" disabled={aiBusy || !prompt.trim()}>
              {aiBusy ? "Thinking…" : "Generate"}
            </button>
          </form>
          {aiText && (
            <p className="mt" style={{ whiteSpace: "pre-wrap" }}>
              {aiText}
            </p>
          )}
        </div>
      </div>
    </>
  );
}