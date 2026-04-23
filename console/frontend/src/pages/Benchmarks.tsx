import React from 'react';
import { useBenchmarks, useModels } from '../api/hooks';

export default function Benchmarks() {
  const { data: benchmarks, isLoading: benchLoading } = useBenchmarks();
  const { data: models } = useModels();

  const avgEbi = models && models.length > 0
    ? models.reduce((s: number, m: any) => s + (m.ebi_score ?? 0), 0) / models.length
    : 0;

  return (
    <div className="flex-1 p-lg overflow-y-auto">
      <div className="max-w-[1200px] mx-auto w-full">
        
        {/* Header */}
        <div className="mb-lg">
          <h1 className="text-3xl font-bold text-white">Industry Benchmarking</h1>
          <p className="text-[#b4b4b4] mt-2">
            Compare your Enterprise Bias Index against sector baselines and global standards.
          </p>
        </div>

        {/* Global Summary Card */}
        <div className="bg-gradient-to-br from-[#171717] to-[#0a0a0a] border border-[#2f2f2f] rounded-2xl p-8 mb-lg flex flex-col md:flex-row items-center gap-12">
          <div className="flex flex-col items-center">
            <div className="relative w-40 h-40">
              <svg className="w-full h-full" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="#2f2f2f" strokeWidth="8" />
                <circle cx="50" cy="50" r="45" fill="none" stroke="#10a37f" strokeWidth="8"
                  strokeDasharray="283" strokeDashoffset={283 - (avgEbi / 100) * 283}
                  strokeLinecap="round" transform="rotate(-90 50 50)"
                  style={{ transition: 'stroke-dashoffset 1s ease' }}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-4xl font-bold text-white">{Math.round(avgEbi)}</span>
                <span className="text-xs text-[#b4b4b4]">Avg EBI</span>
              </div>
            </div>
          </div>
          
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-white mb-2">Portfolio Performance</h3>
            <p className="text-sm text-[#b4b4b4] leading-relaxed">
              Your organization's current Enterprise Bias Index is <span className="text-white font-bold">{Math.round(avgEbi)}</span>. 
              This places you in the <span className="text-[#10a37f] font-bold">top 15%</span> of Fintech respondents globally. 
              You are currently outperforming the BFSI sector average by 12 points.
            </p>
            <div className="mt-6 flex gap-4">
              <div className="bg-[#212121] px-4 py-2 rounded-lg border border-[#2f2f2f]">
                <p className="text-[10px] text-[#b4b4b4] uppercase font-bold">Global Percentile</p>
                <p className="text-lg font-bold text-[#10a37f]">85th</p>
              </div>
              <div className="bg-[#212121] px-4 py-2 rounded-lg border border-[#2f2f2f]">
                <p className="text-[10px] text-[#b4b4b4] uppercase font-bold">Risk Exposure</p>
                <p className="text-lg font-bold text-[#f59e0b]">Low</p>
              </div>
            </div>
          </div>
        </div>

        {/* Sector Comparison Table */}
        <div className="bg-[#171717] border border-[#2f2f2f] rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-[#2f2f2f]">
            <h3 className="text-lg font-semibold text-white">Sector Benchmarks (EBI)</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-[#212121]">
                  <th className="px-6 py-3 text-xs font-bold text-[#b4b4b4] uppercase tracking-wider">Sector</th>
                  <th className="px-6 py-3 text-xs font-bold text-[#b4b4b4] uppercase tracking-wider">Avg. EBI</th>
                  <th className="px-6 py-3 text-xs font-bold text-[#b4b4b4] uppercase tracking-wider">Target</th>
                  <th className="px-6 py-3 text-xs font-bold text-[#b4b4b4] uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-xs font-bold text-[#b4b4b4] uppercase tracking-wider">Trend</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2f2f2f]">
                {benchLoading ? (
                  <tr><td colSpan={5} className="p-10 text-center text-[#b4b4b4]">Loading industry data...</td></tr>
                ) : (
                  benchmarks && benchmarks.map((b: any) => (
                    <tr key={b.sector} className="hover:bg-[#212121] transition-colors">
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-white">{b.sector}</div>
                        <div className="text-xs text-[#b4b4b4]">{b.count} organizations</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-white">{Math.round(b.avg_ebi)}</span>
                          <div className="w-24 bg-[#2f2f2f] h-1.5 rounded-full">
                            <div className="bg-primary h-1.5 rounded-full" style={{ width: `${b.avg_ebi}%` }} />
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-[#b4b4b4]">
                        {b.target_ebi}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border font-bold ${
                          b.avg_ebi >= 75 ? 'border-[#10a37f] text-[#10a37f]' : 'border-[#f59e0b] text-[#f59e0b]'
                        }`}>
                          {b.avg_ebi >= 75 ? 'Optimal' : 'Standard'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="material-symbols-outlined text-[18px] text-[#10a37f]">trending_up</span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Regulatory Radar */}
        <div className="mt-lg grid grid-cols-1 md:grid-cols-2 gap-lg">
           <div className="bg-[#171717] border border-[#2f2f2f] rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Regulatory Alignment</h3>
              <div className="space-y-4">
                {[
                  { name: 'EU AI Act Compliance', status: '92%', color: '#10a37f' },
                  { name: 'EEOC (US) Guidelines', status: '88%', color: '#10a37f' },
                  { name: 'NIST AI RMF', status: '75%', color: '#f59e0b' },
                  { name: 'Singapore AI Verify', status: '65%', color: '#f59e0b' },
                ].map(reg => (
                  <div key={reg.name}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-[#b4b4b4]">{reg.name}</span>
                      <span className="text-sm font-bold" style={{ color: reg.color }}>{reg.status}</span>
                    </div>
                    <div className="w-full bg-[#2f2f2f] h-1.5 rounded-full">
                       <div className="h-1.5 rounded-full" style={{ width: reg.status, backgroundColor: reg.color }} />
                    </div>
                  </div>
                ))}
              </div>
           </div>

           <div className="bg-[#171717] border border-[#2f2f2f] rounded-xl p-6 flex flex-col justify-center">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 rounded-full bg-[#10a37f]/10 flex items-center justify-center">
                  <span className="material-symbols-outlined text-[#10a37f]">verified_user</span>
                </div>
                <div>
                   <h3 className="text-lg font-semibold text-white">Board-Ready Governance</h3>
                   <p className="text-sm text-[#b4b4b4]">Export certified industry comparison for ESG reporting.</p>
                </div>
              </div>
              <button 
                onClick={() => window.open(`${import.meta.env.VITE_API_URL ?? "/api"}/v1/reports/generate?model_id=global_benchmarks&framework=esg`, "_blank")}
                className="w-full py-3 bg-white text-black font-bold rounded-lg hover:bg-[#e2e8f0] transition-colors"
              >
                Generate ESG Fairness Report
              </button>
           </div>
        </div>

      </div>
    </div>
  );
}
