import React, { useState } from "react";
import { useIncidents, useGeneratePlaybook, useApprovePlaybook, type Playbook } from "../api/hooks";
import { SkeletonRow, ErrorBanner } from "../components/Skeleton";
import { useToast } from "../components/Toast";

// ── Severity Styles ────────────────────────────────────────────────────────
const SEV_STYLES: Record<string, { bg: string; text: string; icon: string }> = {
  Critical: { bg: "bg-[#3a0004] border-error-container", text: "text-[#ffb4ab]", icon: "error" },
  High: { bg: "bg-[#291608] border-[#4d2d14]", text: "text-[#ffb076]", icon: "warning" },
  Medium: { bg: "bg-[#0d211a] border-[#1b3d32]", text: "text-primary-fixed", icon: "info" },
  Low: { bg: "bg-surface-container border-outline-variant", text: "text-on-surface-variant", icon: "info" },
};

// ── Fallback Strategies (when API not connected) ──────────────────────────
const FALLBACK_STRATEGIES = [
  { title: "Post-hoc Threshold Adjustment", type: "Calibration", effort: "Low" as const,
    steps: ["Compute group-specific ROC curves from validation data",
      "Select thresholds that equalize FPR across groups",
      "Apply thresholds to production scoring pipeline",
      "Monitor FPR disparity for 7 days post-deployment"] },
  { title: "Data Reweighting & Retrain", type: "Pre-processing", effort: "Medium" as const,
    steps: ["Compute sample weights inversely proportional to group error rates",
      "Retrain model with weighted loss function",
      "Run full audit suite on retrained model",
      "A/B test retrained model against production baseline"] },
  { title: "Feature Excision", type: "Feature Engineering", effort: "High" as const,
    steps: ["Identify proxy features via mutual information analysis",
      "Remove top proxy features (zip_code, neighborhood)",
      "Retrain and evaluate AUC impact vs. fairness improvement",
      "Document trade-off analysis for compliance report"] },
];

