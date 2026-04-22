import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  api,
  type ModelSummary,
  type AuditReport,
  type Incident,
  type Playbook,
  type ComplianceReport,
} from "./client";

// Re-export types for convenience
export type { ModelSummary, AuditReport, Incident, Playbook, ComplianceReport };

// ── Query Hooks ────────────────────────────────────────────────────────────

export const useModels = () =>
  useQuery<ModelSummary[]>({
    queryKey: ["models"],
    queryFn: () => api.get<ModelSummary[]>("/v1/models"),
  });

export const useModelAudit = (modelId: string) =>
  useQuery<AuditReport>({
    queryKey: ["audit", modelId],
    queryFn: () => api.get<AuditReport>(`/v1/models/${modelId}/audit`),
    enabled: !!modelId,
  });

export const useIncidents = (filters?: {
  status?: string;
  severity?: string;
}) => {
  const params = filters
    ? new URLSearchParams(
        Object.entries(filters).filter(([, v]) => v) as [string, string][]
      ).toString()
    : "";
  return useQuery<Incident[]>({
    queryKey: ["incidents", filters],
    queryFn: () => api.get<Incident[]>(`/v1/incidents${params ? "?" + params : ""}`),
  });
};

export const useComplianceReports = () =>
  useQuery<ComplianceReport[]>({
    queryKey: ["compliance"],
    queryFn: () => api.get<ComplianceReport[]>("/v1/reports/compliance"),
  });

// ── Mutation Hooks ─────────────────────────────────────────────────────────

export const useTriggerScan = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (modelId: string) =>
      api.post(`/v1/models/${modelId}/scan`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["models"] }),
  });
};

export const useGeneratePlaybook = () =>
  useMutation({
    mutationFn: (incidentId: string) =>
      api.post<Playbook>(`/v1/incidents/${incidentId}/playbook`),
  });

export const useApprovePlaybook = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (playbookId: string) =>
      api.post(`/v1/playbooks/${playbookId}/approve`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["incidents"] }),
  });
};

export const useGenerateReport = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { model_id: string; framework: string }) =>
      api.post<ComplianceReport>("/v1/reports/compliance", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["compliance"] }),
  });
};
