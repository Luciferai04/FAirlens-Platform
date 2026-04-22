// Typed API client for FairLens console
const BASE = import.meta.env.VITE_API_URL ?? import.meta.env.VITE_API_BASE_URL ?? "/api";

async function getAuthToken(): Promise<string> {
  // Check demo mode first
  if (import.meta.env.VITE_DEMO_MODE === "true" || localStorage.getItem("demo_mode") === "true") {
    return "demo-token";
  }
  
  // Use the Google JWT saved by AuthContext
  const token = localStorage.getItem("google_jwt");
  if (token) return token;
  
  return "dev-token";
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await getAuthToken();
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

// Flat API methods for hooks
export const api = {
  get: <T>(path: string) => apiFetch<T>(path),
  post: <T>(path: string, body?: unknown) =>
    apiFetch<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  // Domain-specific methods (backward compat)
  models: {
    list: () => apiFetch<ModelSummary[]>("/v1/models"),
    getAudit: (id: string) => apiFetch<AuditReport>(`/v1/models/${id}/audit`),
    triggerScan: (id: string) =>
      apiFetch(`/v1/models/${id}/scan`, { method: "POST" }),
  },
  incidents: {
    list: (filter?: string) =>
      apiFetch<Incident[]>(`/v1/incidents${filter ? `?${filter}` : ""}`),
    generatePlaybook: (id: string) =>
      apiFetch<Playbook>(`/v1/incidents/${id}/playbook`, { method: "POST" }),
  },
  reports: {
    list: () => apiFetch<ComplianceReport[]>("/v1/reports/compliance"),
    generate: (body: { model_id: string; framework: string }) =>
      apiFetch<ComplianceReport>("/v1/reports/compliance", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  },
  playbooks: {
    approve: (id: string) =>
      apiFetch(`/v1/playbooks/${id}/approve`, { method: "POST" }),
  },
};

// ── Types ──────────────────────────────────────────────────────────────────

export interface ModelSummary {
  model_id: string;
  name: string;
  version: string;
  provider: string;
  sensitive_cols: string[];
  equity_score: number;
  passed: boolean;
  violations_count: number;
  last_audited: string;
  triggered_by: string;
}

export interface AuditReport {
  report_id: string;
  model_id: string;
  created_at: string;
  protected_cols: string[];
  metrics: Record<string, Record<string, number>>;
  threshold_policy: string | null;
  passed: boolean;
  triggered_by: string;
  violations: Array<{
    col: string;
    metric: string;
    value: number;
    threshold: number;
  }>;
  trend: number[];
}

export interface Incident {
  incident_id: string;
  model_id: string;
  model_name: string;
  model_category: string;
  metric_name: string;
  sub_metric: string;
  current_value: number;
  threshold: number;
  severity: string;
  status: string;
  detected_at: string;
  sensitive_col: string;
  playbook_id: string | null;
}

export interface Playbook {
  playbook_id: string;
  incident_id: string;
  strategies: Array<{
    title: string;
    type: string;
    effort: string;
    steps: string[];
  }>;
  human_approved: boolean;
  created_at: string;
  root_cause_analysis: string;
  status: string;
}

export interface ComplianceReport {
  report_id: string;
  model_id: string;
  model_name: string;
  framework: string;
  generated_at: string;
  kms_signed: boolean;
  sha256_hash: string;
}
