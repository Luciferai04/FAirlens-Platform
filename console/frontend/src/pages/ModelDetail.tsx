import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useModelAudit, useModels, useEBI } from "../api/hooks";
import { EBIWidget } from "../components/EBIWidget";

// ── Helpers ────────────────────────────────────────────────────────────────
const formatMetric = (name: string) =>
  name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

const THRESHOLDS: Record<string, number> = {
  demographic_parity_difference: 0.1,
  equalized_odds_difference: 0.1,
  disparate_impact_ratio: 0.8,
  calibration_error: 0.1,
  theil_index: 0.15,
  statistical_parity_difference: 0.1,
  average_odds_difference: 0.1,
  equal_opportunity_difference: 0.1,
};

const isRatioBased = (metric: string) => metric.includes("ratio");

export default function ModelDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: audit, isLoading: auditLoading } = useModelAudit(id!);
  const { data: ebiData } = useEBI(id!);
  const { data: models } = useModels();
  const model = models?.find((m) => m.model_id === id);

  // SVG radar dimensions
  const CX = 150, CY = 150, R = 110;

  const metricEntries = audit?.metrics ? Object.entries(audit.metrics) : [];
  const numAxes = metricEntries.length || 8;

  const radarPoints = metricEntries.map(([, groups], i) => {
    const avg = Object.values(groups).reduce((s, v) => s + v, 0) / Object.values(groups).length;
    const angle = (2 * Math.PI * i) / numAxes - Math.PI / 2;
    const r = Math.min(avg, 1) * R;
    return { x: CX + r * Math.cos(angle), y: CY + r * Math.sin(angle) };
  });

  const thresholdPoints = metricEntries.map(([name], i) => {
    const t = THRESHOLDS[name] ?? 0.1;
    const val = isRatioBased(name) ? t : 1 - t;
    const angle = (2 * Math.PI * i) / numAxes - Math.PI / 2;
    const r = Math.min(val, 1) * R;
    return { x: CX + r * Math.cos(angle), y: CY + r * Math.sin(angle) };
  });

  const polygonStr = (pts: { x: number; y: number }[]) =>
    pts.map((p) => `${p.x},${p.y}`).join(" ");

  // Timeline data
  const trendData = audit?.trend ?? [];

  return (
    <div className="flex-1 p-lg overflow-y-auto">
      <div className="max-w-[1400px] mx-auto w-full">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 mb-md">
          <button onClick={() => navigate("/models")} className="text-label-sm text-[#b4b4b4] hover:text-white transition-colors">
            Model Registry
          </button>
          <span className="material-symbols-outlined text-[16px] text-[#b4b4b4]">chevron_right</span>
          <span className="text-label-sm text-white">{model?.name ?? id}</span>
        </div>

        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-lg gap-4">
          <div>
            <h1 className="font-h1 text-h1 text-on-surface">{model?.name ?? id}</h1>
            <p className="font-body-md text-body-md text-on-surface-variant mt-xs">Fairness audit details and historical trend analysis.</p>
          </div>
          <div className="flex gap-sm">
            <button
              onClick={() => window.open(`${import.meta.env.VITE_API_URL ?? "/api"}/v1/reports/generate?model_id=${id}&framework=eeoc`, "_blank")}
              className="px-4 py-2 border border-[#2f2f2f] rounded-lg text-[#b4b4b4] hover:bg-[#212121] hover:text-white transition-colors flex items-center gap-2 text-body-md"
            >
              <span className="material-symbols-outlined text-[18px]">download</span> Export Report
            </button>
            <button className="px-4 py-2 bg-[#10a37f] hover:bg-[#0e906f] text-white rounded-lg transition-colors flex items-center gap-2 text-body-md font-medium">
              <span className="material-symbols-outlined text-[18px]">tune</span> Configure Thresholds
            </button>
          </div>
        </div>

        {/* Violations Banner */}
        {audit && !audit.passed && (
          <div className="bg-error-container/20 border border-error-container text-on-error-container px-4 py-3 rounded-lg flex items-center gap-3 mb-lg">
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>error</span>
            <span className="text-body-md">FAILING — {audit.violations?.length ?? 0} violation(s) detected across protected attributes</span>
            <button onClick={() => navigate("/incidents")} className="ml-auto text-label-sm underline hover:text-white transition-colors">
              View Incidents
            </button>
          </div>
        )}

        {/* Metadata Card */}
        <div className="bg-[#171717] border border-[#2f2f2f] rounded-xl p-md mb-lg">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <p className="text-label-sm text-on-surface-variant uppercase mb-1">Status</p>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${audit?.passed ? "bg-[#10a37f]" : "bg-error"}`} />
                <span className="text-body-md text-white font-medium">{audit?.passed ? "Passing" : "Failing"}</span>
              </div>
            </div>
            <div className="md:border-l md:border-[#2f2f2f] md:pl-6">
              <p className="text-label-sm text-on-surface-variant uppercase mb-1">Version</p>
              <p className="text-body-md text-on-surface font-code">{model?.version ?? "—"}</p>
            </div>
            <div className="md:border-l md:border-[#2f2f2f] md:pl-6">
              <p className="text-label-sm text-on-surface-variant uppercase mb-1">Protected Attrs</p>
              <div className="flex gap-1 flex-wrap">
                {(audit?.protected_cols ?? model?.sensitive_cols ?? []).map((c) => (
                  <span key={c} className="bg-surface-container text-on-surface-variant px-2 py-0.5 rounded text-[11px] border border-outline-variant">{c}</span>
                ))}
              </div>
            </div>
            <div className="md:border-l md:border-[#2f2f2f] md:pl-6">
              <p className="text-label-sm text-on-surface-variant uppercase mb-1">Last Audited</p>
              <p className="text-body-md text-on-surface">{audit?.created_at ? new Date(audit.created_at).toLocaleDateString() : "—"}</p>
            </div>
          </div>
        </div>

        {/* EBI Widget */}
        {ebiData && (
          <div className="mb-lg">
            <EBIWidget data={ebiData} />
          </div>
        )}

        {/* Loading */}
        {auditLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Charts Grid */}
        {audit && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-lg mb-lg">
            {/* Radar Chart */}
            <div className="bg-surface border border-outline-variant rounded-xl p-md">
              <h2 className="font-h3 text-h3 text-on-surface mb-md">Fairness Radar</h2>
              <svg viewBox="0 0 300 300" className="w-full max-w-[300px] mx-auto">
                {/* Concentric rings */}
                {[0.25, 0.5, 0.75, 1.0].map((s) => (
                  <circle key={s} cx={CX} cy={CY} r={R * s} fill="none" stroke="#2f2f2f" strokeWidth="0.5" />
                ))}
                {/* Axes */}
                {metricEntries.map((_, i) => {
                  const angle = (2 * Math.PI * i) / numAxes - Math.PI / 2;
                  return (
                    <line key={i} x1={CX} y1={CY} x2={CX + R * Math.cos(angle)} y2={CY + R * Math.sin(angle)}
                      stroke="#2f2f2f" strokeWidth="0.5" />
                  );
                })}
                {/* Threshold polygon */}
                {thresholdPoints.length > 2 && (
                  <polygon points={polygonStr(thresholdPoints)} fill="none" stroke="#ffb4ab"
                    strokeWidth="1" strokeDasharray="2,2" opacity="0.5" />
                )}
                {/* Data polygon */}
                {radarPoints.length > 2 && (
                  <polygon points={polygonStr(radarPoints)} fill="rgba(16,163,127,0.2)"
                    stroke="#10a37f" strokeWidth="2" />
                )}
                {/* Data dots */}
                {radarPoints.map((p, i) => (
                  <circle key={i} cx={p.x} cy={p.y} r="3" fill="#10a37f" />
                ))}
                {/* Labels */}
                {metricEntries.map(([name], i) => {
                  const angle = (2 * Math.PI * i) / numAxes - Math.PI / 2;
                  const lx = CX + (R + 20) * Math.cos(angle);
                  const ly = CY + (R + 20) * Math.sin(angle);
                  const short = name.replace(/_/g, " ").split(" ").slice(0, 2).join(" ");
                  return (
                    <text key={i} x={lx} y={ly} textAnchor="middle" dominantBaseline="middle"
                      className="fill-on-surface-variant" style={{ fontSize: "7px" }}>
                      {short}
                    </text>
                  );
                })}
              </svg>
            </div>

            {/* Equity Trend */}
            <div className="bg-surface border border-outline-variant rounded-xl p-md">
              <h2 className="font-h3 text-h3 text-on-surface mb-md">30-Day Equity Trend</h2>
              <svg viewBox="0 0 500 200" className="w-full">
                {/* Grid lines */}
                {[0, 0.25, 0.5, 0.75, 1].map((v) => (
                  <React.Fragment key={v}>
                    <line x1="40" y1={180 - v * 160} x2="490" y2={180 - v * 160}
                      stroke="#2f2f2f" strokeWidth="0.5" />
                    <text x="35" y={180 - v * 160 + 3} textAnchor="end"
                      className="fill-on-surface-variant" style={{ fontSize: "8px" }}>
                      {v.toFixed(2)}
                    </text>
                  </React.Fragment>
                ))}
                {/* Threshold line */}
                <line x1="40" y1={180 - 0.85 * 160} x2="490" y2={180 - 0.85 * 160}
                  stroke="#ffb4ab" strokeWidth="1" strokeDasharray="4,4" opacity="0.6" />
                <text x="492" y={180 - 0.85 * 160 + 3} className="fill-[#ffb4ab]"
                  style={{ fontSize: "7px" }}>0.85</text>
                {/* Gradient fill */}
                <defs>
                  <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10a37f" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#10a37f" stopOpacity="0" />
                  </linearGradient>
                </defs>
                {trendData.length > 1 && (
                  <>
                    <path
                      d={`M ${trendData.map((v, i) => `${40 + (i / (trendData.length - 1)) * 450},${180 - Math.min(v, 1) * 160}`).join(" L ")} L ${40 + 450},180 L 40,180 Z`}
                      fill="url(#trendFill)"
                    />
                    <path
                      d={`M ${trendData.map((v, i) => `${40 + (i / (trendData.length - 1)) * 450},${180 - Math.min(v, 1) * 160}`).join(" L ")}`}
                      fill="none" stroke="#10a37f" strokeWidth="2"
                    />
                    {/* Dots */}
                    {trendData.map((v, i) => {
                      const x = 40 + (i / (trendData.length - 1)) * 450;
                      const y = 180 - Math.min(v, 1) * 160;
                      const isAnomaly = v < 0.85;
                      return (
                        <circle key={i} cx={x} cy={y} r={isAnomaly ? 4 : 2}
                          fill={isAnomaly ? "#ffb4ab" : "#10a37f"}
                          stroke={isAnomaly ? "#ffb4ab" : "#10a37f"} />
                      );
                    })}
                  </>
                )}
              </svg>
            </div>
          </div>
        )}

        {/* Fairness Metrics Table */}
        {audit && metricEntries.length > 0 && (
          <div className="bg-surface border border-outline-variant rounded-xl overflow-hidden mb-lg">
            <div className="px-md py-3 border-b border-surface-container">
              <h2 className="font-h3 text-h3 text-on-surface">Metric Breakdown</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse whitespace-nowrap">
                <thead>
                  <tr className="bg-surface-container-lowest">
                    {["Metric", "Group Values", "Threshold", "Status"].map((h, i) => (
                      <th key={i} className="py-3 px-5 font-label-sm text-label-sm text-on-surface-variant font-medium tracking-wider uppercase">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2f2f2f]">
                  {metricEntries.map(([metric, groups]) => {
                    const values = Object.values(groups);
                    const maxVal = Math.max(...values);
                    const threshold = THRESHOLDS[metric] ?? 0.1;
                    const passed = isRatioBased(metric) ? maxVal >= threshold : maxVal <= threshold;
                    return (
                      <tr key={metric} className="hover:bg-surface-container-low transition-colors">
                        <td className="py-3 px-5 text-on-surface font-medium text-body-md">{formatMetric(metric)}</td>
                        <td className="py-3 px-5 text-on-surface-variant text-body-md">
                          {Object.entries(groups).map(([g, v]) => `${g}: ${v.toFixed(3)}`).join(" | ")}
                        </td>
                        <td className="py-3 px-5 font-code text-code text-on-surface-variant">
                          {isRatioBased(metric) ? "≥" : "≤"} {threshold}
                        </td>
                        <td className="py-3 px-5">
                          <span className={`material-symbols-outlined text-[18px] ${passed ? "text-[#10a37f]" : "text-error"}`}
                            style={{ fontVariationSettings: "'FILL' 1" }}>
                            {passed ? "check_circle" : "cancel"}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* SHAP Attribution Heatmap (static for now) */}
        {audit && (
          <div className="bg-surface border border-outline-variant rounded-xl overflow-hidden">
            <div className="px-md py-3 border-b border-surface-container flex items-center justify-between">
              <h2 className="font-h3 text-h3 text-on-surface">Feature Attribution (SHAP Disparity)</h2>
              <div className="flex items-center gap-2 text-label-sm text-on-surface-variant">
                <span>Low</span>
                <div className="w-24 h-2 rounded bg-gradient-to-r from-[#131313] via-[#3d4a44] to-[#10a37f]" />
                <span>High</span>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-container-lowest">
                    {["Feature", "White", "Black", "Hispanic", "Disparity"].map((h, i) => (
                      <th key={i} className="py-3 px-5 font-label-sm text-label-sm text-on-surface-variant font-medium tracking-wider uppercase">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2f2f2f]">
                  {[
                    { feature: "zip_code", white: 0.12, black: 0.91, hispanic: 0.34, disp: 0.79 },
                    { feature: "income", white: 0.82, black: 0.78, hispanic: 0.80, disp: 0.04 },
                    { feature: "credit_score", white: 0.71, black: 0.68, hispanic: 0.70, disp: 0.03 },
                    { feature: "employment_type", white: 0.21, black: 0.45, hispanic: 0.30, disp: 0.24 },
                    { feature: "loan_amount", white: 0.33, black: 0.35, hispanic: 0.34, disp: 0.02 },
                  ].map((row) => (
                    <tr key={row.feature} className="hover:bg-surface-container-low transition-colors">
                      <td className="py-3 px-5 font-code text-code text-on-surface">{row.feature}</td>
                      {[row.white, row.black, row.hispanic].map((v, i) => (
                        <td key={i} className="py-3 px-5">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-3 rounded" style={{
                              backgroundColor: `rgba(16, 163, 127, ${v})`,
                            }} />
                            <span className="text-label-sm text-on-surface-variant">{v.toFixed(2)}</span>
                          </div>
                        </td>
                      ))}
                      <td className="py-3 px-5">
                        <span className={`font-code text-code font-medium ${row.disp > 0.2 ? "text-error" : "text-on-surface-variant"}`}>
                          {row.disp.toFixed(2)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
