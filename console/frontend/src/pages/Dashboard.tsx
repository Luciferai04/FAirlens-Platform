import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useModels, useIncidents } from "../api/hooks";
import { SkeletonCard, SkeletonRow, ErrorBanner } from "../components/Skeleton";

// ── Helpers ────────────────────────────────────────────────────────────────
const timeAgo = (iso: string) => {
  const diff = Date.now() - new Date(iso).getTime();
  const h = Math.floor(diff / 3600000);
  if (h < 1) return "Just now";
  return h < 24 ? `${h}h ago` : `${Math.floor(h / 24)}d ago`;
};

const barColor = (score: number) =>
  score < 0.8 ? "bg-error" : score < 0.85 ? "bg-secondary" : "bg-primary";

const sevStyle = (sev: string) => {
  switch (sev) {
    case "Critical":
      return "bg-error-container text-on-error-container";
    case "High":
      return "bg-[#3a1a00] text-[#ffb873] border border-[#6a3b00]";
    case "Medium":
      return "bg-surface-container text-secondary border border-outline-variant";
    default:
      return "bg-surface-container text-on-surface-variant border border-outline-variant";
  }
};

// ── Fallback Data (renders if API is down) ─────────────────────────────────
const FALLBACK_MODELS = [
  { model_id: "loan-approval-v2", name: "Loan Origination v4.2", equity_score: 0.72, passed: false, violations_count: 2, ebi_score: 54 },
  { model_id: "resume-screen-v3", name: "Resume Screening", equity_score: 0.92, passed: true, violations_count: 0, ebi_score: 88 },
  { model_id: "icu-triage-v1", name: "ICU Triage Priority", equity_score: 0.58, passed: false, violations_count: 4, ebi_score: 42 },
  { model_id: "credit-scoring-v5", name: "Credit Scorer Baseline", equity_score: 0.88, passed: true, violations_count: 0, ebi_score: 91 },
  { model_id: "content-rec-v2", name: "Content Feed Ranking", equity_score: 0.79, passed: false, violations_count: 1, ebi_score: 76 },
];

const FALLBACK_INCIDENTS = [
  { incident_id: "INC-8921", model_name: "Loan Origination v4.2", metric_name: "False Positive Rate", severity: "Critical", status: "In-Progress", detected_at: new Date(Date.now() - 3600000 * 4).toISOString() },
  { incident_id: "INC-8914", model_name: "Candidate Screening", metric_name: "Selection Rate", severity: "High", status: "Open", detected_at: new Date(Date.now() - 3600000 * 18).toISOString() },
  { incident_id: "INC-8890", model_name: "ICU Triage Priority", metric_name: "Equal Opportunity Diff", severity: "Critical", status: "Open", detected_at: new Date(Date.now() - 3600000 * 48).toISOString() },
];

