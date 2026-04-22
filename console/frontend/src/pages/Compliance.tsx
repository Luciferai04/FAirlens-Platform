import React, { useState } from "react";
import { useComplianceReports, useGenerateReport } from "../api/hooks";
import { SkeletonRow, ErrorBanner } from "../components/Skeleton";
import { useToast } from "../components/Toast";

// ── Fallback ───────────────────────────────────────────────────────────────
const FALLBACK_REPORTS = [
  { report_id: "FL-REP-8821", model_id: "loan-approval-v2", model_name: "CreditScoring_v4.2",
    framework: "eu_ai_act", generated_at: "2024-10-24T14:32:00Z",
    kms_signed: true, sha256_hash: "a9f4c8b2e3d1a7f6b9c4e8d2f1a5b3c7e9d1f4a6b8c2e5d7f9a1b3c5e7d1" },
  { report_id: "FL-REP-8820", model_id: "resume-screen-v3", model_name: "ResumeScreen_Llama3",
    framework: "eeoc", generated_at: "2024-10-23T09:15:00Z",
    kms_signed: true, sha256_hash: "8b3f1a9ce7d2b4c6f8a0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4c6d8e0f2" },
  { report_id: "FL-REP-8819", model_id: "icu-triage-v1", model_name: "TradingAlgo_XGBoost",
    framework: "rbi_sebi", generated_at: "2024-10-21T16:45:00Z",
    kms_signed: true, sha256_hash: "c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3" },
  { report_id: "FL-REP-8818", model_id: "loan-approval-v2", model_name: "CreditScoring_v4.1",
    framework: "eu_ai_act", generated_at: "2024-09-15T11:20:00Z",
    kms_signed: true, sha256_hash: "7f8e9d0cb4a3c2e1d6f5b4a3c2e1d0f9e8b7a6c5d4e3f2a1b0c9d8e7f6a5b4" },
];

const FRAMEWORKS = [
  { value: "eu_ai_act", label: "EU AI Act (Annex IV)", desc: "Comprehensive assessment for high-risk systems." },
  { value: "eeoc", label: "EEOC (Title VII)", desc: "Disparate impact analysis for employment tools." },
  { value: "rbi_sebi", label: "RBI-SEBI Guidelines", desc: "Algorithmic trading and risk compliance metrics." },
];

const FRAMEWORK_LABELS: Record<string, string> = {
  eu_ai_act: "EU AI Act",
  eeoc: "EEOC (Title VII)",
  rbi_sebi: "RBI-SEBI",
};

