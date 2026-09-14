import type {
  Asset,
  Health,
  Job,
  Preflight,
  Project,
  UploadResult,
  UserMe,
} from "./types";

const TOKEN_KEY = "ytb_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = true,
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`/api${path}`, { ...options, headers });

  if (res.status === 401 && auth) {
    setToken(null);
  }

  const text = await res.text();
  let body: unknown = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = text;
  }

  if (!res.ok) {
    const detail = (body as { detail?: unknown })?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : JSON.stringify(detail ?? body ?? res.statusText);
    throw new ApiError(res.status, message);
  }
  return body as T;
}

export const api = {
  health: () =>
    request<Health>("/health", {}, false),

  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string }>(
      "/auth/login",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      },
      false,
    ),

  register: (email: string, password: string) =>
    request<{ id: number; email: string }>(
      "/auth/register",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      },
      false,
    ),

  me: () => request<UserMe>("/auth/me"),

  projects: () => request<Project[]>("/projects"),

  createProject: (name: string, brief: string) =>
    request<Project>("/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, brief }),
    }),

  preflight: (projectId: number) =>
    request<Preflight>(`/projects/${projectId}/preflight`),

  assets: (projectId: number) =>
    request<Asset[]>(`/projects/${projectId}/assets`),

  jobs: (projectId: number) =>
    request<Job[]>(`/projects/${projectId}/jobs`),

  upload: (projectId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<UploadResult>(`/media/upload/${projectId}`, {
      method: "POST",
      body: form,
    });
  },

  setRights: (assetId: number, status: "COMPLIANT" | "BLOCKED" | "UNKNOWN") =>
    request(`/media/${assetId}/rights`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }),

  render: (projectId: number, assetId: number, start: number, duration: number | null) =>
    request<{ job_id: number; state: string }>("/jobs/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_id: projectId,
        asset_id: assetId,
        start,
        duration,
      }),
    }),

  job: (jobId: number) => request<Job>(`/jobs/${jobId}`),

  generate: (prompt: string) =>
    request<{ text: string }>("/ai/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    }),
};

export function downloadUrl(kind: "job" | "media", id: number): string {
  return `/api/${kind}/${id}/download`;
}