// ── Component ──────────────────────────────────────────────────────────────
export default function Dashboard() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const { data: apiModels, isLoading: modelsLoading, isError: modelsError } = useModels();
  const { data: apiIncidents, isLoading: incidentsLoading, isError: incidentsError } = useIncidents();

  // SOS NOTIFICATION LOGIC
  const [showSOS, setShowSOS] = useState(false);
  const criticalIncident = apiIncidents?.find((inc: any) => inc.severity === 'Critical' && inc.status === 'Open');

  useEffect(() => {
    if (criticalIncident) {
      // Simulate "Real-Time" arrival for the demo
      const timer = setTimeout(() => setShowSOS(true), 3000);
      return () => clearTimeout(timer);
    }
  }, [criticalIncident]);

  // Use API data, fall back to hardcoded
  const models = apiModels ?? FALLBACK_MODELS as any[];
  const incidents = apiIncidents ?? FALLBACK_INCIDENTS as any[];

  const openIncidents = incidents.filter((i: any) => i.status === "Open" || i.status === "In-Progress");
  const avgEquity = models.length > 0
    ? (models.reduce((s: number, m: any) => s + (m.equity_score ?? 0), 0) / models.length)
    : 0;
  const sortedModels = [...models].sort((a: any, b: any) => (a.equity_score ?? 0) - (b.equity_score ?? 0));

  const filteredIncidents = incidents.filter((i: any) =>
    (i.model_name ?? "").toLowerCase().includes(search.toLowerCase())
  );

  const KPI = [
    { label: "Models Monitored", value: models.length, icon: "monitor_heart", iconColor: "text-primary" },
    { label: "Active Incidents", value: openIncidents.length, icon: "warning", iconColor: "text-error",
      badge: openIncidents.length > 0 ? `${openIncidents.filter((i: any) => i.severity === "Critical").length} critical` : undefined,
      badgeClass: "bg-error-container text-on-error-container" },
    { label: "Avg. Equity Score", value: avgEquity.toFixed(2), icon: "balance", iconColor: "text-primary",
      badge: avgEquity >= 0.85 ? "Healthy" : avgEquity >= 0.75 ? "Marginal" : "At Risk",
      badgeClass: avgEquity >= 0.85 ? "bg-primary/10 text-primary" : avgEquity >= 0.75 ? "bg-surface-container text-secondary" : "bg-error-container text-on-error-container" },
    { label: "Avg. Bias Index", value: Math.round(models.reduce((s: number, m: any) => s + (m.ebi_score ?? 0), 0) / (models.length || 1)), icon: "shield", iconColor: "text-[#10a37f]" },
    { label: "Compliance Coverage", value: "94%", icon: "verified", iconColor: "text-primary" },
  ];

  return (
    <div className="flex-1 p-lg overflow-y-auto relative">
      {/* SOS Slack-style Notification */}
      {showSOS && criticalIncident && (
        <div className="fixed bottom-8 right-8 z-[100] animate-in slide-in-from-right-10 duration-500">
          <div className="bg-[#1a1d21] border border-[#d13438] rounded-lg shadow-2xl w-[380px] overflow-hidden">
            <div className="bg-[#d13438] px-3 py-1 flex items-center justify-between">
              <div className="flex items-center gap-2 text-white font-bold text-[12px]">
                <span className="material-symbols-outlined text-[16px]">notifications_active</span>
                SOS EMERGENCY ALERT
              </div>
              <button onClick={() => setShowSOS(false)} className="text-white hover:opacity-70">
                <span className="material-symbols-outlined text-[16px]">close</span>
              </button>
            </div>
            <div className="p-4 flex gap-3">
              <div className="w-10 h-10 rounded bg-[#d13438]/20 flex items-center justify-center shrink-0">
                <span className="material-symbols-outlined text-[#d13438]">warning</span>
              </div>
              <div>
                <h4 className="text-white font-bold text-[14px]">Pipeline Blocked: {criticalIncident.model_name}</h4>
                <p className="text-[#ababad] text-[13px] mt-1">
                  Critical bias detected in production build. Deployment halted automatically.
                </p>
                <div className="mt-3 flex gap-2">
                  <button 
                    onClick={() => { setShowSOS(false); navigate("/incidents"); }}
                    className="bg-[#d13438] text-white text-[12px] font-bold px-3 py-1.5 rounded hover:bg-[#a4262c] transition-colors"
                  >
                    INVESTIGATE NOW
                  </button>
                  <button className="text-[#ababad] text-[12px] px-3 py-1.5 hover:text-white" onClick={() => setShowSOS(false)}>Ignore</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      <div className="max-w-[1400px] mx-auto w-full">
        {/* Error Banner */}
        {(modelsError || incidentsError) && (
          <div className="mb-lg">
            <ErrorBanner onRetry={() => window.location.reload()} />
          </div>
        )}

        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-lg gap-4">
          <div>
            <h1 className="font-h2 text-h2 text-on-surface">Governance Dashboard</h1>
            <p className="font-body-md text-body-md text-on-surface-variant mt-xs">
              Real-time monitoring of AI fairness metrics across all deployed models.
            </p>
          </div>
          <div className="flex gap-sm">
            <button className="bg-surface border border-outline-variant text-on-surface hover:text-white px-4 py-2 rounded-lg text-body-md transition-colors flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px]">download</span> Export Report
            </button>
            <button className="bg-brand text-white hover:bg-brand-hover px-4 py-2 rounded-lg text-body-md font-medium transition-colors flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px]">add</span> New Audit
            </button>
          </div>
        </div>

        {/* KPI Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-md mb-lg">
          {modelsLoading
            ? Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
            : KPI.map((kpi, i) => (
                <div
                  key={i}
                  className="bg-surface border border-outline-variant p-md rounded-xl h-32 flex flex-col justify-between group hover:border-primary/30 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
                      {kpi.label}
                    </span>
                    <span className={`material-symbols-outlined ${kpi.iconColor} text-[20px]`}>
                      {kpi.icon}
                    </span>
                  </div>
                  <div className="flex items-end justify-between">
                    <span className="text-[32px] font-bold text-white leading-none">{kpi.value}</span>
                    {kpi.badge && (
                      <span className={`${kpi.badgeClass} px-2 py-0.5 rounded text-[11px] font-medium`}>
                        {kpi.badge}
                      </span>
                    )}
                  </div>
                  {/* Progress bar for compliance */}
                  {i === 3 && (
                    <div className="w-full bg-surface-container-high rounded-full h-1.5 mt-1">
                      <div className="bg-primary h-1.5 rounded-full" style={{ width: "94%" }} />
                    </div>
                  )}
                </div>
              ))}
        </div>

        {/* Main Grid: Equity Chart + Alerts */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-lg mb-lg">
          {/* Equity Score Distribution */}
          <div className="xl:col-span-2 bg-surface border border-outline-variant rounded-xl p-md">
            <div className="flex items-center justify-between mb-md">
              <h2 className="font-h3 text-h3 text-on-surface">Equity Score Distribution</h2>
              <span className="font-label-sm text-label-sm text-on-surface-variant">
                Threshold: 0.85
              </span>
            </div>
            <div className="space-y-3">
              {sortedModels.map((m: any) => (
                <div
                  key={m.model_id}
                  className="flex items-center gap-4 cursor-pointer group"
                  onClick={() => navigate(`/models/${m.model_id}`)}
                >
                  <span className="text-body-md text-on-surface-variant w-48 truncate group-hover:text-white transition-colors">
                    {m.name}
                  </span>
                  <div className="flex-1 bg-surface-container-high rounded-full h-6 overflow-hidden flex relative">
                    <div
                      className={`h-full ${barColor(m.equity_score)} transition-all duration-500 flex items-center justify-end pr-2`}
                      style={{ width: `${(m.equity_score ?? 0) * 100}%` }}
                    >
                      <span className="text-[10px] font-semibold text-black/80">
                        EQ: {(m.equity_score ?? 0).toFixed(2)}
                      </span>
                    </div>
                    {/* EBI Marker */}
                    <div 
                      className="absolute top-0 bottom-0 w-0.5 bg-white shadow-[0_0_5px_rgba(255,255,255,0.8)] z-10"
                      style={{ left: `${(m.ebi_score ?? 0)}%` }}
                      title={`EBI: ${Math.round(m.ebi_score)}`}
                    />
                  </div>
                  <span className="font-code text-xs font-bold w-12 text-right" style={{ color: m.ebi_score >= 90 ? "#10a37f" : m.ebi_score >= 75 ? "#f59e0b" : "#ef4444" }}>
                    {Math.round(m.ebi_score ?? 0)}
                  </span>
                </div>
              ))}
            </div>
            {/* X-axis labels */}
            <div className="flex justify-between mt-3 font-label-sm text-label-sm text-on-surface-variant">
              <span>0.0</span><span>0.5</span><span className="text-primary">0.85</span><span>1.0</span>
            </div>
          </div>

          {/* Recent Alerts */}
          <div className="xl:col-span-1 bg-surface border border-outline-variant rounded-xl p-md">
            <h2 className="font-h3 text-h3 text-on-surface mb-md">Recent Alerts</h2>
            <div className="space-y-3">
              {openIncidents.slice(0, 3).map((inc: any, i: number) => {
                const isCritical = inc.severity === "Critical";
                return (
                  <div
                    key={inc.incident_id || i}
                    className={`relative border rounded-lg p-3 pl-5 overflow-hidden ${
                      isCritical
                        ? "border-error-container bg-[#1a0a0a]"
                        : "border-outline-variant bg-surface-container-low"
                    }`}
                  >
                    <div
                      className={`absolute left-0 top-0 bottom-0 w-1 ${
                        isCritical ? "bg-error" : "bg-secondary"
                      }`}
                    />
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-body-md text-on-surface font-medium">
                          {inc.model_name ?? inc.model_id}
                        </p>
                        <p className="text-label-sm text-on-surface-variant">
                          {inc.metric_name}
                        </p>
                      </div>
                      <span className="text-label-sm text-on-surface-variant whitespace-nowrap ml-2">
                        {timeAgo(inc.detected_at)}
                      </span>
                    </div>
                  </div>
                );
              })}
              {openIncidents.length === 0 && !incidentsLoading && (
                <p className="text-body-md text-on-surface-variant text-center py-4">
                  No active alerts
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Detailed Incident Table */}
        <div className="bg-surface border border-outline-variant rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-md py-3 border-b border-surface-container">
            <h2 className="font-h3 text-h3 text-on-surface">Incident Overview</h2>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">
                search
              </span>
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 pr-4 py-1.5 bg-surface-container-low border border-surface-container-high rounded-lg text-body-md text-on-surface placeholder:text-on-surface-variant focus:border-primary-container focus:ring-1 focus:ring-primary-container outline-none w-56 transition-all"
                placeholder="Search models..."
              />
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse whitespace-nowrap">
              <thead>
                <tr className="bg-surface-container-lowest">
                  {["Incident ID", "Model", "Metric", "Severity", "Status", ""].map(
                    (h, i) => (
                      <th
                        key={i}
                        className={`py-3 px-5 font-label-sm text-label-sm text-on-surface-variant font-medium tracking-wide uppercase ${
                          i === 5 ? "text-right" : ""
                        }`}
                      >
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2f2f2f] font-body-md text-body-md">
                {incidentsLoading
                  ? Array.from({ length: 3 }).map((_, i) => (
                      <SkeletonRow key={i} cols={6} />
                    ))
                  : filteredIncidents.map((inc: any) => (
                      <tr
                        key={inc.incident_id}
                        className="hover:bg-surface-container-low transition-colors group cursor-pointer"
                        onClick={() => navigate("/incidents")}
                      >
                        <td className="py-3 px-5 text-white font-medium font-code text-code">
                          {inc.incident_id}
                        </td>
                        <td className="py-3 px-5 text-on-surface">
                          {inc.model_name ?? inc.model_id}
                        </td>
                        <td className="py-3 px-5 text-on-surface-variant">
                          {inc.metric_name}
                        </td>
                        <td className="py-3 px-5">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${sevStyle(
                              inc.severity
                            )}`}
                          >
                            {inc.severity}
                          </span>
                        </td>
                        <td className="py-3 px-5">
                          <span className="inline-flex items-center gap-1.5 font-label-sm text-label-sm text-on-surface-variant">
                            <span
                              className={`w-2 h-2 rounded-full ${
                                inc.status === "In-Progress"
                                  ? "bg-primary-container"
                                  : inc.status === "Resolved"
                                  ? "bg-[#10a37f]"
                                  : "border border-on-surface-variant"
                              }`}
                            />
                            {inc.status}
                          </span>
                        </td>
                        <td className="py-3 px-5 text-right">
                          <button className="text-on-surface-variant hover:text-white opacity-0 group-hover:opacity-100 transition-all">
                            <span className="material-symbols-outlined text-[18px]">
                              arrow_forward
                            </span>
                          </button>
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