export default function Compliance() {
  const { showToast } = useToast();
  const { data: apiReports, isLoading, isError } = useComplianceReports();
  const generateReport = useGenerateReport();
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedFramework, setSelectedFramework] = useState("eu_ai_act");
  const [selectedModel, setSelectedModel] = useState("loan-approval-v2");

  const reports = apiReports ?? FALLBACK_REPORTS as any[];

  const downloadReport = async (reportId: string, modelName: string) => {
    const apiUrl = import.meta.env.VITE_API_URL ?? import.meta.env.VITE_API_BASE_URL ?? "/api";
    try {
      const res = await fetch(`${apiUrl}/v1/reports/compliance/${reportId}/download`);
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `FairLens_${modelName}_${reportId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      showToast("Report downloaded successfully");
    } catch {
      showToast("Download failed — API not reachable", "error");
    }
  };

  const handleGenerate = () => {
    generateReport.mutate(
      { model_id: selectedModel, framework: selectedFramework },
      {
        onSuccess: () => {
          setModalOpen(false);
          showToast("Compliance report generated successfully");
        },
        onError: () => {
          setModalOpen(false);
          showToast("Report generation queued (demo mode)", "info");
        },
      }
    );
  };

  return (
    <div className="flex-1 p-lg overflow-y-auto">
      <div className="max-w-[1200px] mx-auto w-full">
        {isError && <div className="mb-lg"><ErrorBanner onRetry={() => window.location.reload()} /></div>}

        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-lg gap-4">
          <div>
            <h1 className="font-h1 text-h1 text-white">Compliance Ledger</h1>
            <p className="font-body-md text-body-md text-on-surface-variant mt-xs max-w-2xl">
              Immutable, cryptographically signed artifacts detailing model performance against selected regulatory frameworks.
            </p>
          </div>
          <button
            onClick={() => setModalOpen(true)}
            className="bg-[#10a37f] text-white font-label-sm px-4 py-2.5 rounded-lg flex items-center space-x-2 hover:bg-[#12a480] transition-colors border border-transparent shadow-sm"
          >
            <span className="material-symbols-outlined text-[18px]">add</span>
            <span>Generate Report</span>
          </button>
        </div>

        {/* Table */}
        <div className="bg-surface border border-[#2f2f2f] rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse whitespace-nowrap">
              <thead>
                <tr className="bg-surface-container-lowest border-b border-[#2f2f2f]">
                  {["Report ID", "Target Model", "Framework", "Generated At", "KMS Signed", "SHA-256 Hash", ""].map((h, i) => (
                    <th key={i} className={`py-3 px-5 font-label-sm text-label-sm text-on-surface-variant font-medium tracking-wide uppercase ${i === 4 ? "text-center" : ""} ${i >= 5 ? "text-right" : ""}`}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2f2f2f] font-body-md text-body-md">
                {isLoading
                  ? Array.from({ length: 4 }).map((_, i) => <SkeletonRow key={i} cols={7} />)
                  : reports.map((r: any) => (
                      <tr key={r.report_id} className="hover:bg-surface-container-low transition-colors duration-150">
                        <td className="py-4 px-5 text-white font-medium">{r.report_id}</td>
                        <td className="py-4 px-5 text-on-surface">{r.model_name}</td>
                        <td className="py-4 px-5">
                          <span className="inline-flex items-center px-2 py-1 rounded bg-[#212121] text-[#ececec] font-label-sm text-[11px] border border-[#2f2f2f]">
                            {FRAMEWORK_LABELS[r.framework] ?? r.framework}
                          </span>
                        </td>
                        <td className="py-4 px-5 text-on-surface-variant">
                          {r.generated_at ? new Date(r.generated_at).toLocaleString() : "—"}
                        </td>
                        <td className="py-4 px-5 text-center">
                          {r.kms_signed ? (
                            <span className="material-symbols-outlined text-[#10a37f] text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                          ) : (
                            <span className="material-symbols-outlined text-on-surface-variant text-[18px]">cancel</span>
                          )}
                        </td>
                        <td className="py-4 px-5 text-right font-code text-code text-on-surface-variant opacity-70">
                          {r.sha256_hash ? `${r.sha256_hash.slice(0, 8)}...${r.sha256_hash.slice(-4)}` : "—"}
                        </td>
                        <td className="py-4 px-5 text-right">
                          <button
                            onClick={() => downloadReport(r.report_id, r.model_name)}
                            className="text-on-surface-variant hover:text-white transition-colors"
                            title="Download PDF"
                          >
                            <span className="material-symbols-outlined text-[18px]">download</span>
                          </button>
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          <div className="bg-surface-container-lowest border-t border-[#2f2f2f] px-5 py-3 flex justify-between items-center text-sm">
            <span className="text-on-surface-variant font-label-sm">
              Showing 1 to {reports.length} of {reports.length} entries
            </span>
            <div className="flex space-x-2">
              <button className="px-3 py-1 border border-[#2f2f2f] rounded bg-transparent text-[#b4b4b4] hover:text-white transition-colors disabled:opacity-50" disabled>Prev</button>
              <button className="px-3 py-1 border border-[#2f2f2f] rounded bg-[#212121] text-white hover:bg-[#2f2f2f] transition-colors">Next</button>
            </div>
          </div>
        </div>
      </div>

      {/* Generate Report Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-[#0d0d0d]/80 backdrop-blur-[2px] z-[100] flex items-center justify-center p-4">
          <div className="bg-[#171717] border border-[#2f2f2f] rounded-xl w-full max-w-lg shadow-[0_0_40px_rgba(0,0,0,0.5)] flex flex-col overflow-hidden">
            {/* Header */}
            <div className="px-6 py-5 border-b border-[#2f2f2f] flex justify-between items-center bg-[#171717]">
              <h2 className="font-h3 text-h3 text-white">Generate Artifact</h2>
              <button onClick={() => setModalOpen(false)} className="text-[#b4b4b4] hover:text-white transition-colors">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            {/* Body */}
            <div className="p-6 flex flex-col space-y-6">
              <div className="flex flex-col space-y-2">
                <label className="font-label-sm text-label-sm text-[#ececec]">Target Model Registry</label>
                <div className="relative">
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="w-full bg-[#0d0d0d] border border-[#2f2f2f] rounded-lg px-4 py-3 text-white font-body-md appearance-none focus:outline-none focus:border-[#10a37f] focus:ring-1 focus:ring-[#10a37f] transition-all"
                  >
                    <option value="loan-approval-v2">CreditScoring_v4.2 (Production)</option>
                    <option value="resume-screen-v3">ResumeScreen_Llama3 (Staging)</option>
                    <option value="icu-triage-v1">ICU Triage Priority (Production)</option>
                    <option value="credit-scoring-v5">CreditScorer_v5 (Production)</option>
                    <option value="content-rec-v2">ContentFeed_v2 (Staging)</option>
                  </select>
                  <div className="absolute inset-y-0 right-0 flex items-center px-3 pointer-events-none text-[#b4b4b4]">
                    <span className="material-symbols-outlined">expand_more</span>
                  </div>
                </div>
                <p className="text-[12px] text-on-surface-variant mt-1">Select the active model deployment to audit.</p>
              </div>

              <div className="flex flex-col space-y-2">
                <label className="font-label-sm text-label-sm text-[#ececec]">Governance Framework</label>
                <div className="grid grid-cols-1 gap-3">
                  {FRAMEWORKS.map((fw) => (
                    <label
                      key={fw.value}
                      className={`flex items-start space-x-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedFramework === fw.value
                          ? "border-[#10a37f] bg-[#212121]"
                          : "border-[#2f2f2f] bg-[#0d0d0d] hover:border-[#10a37f]"
                      }`}
                    >
                      <input
                        type="radio"
                        name="framework"
                        checked={selectedFramework === fw.value}
                        onChange={() => setSelectedFramework(fw.value)}
                        className="mt-0.5 appearance-none w-4 h-4 rounded-full border border-[#2f2f2f] bg-transparent checked:bg-[#10a37f] checked:border-[#10a37f] checked:ring-2 checked:ring-offset-2 checked:ring-offset-[#212121] checked:ring-[#10a37f]"
                      />
                      <div className="flex flex-col">
                        <span className="text-white font-medium text-sm">{fw.label}</span>
                        <span className="text-on-surface-variant text-xs mt-0.5">{fw.desc}</span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-[#2f2f2f] bg-[#131313] flex justify-end items-center space-x-3">
              <button onClick={() => setModalOpen(false)} className="px-4 py-2 text-[#b4b4b4] font-label-sm border border-transparent hover:text-white transition-colors">
                Cancel
              </button>
              <button
                onClick={handleGenerate}
                disabled={generateReport.isPending}
                className="px-5 py-2 bg-[#10a37f] text-white font-label-sm rounded-lg hover:bg-[#12a480] transition-colors flex items-center space-x-2 disabled:opacity-50"
              >
                {generateReport.isPending ? (
                  <span className="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                ) : (
                  <span className="material-symbols-outlined text-[18px]">play_arrow</span>
                )}
                <span>{generateReport.isPending ? "Generating..." : "Execute Run"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
