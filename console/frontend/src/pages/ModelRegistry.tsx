import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useModels, useTriggerScan } from "../api/hooks";
import { SkeletonRow, ErrorBanner } from "../components/Skeleton";

// ── Fallback Data ──────────────────────────────────────────────────────────
const FALLBACK_MODELS = [
  { model_id: "loan-approval-v2", name: "Loan Origination v4.2", version: "v4.2.1", provider: "sklearn",
    sensitive_cols: ["race", "gender"], equity_score: 0.72, passed: false, violations_count: 2,
    last_audited: "2024-10-24T14:30:00Z", triggered_by: "scheduled" },
  { model_id: "resume-screen-v3", name: "Resume Screening", version: "v3.1.0", provider: "Vertex AI",
    sensitive_cols: ["age", "gender"], equity_score: 0.92, passed: true, violations_count: 0,
    last_audited: "2024-10-24T12:00:00Z", triggered_by: "ci_gate" },
  { model_id: "icu-triage-v1", name: "ICU Triage Priority", version: "v1.0.3", provider: "TensorFlow",
    sensitive_cols: ["race", "age", "insurance_type"], equity_score: 0.58, passed: false, violations_count: 4,
    last_audited: "2024-10-23T09:15:00Z", triggered_by: "manual" },
  { model_id: "credit-scoring-v5", name: "Credit Scorer Baseline", version: "v5.0.0", provider: "Vertex AI",
    sensitive_cols: ["age", "income_bracket"], equity_score: 0.88, passed: true, violations_count: 0,
    last_audited: "2024-10-22T16:45:00Z", triggered_by: "scheduled" },
  { model_id: "content-rec-v2", name: "Content Feed Ranking", version: "v2.1.0", provider: "AWS Sagemaker",
    sensitive_cols: ["gender", "region"], equity_score: 0.79, passed: false, violations_count: 1,
    last_audited: "2024-10-17T08:30:00Z", triggered_by: "ci_gate" },
];

const STATUS_LABEL = (m: any) => {
  if (m.passed) return "Passing";
  if ((m.equity_score ?? 0) < 0.8) return "Critical";
  return "Warning";
};

const STATUS_STYLE = (label: string) => {
  switch (label) {
    case "Passing": return "bg-primary/10 text-primary border border-primary/20";
    case "Critical": return "bg-error-container text-on-error-container";
    case "Warning": return "bg-[#3a1a00] text-[#ffb873] border border-[#6a3b00]";
    default: return "bg-surface-container text-on-surface-variant";
  }
};

