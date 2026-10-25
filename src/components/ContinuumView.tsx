import React, { useState } from 'react';
import { Shield, Lock, FileCode, CheckCircle, AlertOctagon, Layers, ArrowRight } from 'lucide-react';
import { ContinuumManifest } from '../types';

interface ContinuumViewProps {
  manifest: ContinuumManifest;
  onOpenReport: (title: string, data: unknown) => void;
}

export const ContinuumView: React.FC<ContinuumViewProps> = ({ manifest, onOpenReport }) => {
  const [activeTab, setActiveTab] = useState<'invariants' | 'proofs' | 'ownership' | 'truth'>('invariants');

  return (
    <div className="space-y-6 pb-16">
      {/* Top Banner */}
      <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Shield className="w-5 h-5 text-[#66e3c4]" />
              <h2 className="text-lg font-bold text-[#eef3f8]">Capability OS Continuum & Architecture Lock</h2>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#10241b] text-[#66e3c4] border border-[#66e3c4]/30">
                LOCKED: 2026-09-22
              </span>
            </div>
            <p className="text-xs text-[#8d9aaa] leading-relaxed max-w-3xl">
              The accepted proof-and-seal continuum is the Capability OS architecture anchor. RC1 is not accepted and is downstream packaging. CAPPO is the sole consequence authority; GnomLedger / PGL is the evidence domain.
            </p>
          </div>

          <button
            onClick={() => onOpenReport('Veklom Continuum Manifest', manifest)}
            className="self-start sm:self-center px-3.5 py-2 rounded-lg bg-[#10151d] border border-[#26303d] hover:border-[#66e3c4] text-[#66e3c4] text-xs font-mono flex items-center gap-2 cursor-pointer transition-colors"
          >
            <FileCode className="w-4 h-4" />
            Inspect Full Manifest JSON →
          </button>
        </div>

        {/* Infrastructure Boundary Notice */}
        <div className="mt-4 p-3 bg-[#0e131b] rounded-lg border border-[#26303d] text-xs font-mono flex flex-wrap items-center gap-3">
          <span className="text-[#66e3c4] font-bold">Current Core V1 Infrastructure Lock:</span>
          <span className="text-[#eef3f8]">Owned/Local Hardware + Docker + Cloudflare Tunnels</span>
          <span className="text-[#ff8e8e]">(Coolify, Hetzner, Vercel, and legacy Control Plane are strictly retired)</span>
        </div>
      </div>

      {/* Sub-tabs */}
      <div className="flex items-center gap-2 border-b border-[#26303d] pb-2 font-mono text-xs">
        <button
          onClick={() => setActiveTab('invariants')}
          className={`px-3 py-1.5 rounded-lg cursor-pointer transition-colors ${
            activeTab === 'invariants'
              ? 'bg-[#151c27] text-[#66e3c4] border border-[#26303d]'
              : 'text-[#8d9aaa] hover:text-[#eef3f8]'
          }`}
        >
          Hard Invariants ({manifest.hard_invariants.length})
        </button>
        <button
          onClick={() => setActiveTab('proofs')}
          className={`px-3 py-1.5 rounded-lg cursor-pointer transition-colors ${
            activeTab === 'proofs'
              ? 'bg-[#151c27] text-[#66e3c4] border border-[#26303d]'
              : 'text-[#8d9aaa] hover:text-[#eef3f8]'
          }`}
        >
          Accepted Proof Programs ({manifest.proof_programs.length})
        </button>
        <button
          onClick={() => setActiveTab('truth')}
          className={`px-3 py-1.5 rounded-lg cursor-pointer transition-colors ${
            activeTab === 'truth'
              ? 'bg-[#151c27] text-[#66e3c4] border border-[#26303d]'
              : 'text-[#8d9aaa] hover:text-[#eef3f8]'
          }`}
        >
          Truth Hierarchy Policy
        </button>
        <button
          onClick={() => setActiveTab('ownership')}
          className={`px-3 py-1.5 rounded-lg cursor-pointer transition-colors ${
            activeTab === 'ownership'
              ? 'bg-[#151c27] text-[#66e3c4] border border-[#26303d]'
              : 'text-[#8d9aaa] hover:text-[#eef3f8]'
          }`}
        >
          Subsystem Ownership
        </button>
      </div>

      {/* Invariants Tab */}
      {activeTab === 'invariants' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {manifest.hard_invariants.map((inv) => (
            <div
              key={inv.id}
              className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 shadow-sm space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-[#66e3c4]">{inv.id}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#10241b] text-[#66e3c4] border border-[#66e3c4]/30">
                  Hard Gate
                </span>
              </div>
              <div className="p-3 bg-[#0b0e13] rounded-lg border border-[#26303d] font-mono text-xs text-[#ffca6b]">
                {inv.expression}
              </div>
              <p className="text-xs text-[#8d9aaa] leading-relaxed">
                {inv.implementation_rule}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Proof Programs Tab */}
      {activeTab === 'proofs' && (
        <div className="space-y-4">
          {manifest.proof_programs.map((prog) => (
            <div
              key={prog.program_id}
              className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 shadow-sm space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#26303d]">
                <div>
                  <h4 className="text-base font-bold text-[#eef3f8] font-mono">{prog.program_id}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[11px] font-mono text-[#66e3c4] bg-[#10241b] px-2 py-0.5 rounded border border-[#66e3c4]/30">
                      {prog.acceptance}
                    </span>
                    <span className="text-[11px] font-mono text-[#8d9aaa]">
                      Class: {prog.proof_classification}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <span className="text-xs font-mono uppercase text-[#8d9aaa] block mb-1">Claim Scope:</span>
                <p className="text-xs text-[#eef3f8] bg-[#0e131b] p-3 rounded-lg border border-[#26303d] leading-relaxed">
                  {prog.claim_scope}
                </p>
              </div>

              <div>
                <span className="text-xs font-mono uppercase text-[#66e3c4] block mb-1">Establishes:</span>
                <ul className="space-y-1 text-xs text-[#8d9aaa]">
                  {prog.establishes.map((est, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <CheckCircle className="w-3.5 h-3.5 text-[#66e3c4] shrink-0 mt-0.5" />
                      <span>{est}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <span className="text-xs font-mono uppercase text-[#ff8e8e] block mb-1">Tested Boundaries:</span>
                <ul className="space-y-1 text-xs text-[#8d9aaa]">
                  {prog.boundaries.map((bound, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <AlertOctagon className="w-3.5 h-3.5 text-[#ff8e8e] shrink-0 mt-0.5" />
                      <span>{bound}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Truth Hierarchy Policy Tab */}
      {activeTab === 'truth' && (
        <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-6 shadow-sm space-y-4 max-w-3xl">
          <div className="flex items-center justify-between pb-3 border-b border-[#26303d]">
            <h3 className="text-base font-bold text-[#eef3f8]">Veklom Truth Hierarchy Order</h3>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#321816] text-[#ff8e8e] border border-[#ff8e8e]/30">
              no_synthetic_promotion: true
            </span>
          </div>
          <p className="text-xs text-[#8d9aaa] leading-relaxed">
            In any dispute between claims, source state, or model prose, the hierarchy orders evidence strictly. A lower tier can never overrule a higher tier.
          </p>

          <ol className="space-y-2.5 font-mono text-xs">
            {manifest.truth_policy.order.map((item, idx) => (
              <li
                key={idx}
                className="p-3 bg-[#0e131b] border border-[#26303d] rounded-lg text-[#eef3f8] flex items-center justify-between"
              >
                <span>{item}</span>
                <span className="text-[#66e3c4] text-[10px] font-bold">Tier {idx + 1}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Subsystem Ownership Tab */}
      {activeTab === 'ownership' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(manifest.ownership).map(([key, val]) => (
            <div
              key={key}
              className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-4 shadow-sm"
            >
              <span className="text-xs font-mono uppercase text-[#8d9aaa] block mb-1">
                {key.replace(/_/g, ' ')}
              </span>
              <div className="text-sm font-semibold text-[#eef3f8] font-mono break-words">
                {typeof val === 'string'
                  ? val
                  : Array.isArray(val)
                  ? val.join(', ')
                  : JSON.stringify(val)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
