export interface Project {
  id: number;
  name: string;
  brief: string;
}

export interface Asset {
  id: number;
  filename: string;
  mime_type: string;
  rights_status: "COMPLIANT" | "BLOCKED" | "UNKNOWN" | string;
  probe: {
    format?: { duration?: string };
    streams?: Array<{ codec_type?: string; codec_name?: string }>;
    probe_error?: string;
  };
}

export interface PreflightAsset {
  asset_id: number;
  filename: string;
  rights_status: string;
  verdict: string;
}

export interface Preflight {
  project_id: number;
  verdict: string;
  assets: PreflightAsset[];
}

export interface Job {
  id: number;
  type: string;
  state: string;
  error: string;
  output: { path?: string };
}

export interface UploadResult {
  id: number;
  filename: string;
  probe: Asset["probe"];
}

export interface Health {
  status: string;
  service: string;
  ai_provider: string;
}

export interface UserMe {
  id: number;
  email: string;
  is_admin: boolean;
}