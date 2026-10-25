import React, { useState } from 'react';
import {
  ShieldAlert,
  Send,
  Server,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  ExternalLink,
  Lock,
  ArrowRight,
  Database,
  Radio,
  FileText,
} from 'lucide-react';
import {
  Capability,
  CoreBackendService,
  SecurityPosture,
  Department,
  ToolboxMeeting,
  CommandMessage,
  GateApprovalRequest,
} from '../types';

interface CockpitViewProps {
  branch: string;
  commit: string;
  isDirty: boolean;
  activeMission: ToolboxMeeting;
  allMissions: ToolboxMeeting[];
  onSelectMission: (mission: ToolboxMeeting) => void;
  coreBackend4: CoreBackendService[];
  capabilities: Capability[];
  security: SecurityPosture;
  departments: Department[];
  messages: CommandMessage[];
  onSendMessage: (text: string, risk: 'low' | 'medium' | 'high' | 'critical', requiresApproval: boolean) => void;
  onOpenReport: (title: string, data: unknown) => void;
  onInitiateGateApproval: (req: GateApprovalRequest) => void;
}

export const CockpitView: React.FC<CockpitViewProps> = ({
  branch,
  commit,
  isDirty,
  activeMission,
  allMissions,
  onSelectMission,
  coreBackend4,
  capabilities,
  security,
  departments,
  messages,
  onSendMessage,
  onOpenReport,
  onInitiateGateApproval,
}) => {
  const [instructionText, setInstructionText] = useState('');
  const [instructionRisk, setInstructionRisk] = useState<'low' | 'medium' | 'high' | 'critical'>('medium');
  const [requiresApproval, setRequiresApproval] = useState(true);
  const [sendResult, setSendResult] = useState<string | null>(null);

  const handleQueueInstruction = (e: React.FormEvent) => {
    e.preventDefault();
    if (!instructionText.trim()) return;

    onSendMessage(instructionText.trim(), instructionRisk, requiresApproval);
    setSendResult('Instruction queued in reports/command-desk-inbox.jsonl');
    setInstructionText('');

    setTimeout(() => {
      setSendResult(null);
    }, 4500);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'reported':
      case 'aligned':
        return <span className="text-[#66e3c4] font-medium text-xs">aligned / reported</span>;
      case 'needs_clarification':
        return <span className="text-[#ffca6b] font-medium text-xs">needs clarification</span>;
      case 'awaiting_response':
        return <span className="text-[#8d9aaa] text-xs">awaiting response</span>;
      default:
        return <span className="text-[#ff8e8e] text-xs">{status}</span>;
    }
  };

  return (
    <div className="space-y-7 pb-16">
      {/* 1. Source Truth vs Production Truth */}
      <section className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-md backdrop-blur-sm">
        <div className="flex items-center justify-between pb-3 border-b border-[#26303d]/70 mb-4">
          <h2 className="text-sm uppercase font-mono tracking-wider font-semibold text-[#66e3c4] flex items-center gap-2">
            <Radio className="w-4 h-4 text-[#66e3c4] animate-pulse" />
            Source Truth vs Production Truth
          </h2>
          <span className="text-xs font-mono text-[#8d9aaa] bg-[#0b0e13] px-2.5 py-1 rounded border border-[#26303d]">
            CURRENT_ARCHITECTURE_LOCK: active
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 rounded-lg bg-[#0e131b] border border-[#26303d]/80">
            <div className="flex items-center justify-between mb-2">
              <strong className="text-sm font-semibold text-[#eef3f8]">GitHub Source Truth</strong>
              <span className="text-xs px-2 py-0.5 rounded bg-[#66e3c4]/10 text-[#66e3c4] border border-[#66e3c4]/30">
                Tier-0 Anchor
              </span>
            </div>
            <div className="text-xs font-mono text-[#8d9aaa] space-y-1.5">
              <p>Repository: <span className="text-[#eef3f8]">reprewindai-dev/veklom-ops-command</span></p>
              <p>Branch: <span className="text-[#eef3f8]">{branch}</span></p>
              <p>Commit: <span className="text-[#66e3c4]">{commit}</span></p>
              <p>
                Working tree: <span className={isDirty ? 'text-[#ffca6b]' : 'text-[#66e3c4]'}>{isDirty ? 'dirty (uncommitted changes)' : 'clean'}</span>
              </p>
              <p className="text-[11px] text-[#8d9aaa] pt-1">
                Poltergeist watching local working tree with zero unauthorized mutations allowed.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-lg bg-[#0e131b] border border-[#26303d]/80">
            <div className="flex items-center justify-between mb-2">
              <strong className="text-sm font-semibold text-[#eef3f8]">Production Truth</strong>
              <span className="text-xs px-2 py-0.5 rounded bg-[#ffca6b]/10 text-[#ffca6b] border border-[#ffca6b]/30">
                Zero Synthetic Promotion
              </span>
            </div>
            <p className="text-xs text-[#8d9aaa] leading-relaxed mb-2">
              No production claim is made by this panel. Runtime proof must come from fresh observation of the owned Docker hosts and live HTTPS checks.
            </p>
            <div className="text-xs font-mono">
              <div className="p-2 rounded bg-[#2e2410]/50 border border-[#ffca6b]/30 text-[#ffca6b] flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>Deployment: not evaluated by this local panel. Coolify, Hetzner, and Vercel are strictly retired.</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Active Toolbox Meeting */}
      <section className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-md backdrop-blur-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#26303d]/70 mb-4">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#66e3c4] animate-ping"></span>
            <h2 className="text-base font-bold text-[#eef3f8]">
              Active Toolbox Meeting · <span className="font-mono text-[#66e3c4]">{activeMission.mission_id}</span>
            </h2>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#10151d] border border-[#26303d] text-[#ffca6b] font-mono">
              {activeMission.status}
            </span>
          </div>

          {/* Quick Mission Selector */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-[#8d9aaa] font-mono whitespace-nowrap">Switch Meeting:</label>
            <select
              value={activeMission.mission_id}
              onChange={(e) => {
                const found = allMissions.find((m) => m.mission_id === e.target.value);
                if (found) onSelectMission(found);
              }}
              className="text-xs font-mono bg-[#0d1219] text-[#eef3f8] border border-[#26303d] rounded-lg px-2.5 py-1.5 focus:border-[#66e3c4] focus:outline-none"
            >
              {allMissions.map((m) => (
                <option key={m.mission_id} value={m.mission_id}>
                  {m.mission_id} ({m.title.slice(0, 30)}...)
                </option>
              ))}
            </select>
            <button
              onClick={() => onOpenReport(`${activeMission.mission_id} Toolbox Meeting Spec`, activeMission)}
              className="text-xs text-[#66e3c4] hover:underline flex items-center gap-1 font-mono whitespace-nowrap px-2 py-1 bg-[#10151d] rounded border border-[#26303d]"
            >
              <FileText className="w-3.5 h-3.5" />
              Raw JSON →
            </button>
          </div>
        </div>

        <div className="text-sm font-medium text-[#eef3f8] mb-1">{activeMission.title}</div>
        <div className="text-xs text-[#8d9aaa] mb-4 leading-relaxed font-mono">
          {activeMission.primary_objective || activeMission.instructions || activeMission.intent || 'No objective text recorded.'}
        </div>

        {/* Supporting Departments Pills */}
        <div className="flex flex-wrap gap-2 mb-4">
          {activeMission.responses?.map((r) => (
            <span
              key={r.department}
              className={`text-xs font-mono px-2.5 py-1 rounded-full border ${
                r.status === 'reported' || r.report?.status === 'aligned'
                  ? 'bg-[#10151d] border-[#66e3c4]/40 text-[#66e3c4]'
                  : 'bg-[#2e2410]/60 border-[#ffca6b]/40 text-[#ffca6b]'
              }`}
            >
              {r.department}: {r.status}
            </span>
          ))}
        </div>

        {/* Responses Table */}
        <div className="overflow-x-auto rounded-lg border border-[#26303d]">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-[#0e131b] text-[#8d9aaa] border-b border-[#26303d] font-mono">
                <th className="py-2.5 px-3">Department</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Mission Understanding</th>
                <th className="py-2.5 px-3">Handoff To</th>
                <th className="py-2.5 px-3 text-right">Report</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#26303d]/60 bg-[#121720]">
              {activeMission.responses?.map((r) => (
                <tr key={r.department} className="hover:bg-[#17202c]/50 transition-colors">
                  <td className="py-2.5 px-3 font-semibold text-[#eef3f8]">{r.department}</td>
                  <td className="py-2.5 px-3">{getStatusBadge(r.report?.status || r.status)}</td>
                  <td className="py-2.5 px-3 text-[#8d9aaa] max-w-md truncate">
                    {r.report?.mission_understanding || 'Awaiting response from team daemon.'}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-[#8d9aaa]">{r.report?.handoff_to || '—'}</td>
                  <td className="py-2.5 px-3 text-right">
                    <button
                      onClick={() => onOpenReport(`${r.department} report`, r.report || { status: 'awaiting_response' })}
                      className="text-[#66e3c4] hover:underline font-mono inline-flex items-center gap-1 cursor-pointer"
                    >
                      Open →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 3. Send Instruction to Command Desk */}
      <section className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-md backdrop-blur-sm">
        <div className="mb-3">
          <h2 className="text-base font-bold text-[#eef3f8]">Send an instruction to Command Desk</h2>
          <p className="text-xs text-[#8d9aaa] mt-0.5">
            Messages are queued in <code className="bg-[#0d1219] px-1 py-0.5 rounded text-[#c8f6e9]">reports/command-desk-inbox.jsonl</code>. Production-impacting work remains approval-gated by Veklom Gate.
          </p>
        </div>

        <form onSubmit={handleQueueInstruction} className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-[1fr_200px] gap-3">
            <textarea
              value={instructionText}
              onChange={(e) => setInstructionText(e.target.value)}
              placeholder="Example: inspect Core Backend 4 for protocol drift. Do not deploy or modify production."
              rows={3}
              className="w-full font-mono text-xs sm:text-sm bg-[#0d1219] text-[#eef3f8] border border-[#26303d] rounded-lg p-3 placeholder-[#8d9aaa]/50 focus:border-[#66e3c4] focus:outline-none transition-colors"
            />
            <div className="space-y-3 flex flex-col justify-between">
              <div>
                <label className="block text-xs font-mono text-[#8d9aaa] mb-1">Risk Tier:</label>
                <select
                  value={instructionRisk}
                  onChange={(e) => setInstructionRisk(e.target.value as 'low' | 'medium' | 'high' | 'critical')}
                  className="w-full font-mono text-xs bg-[#0d1219] text-[#eef3f8] border border-[#26303d] rounded-lg p-2.5 focus:border-[#66e3c4] focus:outline-none cursor-pointer"
                >
                  <option value="low">Low risk (Read-only / Safe)</option>
                  <option value="medium">Medium risk (Governance)</option>
                  <option value="high">High risk (External/Approval)</option>
                  <option value="critical">Critical (Full Gate Sign)</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="approval-gate"
                  checked={requiresApproval}
                  onChange={(e) => setRequiresApproval(e.target.checked)}
                  className="rounded border-[#26303d] bg-[#0d1219] text-[#66e3c4] focus:ring-0 cursor-pointer"
                />
                <label htmlFor="approval-gate" className="text-xs font-mono text-[#8d9aaa] cursor-pointer">
                  Requires Gate Approval
                </label>
              </div>

              <button
                type="submit"
                disabled={!instructionText.trim()}
                className="w-full bg-[#66e3c4] hover:bg-[#78e0b4] disabled:opacity-50 disabled:cursor-not-allowed text-[#07120f] font-bold text-xs py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-all cursor-pointer shadow-sm"
              >
                <Send className="w-4 h-4" />
                Queue instruction
              </button>
            </div>
          </div>

          {sendResult && (
            <div className="p-3 bg-[#10241b] border border-[#66e3c4]/40 text-[#66e3c4] rounded-lg text-xs font-mono flex items-center gap-2 animate-fade-in">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{sendResult}</span>
            </div>
          )}
        </form>
      </section>

      {/* 4. Core Backend 4 */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-base font-bold text-[#eef3f8] flex items-center gap-2">
              <Server className="w-4 h-4 text-[#66e3c4]" />
              Core Backend 4
            </h2>
            <p className="text-xs text-[#8d9aaa]">
              Tier-0 backends governed by Veklom Ops Command. Strictest gates apply.
            </p>
          </div>
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#10151d] border border-[#26303d] text-[#66e3c4]">
            4 Services Active
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {coreBackend4.map((service) => (
            <article
              key={service.repo}
              className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-4 shadow-sm flex flex-col justify-between hover:border-[#66e3c4]/40 transition-colors"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <h3 className="text-sm font-bold text-[#eef3f8] font-mono break-all">
                    {service.repo.split('/').at(-1)}
                  </h3>
                  {service.canonical_port && (
                    <span className="text-[10px] font-mono bg-[#0e131b] px-2 py-0.5 rounded border border-[#26303d] text-[#66e3c4]">
                      :{service.canonical_port}
                    </span>
                  )}
                </div>

                <div className="text-[11px] text-[#8d9aaa] mb-3">
                  Owner: <span className="text-[#eef3f8]">{service.owner_departments.join(', ')}</span>
                </div>

                <div className="text-xs font-mono space-y-1 text-[#8d9aaa] bg-[#0e131b] p-2.5 rounded-lg border border-[#26303d]/60 mb-3">
                  <div className="flex justify-between">
                    <span>Protocol:</span>
                    <span className="text-[#eef3f8] truncate max-w-[120px]">{service.protocol}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Health:</span>
                    <span className="text-[#66e3c4]">{service.health}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Risk:</span>
                    <span className="text-[#ffca6b]">{service.risk}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Target:</span>
                    <span className="text-[#eef3f8] truncate max-w-[120px]">{service.deployment}</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-[#26303d]/60 flex items-center justify-between text-[10px] text-[#8d9aaa] font-mono">
                <span>Verified: {service.last_verified.slice(0, 10)}</span>
                <button
                  onClick={() =>
                    onInitiateGateApproval({
                      aud: service.repo,
                      tool: 'restart_container',
                      action: 'restart_service',
                      params: { service: service.repo.split('/').at(-1), port: service.canonical_port },
                      params_sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
                      risk_tier: 'high',
                      expires_after_seconds: 300,
                      reason: `Emergency restart for ${service.repo.split('/').at(-1)}`,
                    })
                  }
                  className="text-[#66e3c4] hover:underline cursor-pointer"
                >
                  Gate Action →
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* 5. Capability Registry */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-base font-bold text-[#eef3f8]">Capability Registry</h2>
            <p className="text-xs text-[#8d9aaa]">
              Governed operational tools. Actions are granted only within classified risk policies.
            </p>
          </div>
          <span className="text-xs font-mono text-[#8d9aaa] bg-[#121720] px-2.5 py-1 rounded border border-[#26303d]">
            {capabilities.length} Capabilities Recorded
          </span>
        </div>

        <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[#0e131b] text-[#8d9aaa] border-b border-[#26303d] font-mono">
                  <th className="py-3 px-4">Capability & Provider</th>
                  <th className="py-3 px-4">Owner</th>
                  <th className="py-3 px-4">Risk Tier</th>
                  <th className="py-3 px-4 text-center">Approval</th>
                  <th className="py-3 px-4 text-center">Mutation</th>
                  <th className="py-3 px-4 text-center">Evidence</th>
                  <th className="py-3 px-4">Allowed Scope</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#26303d]/60">
                {capabilities.map((c) => (
                  <tr key={c.name} className="hover:bg-[#17202c]/40 transition-colors">
                    <td className="py-3 px-4">
                      <strong className="text-[#eef3f8] block">{c.name}</strong>
                      <span className="text-[#8d9aaa] font-mono text-[11px]">{c.provider}</span>
                    </td>
                    <td className="py-3 px-4 font-mono text-[#8d9aaa]">{c.owner}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-mono uppercase ${
                          c.risk_tier === 'low'
                            ? 'bg-[#10241b] text-[#66e3c4] border border-[#66e3c4]/30'
                            : c.risk_tier === 'medium'
                            ? 'bg-[#2e2410] text-[#ffca6b] border border-[#ffca6b]/30'
                            : 'bg-[#321816] text-[#ff8e8e] border border-[#ff8e8e]/30'
                        }`}
                      >
                        {c.risk_tier}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-mono">
                      {c.approval_required ? (
                        <span className="text-[#ffca6b]">yes</span>
                      ) : (
                        <span className="text-[#8d9aaa]">no</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center font-mono">
                      {c.mutation_allowed ? (
                        <span className="text-[#ff8e8e]">yes</span>
                      ) : (
                        <span className="text-[#66e3c4]">no</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center font-mono">
                      {c.evidence_required ? (
                        <span className="text-[#66e3c4]">yes</span>
                      ) : (
                        <span className="text-[#8d9aaa]">no</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-[#8d9aaa] text-[11px] max-w-xs truncate">
                      {c.allowed_use || 'Governed within repository scope.'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* 6. Security Exposure */}
      <section>
        <div className="mb-3">
          <h2 className="text-base font-bold text-[#eef3f8] flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-[#66e3c4]" />
            Security Exposure & Posture
          </h2>
          <p className="text-xs text-[#8d9aaa]">
            Real-time checks guarding against credential leakage, raw IP exposure, and port drift.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {Object.entries(security).map(([key, value]) => (
            <article
              key={key}
              className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-3.5 shadow-sm"
            >
              <div className="text-xs font-mono text-[#8d9aaa] capitalize mb-1">
                {key.replace(/_/g, ' ')}
              </div>
              <div className="text-xs font-semibold text-[#eef3f8] break-words">
                {value}
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* 7. Departments Grid */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-base font-bold text-[#eef3f8]">The 9 Canonical Departments</h2>
            <p className="text-xs text-[#8d9aaa]">
              Poltergeist-powered autonomous teams watching and protecting the build and runtime boundary.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {departments.map((d) => (
            <article
              key={d.team}
              className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-4 shadow-sm flex flex-col justify-between hover:border-[#66e3c4]/40 transition-colors"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h3 className="text-sm font-bold text-[#eef3f8]">{d.name}</h3>
                  <span className="text-[10px] font-mono text-[#8d9aaa] bg-[#0e131b] px-2 py-0.5 rounded border border-[#26303d]">
                    {d.team}
                  </span>
                </div>
                <div className="text-xs text-[#8d9aaa] mb-3 leading-relaxed">{d.mission}</div>
                <div className="text-xs font-mono text-[#ffca6b] mb-2 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#ffca6b]"></span>
                  {d.targetCount} targets · {d.watcher}
                </div>
                <div className="text-[11px] text-[#8d9aaa] bg-[#0e131b] p-2 rounded-lg border border-[#26303d]/60 mb-3">
                  <span className={d.latestReport?.status === 'aligned' ? 'text-[#66e3c4]' : 'text-[#ffca6b]'}>
                    {d.latestReport ? `${d.latestReport.status} · ` : ''}
                  </span>
                  {d.latestReport?.mission_understanding || 'No department response yet.'}
                </div>
              </div>

              <div className="pt-2 border-t border-[#26303d]/60 flex items-center justify-between">
                <span className="text-[10px] text-[#8d9aaa] font-mono">Captain: {d.captain || 'Assigned'}</span>
                <button
                  onClick={() => onOpenReport(`${d.name} Report`, d.latestReport || { status: 'awaiting_response' })}
                  className="text-xs text-[#66e3c4] hover:underline flex items-center gap-1 font-mono cursor-pointer"
                >
                  Open report →
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* 8. Operator Feed */}
      <section className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-md backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-[#eef3f8] flex items-center gap-2">
            <Radio className="w-4 h-4 text-[#66e3c4]" />
            Operator Feed & Inbox Logs
          </h2>
          <span className="text-xs font-mono text-[#8d9aaa]">
            {messages.length} Instructions Tracked
          </span>
        </div>

        {messages.length === 0 ? (
          <div className="text-xs text-[#8d9aaa] p-4 text-center">
            No new messages in this session.
          </div>
        ) : (
          <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className="border-l-3 border-[#66e3c4] bg-[#0f151d] p-3 rounded-r-lg border-y border-r border-[#26303d]/70 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div>
                  <div className="font-semibold text-[#eef3f8] flex items-center gap-2 mb-1">
                    <span>Queued to Command Desk</span>
                    <span className="text-[10px] font-mono text-[#8d9aaa] bg-[#121720] px-1.5 py-0.2 rounded border border-[#26303d]">
                      #{msg.id.slice(0, 8)}
                    </span>
                  </div>
                  <p className="text-[#c8f6e9] font-mono text-xs">{msg.text}</p>
                  <div className="text-[#8d9aaa] text-[11px] font-mono mt-1 flex items-center gap-3">
                    <span>{new Date(msg.createdAt).toLocaleTimeString()}</span>
                    <span>·</span>
                    <span className="uppercase text-[#ffca6b]">{msg.risk} risk</span>
                    <span>·</span>
                    <span>{msg.requiresApproval ? 'approval required' : 'autonomous'}</span>
                    <span>·</span>
                    <span className="text-[#66e3c4]">Status: {msg.status}</span>
                  </div>
                </div>

                {msg.requiresApproval && msg.status === 'queued' && (
                  <button
                    onClick={() =>
                      onInitiateGateApproval({
                        request_id: msg.id,
                        aud: 'veklom-ops-command',
                        tool: 'dispatch_instruction',
                        action: 'execute_queued_task',
                        params: { messageId: msg.id, instruction: msg.text, risk: msg.risk },
                        params_sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                        risk_tier: msg.risk,
                        expires_after_seconds: 300,
                        reason: msg.text,
                      })
                    }
                    className="shrink-0 px-3 py-1.5 rounded-lg bg-[#2e2410] hover:bg-[#3d3015] border border-[#ffca6b]/40 text-[#ffca6b] text-xs font-mono font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
                  >
                    <Lock className="w-3.5 h-3.5" />
                    Approve in Gate →
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
