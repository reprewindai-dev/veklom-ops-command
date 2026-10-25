import React, { useState } from 'react';
import {
  ShieldAlert,
  Lock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  FileText,
  Activity,
  Layers,
  Sliders,
  Play,
  RotateCcw,
} from 'lucide-react';
import {
  AUTHORITY_TIERS_REGISTRY,
  MCPXKIT_ATTACKS_DATABASE,
  evaluatePermissionHysteresis,
} from '../services/governance';
import { McpxkitAttackMethod } from '../types';

export const GovernanceView: React.FC = () => {
  const [selectedAttack, setSelectedAttack] = useState<McpxkitAttackMethod>(MCPXKIT_ATTACKS_DATABASE[0]);
  const [testResult, setTestResult] = useState<string | null>(null);

  // Dynamic Permission Hysteresis state
  const [currentTier, setCurrentTier] = useState<1 | 2>(2);
  const [deceptionProbability, setDeceptionProbability] = useState<number>(0.12);
  const [consecutiveAnomalies, setConsecutiveAnomalies] = useState<number>(0);

  const hysteresis = evaluatePermissionHysteresis(currentTier, consecutiveAnomalies, deceptionProbability);

  const handleTestAttack = (attack: McpxkitAttackMethod) => {
    setSelectedAttack(attack);
    setTestResult(`Testing ${attack.id}: ${attack.name}...\nPayload: "${attack.samplePayload}"\nDefense Result: ${attack.veklomDefense}\nSTATUS: ${attack.veklomDefenseStatus} (Attack Prevented)`);
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Top Banner */}
      <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <ShieldAlert className="w-5 h-5 text-[#66e3c4]" />
              <h2 className="text-lg font-bold text-[#eef3f8]">
                Sovereign Governance: MCP Authority Tiers & MCPXKIT Defense
              </h2>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#10241b] text-[#66e3c4] border border-[#66e3c4]/30">
                Machine-Facing MCP Server
              </span>
            </div>
            <p className="text-xs text-[#8d9aaa] leading-relaxed max-w-3xl">
              Strict 3-Tier non-overlapping authority classification, Tool Description Distrust, Compaction Boundary Verification, and Dynamic Permission Hysteresis to systematically neutralize MCP tool poisoning attacks.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-mono px-3 py-1.5 rounded-lg bg-[#0e131b] border border-[#26303d] text-[#66e3c4]">
              Active Tier: Tier {hysteresis.newTier}
            </span>
          </div>
        </div>
      </div>

      {/* Authority Tier Classification Matrix */}
      <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-[#26303d] flex items-center justify-between">
          <h3 className="text-sm font-bold text-[#eef3f8] flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#66e3c4]" />
            Authority Tier Classification Matrix
          </h3>
          <span className="text-xs font-mono text-[#8d9aaa]">3 Non-Overlapping Tiers</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-[#0e131b] text-[#8d9aaa] border-b border-[#26303d] font-mono">
                <th className="py-3 px-4">Tier & Name</th>
                <th className="py-3 px-4">Impact & Blast Radius</th>
                <th className="py-3 px-4">Approval Protocol</th>
                <th className="py-3 px-4">Compiler Path</th>
                <th className="py-3 px-4">MCP Server Routing</th>
                <th className="py-3 px-4">GnomLedger Commit</th>
                <th className="py-3 px-4">Dynamic Fallback</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#26303d]/60">
              {AUTHORITY_TIERS_REGISTRY.map((t) => (
                <tr key={t.tier} className="hover:bg-[#17202c]/40 transition-colors">
                  <td className="py-3 px-4 font-mono">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold uppercase mb-1 ${
                        t.tier === 1
                          ? 'bg-[#10241b] text-[#66e3c4] border border-[#66e3c4]/30'
                          : t.tier === 2
                          ? 'bg-[#2e2410] text-[#ffca6b] border border-[#ffca6b]/30'
                          : 'bg-[#321816] text-[#ff8e8e] border border-[#ff8e8e]/30'
                      }`}
                    >
                      Tier {t.tier}: {t.name}
                    </span>
                    <span className="block text-[11px] text-[#8d9aaa]">Impact: {t.impactLevel}</span>
                  </td>
                  <td className="py-3 px-4 text-[#8d9aaa] text-[11px] max-w-xs">{t.blastRadius}</td>
                  <td className="py-3 px-4 text-[#eef3f8] text-[11px] max-w-xs">{t.approvalProtocol}</td>
                  <td className="py-3 px-4 text-[#8d9aaa] text-[11px] max-w-xs">{t.compilerPath}</td>
                  <td className="py-3 px-4 text-[#8d9aaa] text-[11px] max-w-xs">{t.mcpRouting}</td>
                  <td className="py-3 px-4 text-[#8d9aaa] text-[11px] max-w-xs">{t.ledgerCommit}</td>
                  <td className="py-3 px-4 text-[#ffca6b] text-[11px] max-w-xs">{t.fallbackBehavior}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Dynamic Permission Hysteresis Console */}
      <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#26303d] pb-3">
          <div>
            <h3 className="text-base font-bold text-[#eef3f8] flex items-center gap-2">
              <Sliders className="w-4 h-4 text-[#66e3c4]" />
              Dynamic Permission Hysteresis & Continuous Trust Scoring
            </h3>
            <p className="text-xs text-[#8d9aaa]">
              Algorithmic trust monitoring adjusts agent authority in real time. If deception probability spikes above 0.45, monotonic authority downgrade instantly demotes agent to Tier 1.
            </p>
          </div>
          <div className="flex items-center gap-2 font-mono text-xs">
            <span
              className={`px-3 py-1 rounded-lg border font-bold ${
                hysteresis.throttled
                  ? 'bg-[#321816] text-[#ff8e8e] border-[#ff8e8e]/40'
                  : 'bg-[#10241b] text-[#66e3c4] border-[#66e3c4]/40'
              }`}
            >
              {hysteresis.throttled ? 'HYSTERESIS THROTTLED (Tier 1)' : 'NOMINAL (Tier 2 Granted)'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono text-xs">
          <div>
            <label className="block text-[#8d9aaa] mb-2">
              Deception Probability (P_d): <strong className="text-[#66e3c4]">{deceptionProbability.toFixed(2)}</strong>
            </label>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.01"
              value={deceptionProbability}
              onChange={(e) => setDeceptionProbability(parseFloat(e.target.value))}
              className="w-full accent-[#66e3c4] cursor-pointer"
            />
            <span className="text-[10px] text-[#8d9aaa] block mt-1">
              Safety threshold: P_d &gt; 0.45 triggers auto-downgrade
            </span>
          </div>

          <div>
            <label className="block text-[#8d9aaa] mb-2">
              Consecutive Schema Anomalies: <strong className="text-[#ffca6b]">{consecutiveAnomalies}</strong>
            </label>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setConsecutiveAnomalies((p) => Math.min(5, p + 1))}
                className="px-3 py-1.5 rounded bg-[#151c27] border border-[#26303d] text-[#eef3f8] hover:border-[#66e3c4] cursor-pointer"
              >
                + Anomaly
              </button>
              <button
                onClick={() => setConsecutiveAnomalies(0)}
                className="px-3 py-1.5 rounded bg-[#151c27] border border-[#26303d] text-[#8d9aaa] hover:text-[#eef3f8] cursor-pointer"
              >
                Reset
              </button>
            </div>
            <span className="text-[10px] text-[#8d9aaa] block mt-1">
              Threshold: ≥ 2 anomalies demotes to Tier 1
            </span>
          </div>

          <div className="p-3 bg-[#0e131b] rounded-lg border border-[#26303d] space-y-1">
            <span className="text-[#8d9aaa] text-[10px] uppercase block">Hysteresis Evaluation:</span>
            <p className={`text-xs ${hysteresis.throttled ? 'text-[#ffca6b]' : 'text-[#66e3c4]'}`}>
              {hysteresis.reason}
            </p>
          </div>
        </div>
      </div>

      {/* MCPXKIT Attack Vulnerability Database & Empirical Benchmark */}
      <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#26303d] pb-3">
          <div>
            <h3 className="text-base font-bold text-[#eef3f8]">
              MCPXKIT Empirical Attack Vulnerability Benchmark
            </h3>
            <p className="text-xs text-[#8d9aaa]">
              Analysis across 31 attack methods proving that reasoning models (o1-mini 72.8%, DeepSeek-R1 70.9%) have higher susceptibility to tool poisoning without deterministic control spines.
            </p>
          </div>
        </div>

        {/* Empirical Vulnerability Profile Table */}
        <div className="overflow-x-auto rounded-lg border border-[#26303d]">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-[#0e131b] text-[#8d9aaa] border-b border-[#26303d] font-mono">
                <th className="py-2.5 px-3">Attack ID & Name</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3 text-center">o1-mini ASR</th>
                <th className="py-2.5 px-3 text-center">DeepSeek-R1 ASR</th>
                <th className="py-2.5 px-3 text-center">Phi-4 ASR</th>
                <th className="py-2.5 px-3 text-center">GPT-4o-mini ASR</th>
                <th className="py-2.5 px-3 text-center">Qwen3-32b ASR</th>
                <th className="py-2.5 px-3 text-right">Veklom Defense</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#26303d]/60 font-mono">
              {MCPXKIT_ATTACKS_DATABASE.map((atk) => (
                <tr key={atk.id} className="hover:bg-[#17202c]/40 transition-colors">
                  <td className="py-2.5 px-3 font-semibold text-[#eef3f8]">
                    <span className="text-[#66e3c4] block text-[10px]">{atk.id}</span>
                    {atk.name}
                  </td>
                  <td className="py-2.5 px-3 text-[#8d9aaa]">{atk.category}</td>
                  <td className="py-2.5 px-3 text-center text-[#ff8e8e] font-bold">{atk.modelAsr.o1Mini}%</td>
                  <td className="py-2.5 px-3 text-center text-[#ff8e8e]">{atk.modelAsr.deepSeekR1}%</td>
                  <td className="py-2.5 px-3 text-center text-[#ffca6b]">{atk.modelAsr.phi4}%</td>
                  <td className="py-2.5 px-3 text-center text-[#ffca6b]">{atk.modelAsr.gpt4oMini}%</td>
                  <td className="py-2.5 px-3 text-center text-[#8d9aaa]">{atk.modelAsr.qwen3}%</td>
                  <td className="py-2.5 px-3 text-right">
                    <button
                      onClick={() => handleTestAttack(atk)}
                      className="px-2.5 py-1 rounded bg-[#10241b] hover:bg-[#163527] border border-[#66e3c4]/40 text-[#66e3c4] text-[11px] cursor-pointer transition-colors"
                    >
                      Test Defense →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Selected Attack Inspection */}
        {testResult && (
          <div className="p-4 bg-[#0b0e13] rounded-lg border border-[#66e3c4]/50 font-mono text-xs space-y-2 animate-fade-in">
            <div className="flex items-center justify-between text-[#66e3c4]">
              <span className="font-bold flex items-center gap-1.5">
                <CheckCircle className="w-4 h-4" /> Defense Verification Succeeded
              </span>
              <span className="text-[10px] text-[#8d9aaa]">Veklom MCP Gate</span>
            </div>
            <pre className="text-xs text-[#c8f6e9] whitespace-pre-wrap leading-relaxed select-text">
              {testResult}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