export default function ModelRegistry() {
  const navigate = useNavigate();
  const { data: apiModels, isLoading, isError } = useModels();
  const triggerScan = useTriggerScan();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"All" | "Passing" | "Warning" | "Critical">("All");
  const [scanningId, setScanningId] = useState<string | null>(null);
  const [showAuditModal, setShowAuditModal] = useState(false);
  const [selectedAuditModel, setSelectedAuditModel] = useState("");
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const models = apiModels ?? FALLBACK_MODELS as any[];

  const filtered = models
    .filter((m: any) => (m.name ?? "").toLowerCase().includes(search.toLowerCase()))
    .filter((m: any) => {
      if (statusFilter === "All") return true;
      return STATUS_LABEL(m) === statusFilter;
    });

  const handleScan = (e: React.MouseEvent, modelId: string) => {
    e.stopPropagation();
    setScanningId(modelId);
    triggerScan.mutate(modelId, { onSettled: () => setScanningId(null) });
  };

  return (
    <div className="flex-1 p-lg overflow-y-auto">
      <div className="max-w-[1400px] mx-auto w-full">
        {isError && <div className="mb-lg"><ErrorBanner onRetry={() => window.location.reload()} /></div>}

        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-lg gap-4">
          <div>
            <h1 className="font-h1 text-h1 text-on-surface">Model Registry</h1>
            <p className="font-body-md text-body-md text-on-surface-variant mt-xs">
              Central catalog of all AI models under fairness governance.
            </p>
          </div>
          <button
            onClick={() => { setSelectedAuditModel(models[0]?.model_id ?? ""); setShowAuditModal(true); }}
            className="bg-primary-container text-on-primary-container px-4 py-2 rounded-lg text-body-md font-medium transition-colors flex items-center gap-2 hover:bg-primary"
          >
            <span className="material-symbols-outlined text-[18px]">play_circle</span> Trigger Audit
          </button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-md items-center">
          <div className="relative flex-1 max-w-sm">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">search</span>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 bg-surface-container-low border border-surface-container-high rounded-lg text-body-md text-on-surface placeholder:text-on-surface-variant focus:border-primary-fixed-dim focus:ring-1 focus:ring-primary-fixed-dim outline-none w-full transition-all"
              placeholder="Search models..."
            />
          </div>
          <div className="flex gap-2">
            {(["All", "Passing", "Warning", "Critical"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`px-3 py-1.5 rounded text-label-sm border transition-colors ${
                  statusFilter === s
                    ? "bg-[#10a37f] text-white border-[#10a37f]"
                    : "bg-surface border-outline-variant text-[#b4b4b4] hover:text-white"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="bg-surface border border-outline-variant rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse whitespace-nowrap">
              <thead>
                <tr className="bg-surface-container-low">
                  {["Model Name", "Version", "Provider", "Protected Attrs", "Equity Score", "Status", "Actions"].map((h, i) => (
                    <th key={i} className={`py-3 px-5 font-label-sm text-label-sm text-on-surface-variant font-medium tracking-wider uppercase ${i === 6 ? "text-right" : ""}`}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2f2f2f] font-body-md text-body-md">
                {isLoading
                  ? Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} cols={7} />)
                  : filtered.map((m: any) => {
                      const status = STATUS_LABEL(m);
                      return (
                        <React.Fragment key={m.model_id}>
                          <tr
                            onClick={() => setExpandedRow(expandedRow === m.model_id ? null : m.model_id)}
                            className="hover:bg-surface-container-low transition-colors cursor-pointer group"
                          >
                            <td className="py-4 px-5 text-white font-medium">{m.name}</td>
                            <td className="py-4 px-5">
                              <span className="bg-surface-container-high font-code text-code px-2 py-0.5 rounded text-on-surface-variant">
                                {m.version}
                              </span>
                            </td>
                            <td className="py-4 px-5 text-on-surface-variant">{m.provider}</td>
                            <td className="py-4 px-5">
                              <div className="flex gap-1 flex-wrap">
                                {(m.sensitive_cols ?? []).map((c: string) => (
                                  <span key={c} className="bg-surface-container text-on-surface-variant px-2 py-0.5 rounded text-[11px] border border-outline-variant">
                                    {c}
                                  </span>
                                ))}
                              </div>
                            </td>
                            <td className="py-4 px-5">
                              <div className="flex items-center gap-2">
                                <div className="w-20 bg-surface-container-high rounded-full h-2">
                                  <div
                                    className={`h-2 rounded-full ${m.equity_score >= 0.85 ? "bg-primary" : m.equity_score >= 0.75 ? "bg-secondary" : "bg-error"}`}
                                    style={{ width: `${(m.equity_score ?? 0) * 100}%` }}
                                  />
                                </div>
                                <span className="font-code text-code text-on-surface">{(m.equity_score ?? 0).toFixed(2)}</span>
                              </div>
                            </td>
                            <td className="py-4 px-5">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${STATUS_STYLE(status)}`}>
                                {status}
                              </span>
                            </td>
                            <td className="py-4 px-5 text-right">
                              <div className="flex items-center justify-end gap-2">
                                <button
                                  onClick={(e) => handleScan(e, m.model_id)}
                                  className="px-3 py-1.5 border border-outline-variant rounded-lg text-on-surface-variant hover:text-white hover:bg-surface-container-high transition-colors flex items-center gap-1.5 text-label-sm"
                                  title="Scan Now"
                                >
                                  <span className={`material-symbols-outlined text-[16px] ${scanningId === m.model_id ? "animate-spin" : ""}`}>
                                    {scanningId === m.model_id ? "progress_activity" : "refresh"}
                                  </span>
                                  Scan
                                </button>
                                <button
                                  onClick={(e) => { e.stopPropagation(); navigate(`/models/${m.model_id}`); }}
                                  className="px-3 py-1.5 border border-outline-variant rounded-lg text-on-surface-variant hover:text-white hover:bg-surface-container-high transition-colors flex items-center gap-1.5 text-label-sm"
                                >
                                  <span className="material-symbols-outlined text-[16px]">open_in_new</span>
                                  Details
                                </button>
                              </div>
                            </td>
                          </tr>
                          {/* Expanded Row */}
                          {expandedRow === m.model_id && (
                            <tr>
                              <td colSpan={7} className="bg-surface-container-lowest px-5 py-4">
                                <div className="grid grid-cols-3 gap-4">
                                  <div className="bg-surface-container border border-outline-variant rounded-lg p-3">
                                    <p className="text-label-sm text-on-surface-variant uppercase mb-2">Last Audited</p>
                                    <p className="text-body-md text-on-surface">{m.last_audited ? new Date(m.last_audited).toLocaleDateString() : "—"}</p>
                                  </div>
                                  <div className="bg-surface-container border border-outline-variant rounded-lg p-3">
                                    <p className="text-label-sm text-on-surface-variant uppercase mb-2">Violations</p>
                                    <p className={`text-body-md ${m.violations_count > 0 ? "text-error" : "text-primary"}`}>
                                      {m.violations_count ?? 0} active
                                    </p>
                                  </div>
                                  <div className="bg-surface-container border border-outline-variant rounded-lg p-3">
                                    <p className="text-label-sm text-on-surface-variant uppercase mb-2">Triggered By</p>
                                    <p className="text-body-md text-on-surface capitalize">{(m.triggered_by ?? "").replace("_", " ")}</p>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })}
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          <div className="bg-surface-container-lowest border-t border-[#2f2f2f] px-5 py-3 flex justify-between items-center text-sm">
            <span className="text-on-surface-variant font-label-sm">
              Showing {filtered.length} of {models.length} models
            </span>
          </div>
        </div>
      </div>

      {/* Trigger Audit Modal */}
      {showAuditModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowAuditModal(false)}>
          <div className="bg-[#171717] border border-[#2f2f2f] rounded-xl p-6 w-[400px]" onClick={(e) => e.stopPropagation()}>
            <h2 className="font-h3 text-h3 text-white mb-4">Trigger New Audit</h2>
            <label className="block mb-2 text-label-sm text-on-surface-variant">Select Model</label>
            <select
              value={selectedAuditModel}
              onChange={(e) => setSelectedAuditModel(e.target.value)}
              className="w-full bg-surface-container-low border border-outline-variant rounded-lg px-3 py-2 text-on-surface mb-6 focus:outline-none focus:border-primary-container"
            >
              {models.map((m: any) => (
                <option key={m.model_id} value={m.model_id}>{m.name}</option>
              ))}
            </select>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowAuditModal(false)}
                className="px-4 py-2 border border-[#2f2f2f] rounded-lg text-[#b4b4b4] hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  triggerScan.mutate(selectedAuditModel);
                  setShowAuditModal(false);
                }}
                className="px-4 py-2 bg-[#10a37f] text-white rounded-lg hover:bg-[#0e906f] transition-colors flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-[18px]">play_circle</span>
                Run Audit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