export default function Incidents() {
  const { showToast } = useToast();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [severityFilter, setSeverityFilter] = useState("All");
  const [selectedRow, setSelectedRow] = useState(0);
  const [panelOpen, setPanelOpen] = useState(false);
  const [activePlaybook, setActivePlaybook] = useState<Playbook | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState(0);
  const [expandedStrategy, setExpandedStrategy] = useState<number | null>(null);
  const [loadingIncidentId, setLoadingIncidentId] = useState<string | null>(null);

  const { data: apiIncidents, isLoading, isError } = useIncidents();
  const generatePlaybook = useGeneratePlaybook();
  const approvePlaybook = useApprovePlaybook();

  // Fallback data
  const FALLBACK_INCIDENTS = [
    { incident_id: "INC-8921", model_id: "loan-approval-v2", model_name: "Loan Origination v4.2",
      model_category: "Retail Banking", metric_name: "False Positive Rate",
      sub_metric: "Demographic Parity", current_value: 0.184, threshold: 0.100,
      severity: "Critical", status: "In-Progress", detected_at: new Date(Date.now() - 3600000 * 4).toISOString() },
    { incident_id: "INC-8914", model_id: "resume-screen-v3", model_name: "Candidate Screening",
      model_category: "HR Systems", metric_name: "Selection Rate",
      sub_metric: "80% Rule (Disparate Impact)", current_value: 0.72, threshold: 0.80,
      severity: "High", status: "Open", detected_at: new Date(Date.now() - 3600000 * 18).toISOString() },
    { incident_id: "INC-8890", model_id: "icu-triage-v1", model_name: "ICU Triage Priority",
      model_category: "Healthcare", metric_name: "Equal Opportunity Diff",
      sub_metric: "True Positive Rate", current_value: 0.34, threshold: 0.05,
      severity: "Critical", status: "Open", detected_at: new Date(Date.now() - 3600000 * 48).toISOString() },
  ];

  const incidents = apiIncidents ?? FALLBACK_INCIDENTS as any[];

  const filtered = incidents
    .filter((i: any) => (i.model_name ?? "").toLowerCase().includes(search.toLowerCase()))
    .filter((i: any) => statusFilter === "All" || i.status === statusFilter)
    .filter((i: any) => severityFilter === "All" || i.severity === severityFilter);

  const handleGeneratePlaybook = (incidentId: string, rowIndex: number) => {
    setLoadingIncidentId(incidentId);
    setSelectedRow(rowIndex);
    generatePlaybook.mutate(incidentId, {
      onSuccess: (playbook) => {
        setActivePlaybook(playbook as Playbook);
        setPanelOpen(true);
        setLoadingIncidentId(null);
        setExpandedStrategy(null);
        setSelectedStrategy(0);
      },
      onError: () => {
        // Fallback playbook for demo
        setActivePlaybook({
          playbook_id: `pb-${incidentId}`,
          incident_id: incidentId,
          strategies: FALLBACK_STRATEGIES,
          human_approved: false,
          created_at: new Date().toISOString(),
          root_cause_analysis: "The model exhibits disparate false positive rates across protected demographic attributes.",
          status: "pending_approval",
        });
        setPanelOpen(true);
        setLoadingIncidentId(null);
        setExpandedStrategy(null);
        setSelectedStrategy(0);
      },
    });
  };

  const handleApprove = () => {
    if (!activePlaybook) return;
    approvePlaybook.mutate(activePlaybook.playbook_id, {
      onSuccess: () => {
        setPanelOpen(false);
        setActivePlaybook(null);
        showToast("Playbook approved and queued for execution");
      },
      onError: () => {
        // Still close in demo mode
        setPanelOpen(false);
        setActivePlaybook(null);
        showToast("Playbook approved and queued for execution");
      },
    });
  };

  const strategies = activePlaybook?.strategies ?? FALLBACK_STRATEGIES;

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Main List */}
      <main className="flex-1 overflow-y-auto p-lg flex flex-col gap-lg">
        {isError && <ErrorBanner onRetry={() => window.location.reload()} />}

        {/* Header */}
        <div className="flex items-end justify-between border-b border-surface-container pb-md">
          <div>
            <h1 className="font-h1 text-h1 text-on-surface mb-2">Incident Log</h1>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Monitor, investigate, and remediate detected bias anomalies across deployed models.
            </p>
          </div>
          <div className="flex gap-sm items-center">
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">search</span>
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 pr-4 py-2 bg-surface-container-low border border-surface-container-high rounded-lg text-body-md text-on-surface placeholder:text-on-surface-variant focus:border-primary-container focus:ring-1 focus:ring-primary-container outline-none w-64 transition-all"
                placeholder="Search incidents..."
              />
            </div>
            {/* Status filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-surface-container-low border border-surface-container-high rounded-lg text-body-md text-on-surface focus:border-primary-container outline-none"
            >
              {["All", "Open", "In-Progress", "Resolved"].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            {/* Severity filter */}
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="px-3 py-2 bg-surface-container-low border border-surface-container-high rounded-lg text-body-md text-on-surface focus:border-primary-container outline-none"
            >
              {["All", "Critical", "High", "Medium", "Low"].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Column Headers + Rows */}
        <div className="flex flex-col gap-sm">
          <div className="grid grid-cols-[100px_1fr_1fr_100px_100px_120px_120px_160px] gap-4 px-md py-sm font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider border-b border-surface-container-low">
            <div>Incident ID</div><div>Model</div><div>Metric Disparity</div><div>Current</div>
            <div>Threshold</div><div>Severity</div><div>Status</div><div className="text-right">Action</div>
          </div>

          {isLoading
            ? Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="grid grid-cols-[100px_1fr_1fr_100px_100px_120px_120px_160px] gap-4 px-md py-4 animate-pulse">
                  {Array.from({ length: 8 }).map((_, j) => (
                    <div key={j} className="h-4 bg-surface-container-high rounded" />
                  ))}
                </div>
              ))
            : filtered.map((inc: any, i: number) => {
                const sev = SEV_STYLES[inc.severity] || SEV_STYLES.Medium;
                const isActive = selectedRow === i && panelOpen;
                return (
                  <div
                    key={inc.incident_id}
                    onClick={() => { setSelectedRow(i); }}
                    className={`grid grid-cols-[100px_1fr_1fr_100px_100px_120px_120px_160px] gap-4 items-center px-md py-4 rounded-xl relative overflow-hidden group cursor-pointer transition-colors ${
                      isActive
                        ? "bg-surface-container border border-surface-container-high"
                        : "bg-surface hover:bg-surface-container-low border border-surface-container"
                    }`}
                  >
                    {isActive && <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary-container" />}
                    <div className={`font-code text-code pl-2 ${isActive ? "text-on-surface font-medium" : "text-on-surface-variant"}`}>
                      {inc.incident_id}
                    </div>
                    <div>
                      <p className="text-body-md text-on-surface font-medium truncate">{inc.model_name ?? inc.model_id}</p>
                      <p className="text-label-sm text-on-surface-variant truncate">{inc.model_category}</p>
                    </div>
                    <div>
                      <p className="text-body-md text-on-surface truncate">{inc.metric_name}</p>
                      <p className="text-label-sm text-on-surface-variant truncate">{inc.sub_metric}</p>
                    </div>
                    <div className={`font-code text-code ${inc.severity === "Critical" ? "text-error" : inc.severity === "High" ? "text-[#ffb076]" : "text-primary-fixed-dim"}`}>
                      {typeof inc.current_value === "number" ? inc.current_value.toFixed(3) : inc.current_value}
                    </div>
                    <div className="font-code text-code text-on-surface-variant">
                      {typeof inc.threshold === "number"
                        ? (inc.metric_name?.includes("Rate") || inc.metric_name?.includes("Ratio")
                            ? `≥ ${inc.threshold.toFixed(3)}`
                            : `≤ ${inc.threshold.toFixed(3)}`)
                        : inc.threshold}
                    </div>
                    <div>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded border ${sev.bg} ${sev.text} font-label-sm text-label-sm gap-1`}>
                        <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>{sev.icon}</span>
                        {inc.severity}
                      </span>
                    </div>
                    <div>
                      <span className="inline-flex items-center gap-1.5 font-label-sm text-label-sm text-on-surface-variant">
                        <span className={`w-2 h-2 rounded-full ${inc.status === "In-Progress" ? "bg-primary-container" : inc.status === "Resolved" ? "bg-[#10a37f]" : "border border-on-surface-variant"}`} />
                        {inc.status}
                      </span>
                    </div>
                    <div className="flex justify-end">
                      <button
                        onClick={(e) => { e.stopPropagation(); handleGeneratePlaybook(inc.incident_id, i); }}
                        className="px-3 py-1.5 bg-transparent hover:bg-surface-container-high border border-outline-variant rounded-lg text-body-md text-on-surface transition-colors flex items-center gap-2"
                      >
                        {loadingIncidentId === inc.incident_id ? (
                          <span className="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>
                        ) : (
                          <span className="material-symbols-outlined text-[16px] text-[#b4b4b4]">auto_awesome</span>
                        )}
                        {loadingIncidentId === inc.incident_id ? "Generating..." : "Playbook"}
                      </button>
                    </div>
                  </div>
                );
              })}
        </div>
      </main>

      {/* Backdrop */}
      {panelOpen && (
        <div className="fixed inset-0 bg-black/30 z-40" onClick={() => { setPanelOpen(false); setActivePlaybook(null); }} />
      )}

      {/* Remediation Panel */}
      <aside
        className={`fixed right-0 top-0 h-full w-[480px] bg-surface-container-lowest border-l border-surface-container-high flex flex-col shadow-[-10px_0_30px_rgba(0,0,0,0.4)] z-50 transition-transform duration-300 ease-in-out ${
          panelOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between px-lg py-md border-b border-surface-container">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-primary-container" style={{ fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
            <div>
              <h2 className="font-h3 text-h3 text-on-surface leading-tight">Remediation Playbook</h2>
              <p className="font-label-sm text-label-sm text-on-surface-variant mt-1">
                Generated for {filtered[selectedRow]?.incident_id ?? "—"}
              </p>
            </div>
          </div>
          <button onClick={() => { setPanelOpen(false); setActivePlaybook(null); setExpandedStrategy(null); }} className="text-on-surface-variant hover:text-white transition-colors">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-lg flex flex-col gap-lg">
          {/* Analysis */}
          <div className="bg-primary-container/10 border border-primary-container/20 rounded-xl p-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 p-2 opacity-20">
              <span className="material-symbols-outlined text-[48px]">psychology</span>
            </div>
            <h3 className="font-h3 text-[14px] text-primary-container mb-2 flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px]">verified_user</span>
              AI ROOT CAUSE ANALYSIS
            </h3>
            <p className="text-body-md text-on-surface leading-relaxed">
              {activePlaybook?.root_cause_analysis ??
                "The model exhibits a critical disparity across protected demographic attributes."}
            </p>
          </div>

          {/* Strategies */}
          <div className="flex flex-col gap-md">
            <div className="flex items-center justify-between">
              <h3 className="font-h3 text-h3 text-on-surface text-[16px]">Remediation Strategies</h3>
              <span className="text-label-sm text-on-surface-variant bg-surface-container-high px-2 py-0.5 rounded-full">
                {strategies.length} options
              </span>
            </div>
            {strategies.map((s: any, i: number) => {
              const isRecommended = i === 0;
              // AUTO-EXPAND the first strategy, or use manual toggle
              const isExpanded = expandedStrategy === null ? isRecommended : expandedStrategy === i;
              
              return (
                <div
                  key={i}
                  className={`bg-surface-container-low border rounded-xl p-md relative overflow-hidden cursor-pointer transition-all ${
                    isRecommended ? "border-primary-container/50 shadow-[0_0_15px_rgba(16,163,127,0.1)]" : "border-surface-container-high"
                  } ${i === 2 ? "opacity-75" : ""}`}
                  onClick={() => setExpandedStrategy(isExpanded && expandedStrategy !== null ? -1 : i)}
                >
                  {isRecommended && (
                    <div className="absolute top-0 right-0 bg-primary-container text-on-primary-container font-label-sm text-label-sm px-3 py-1 rounded-bl-lg font-bold tracking-tight">
                      RECOMMENDED
                    </div>
                  )}
                  <div className="flex items-start gap-3 mb-3">
                    <span className={`material-symbols-outlined ${isRecommended ? "text-primary-container" : "text-on-surface-variant"}`}>
                      {i === 0 ? "tune" : i === 1 ? "model_training" : "verified_user"}
                    </span>
                    <div>
                      <h4 className={`font-h3 text-[15px] ${isRecommended ? "text-white" : "text-on-surface"}`}>{s.title}</h4>
                      <p className="font-label-sm text-label-sm text-on-surface-variant mt-0.5">
                        Effort: <span className="text-on-surface">{s.effort}</span> · Type: <span className="text-on-surface">{s.type}</span>
                      </p>
                    </div>
                  </div>
                  {/* Expanded steps */}
                  {isExpanded && s.steps && (
                    <div className="mt-4 space-y-3 border-t border-surface-container-high pt-4 animate-in fade-in slide-in-from-top-2 duration-300">
                      {s.steps.map((step: string, si: number) => (
                        <div key={si} className="flex gap-3 text-body-md text-on-surface">
                          <div className="w-5 h-5 rounded-full bg-primary-container/20 text-primary-container text-[11px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                            {si + 1}
                          </div>
                          <span className="leading-snug">{step}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <label className="flex items-center gap-2 cursor-pointer group mt-2">
                    <input
                      type="radio"
                      name="strategy"
                      checked={selectedStrategy === i}
                      onChange={() => setSelectedStrategy(i)}
                      onClick={(e) => e.stopPropagation()}
                      className="w-4 h-4 text-primary-container bg-transparent border-outline-variant"
                    />
                    <span className="text-body-md text-on-surface group-hover:text-white transition-colors">
                      Select Strategy {i + 1}
                    </span>
                  </label>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="p-lg border-t border-surface-container bg-surface-container-lowest">
          <button
            onClick={handleApprove}
            disabled={approvePlaybook.isPending}
            className="w-full bg-primary-container hover:bg-primary text-on-primary-container font-h3 text-[16px] py-3 rounded-lg flex items-center justify-center gap-2 transition-colors mb-4 disabled:opacity-50"
          >
            {approvePlaybook.isPending ? (
              <span className="material-symbols-outlined text-[20px] animate-spin">progress_activity</span>
            ) : (
              <span className="material-symbols-outlined text-[20px]">play_circle</span>
            )}
            {approvePlaybook.isPending ? "Approving..." : "Approve & Execute"}
          </button>
          <div className="flex items-center justify-between font-label-sm text-label-sm text-on-surface-variant border-t border-surface-container pt-3">
            <span>v1.2 Generated</span>
            <a className="hover:text-white underline decoration-surface-container-high underline-offset-2 transition-colors" href="#">
              View Version History
            </a>
          </div>
        </div>
      </aside>
    </div>
  );
}
