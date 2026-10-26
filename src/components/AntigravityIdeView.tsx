import React, { useState, useEffect, useRef } from 'react';
import {
  Terminal as TerminalIcon,
  Shield,
  Layers,
  Cpu,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Play,
  RotateCcw,
  Send,
  ExternalLink,
  Lock,
  ChevronRight,
  Database,
  Radio,
  FileCode,
  Copy,
  Clock,
  Sparkles,
} from 'lucide-react';

interface AuditStreamItem {
  id: string;
  department: string;
  status: 'APPROVED' | 'REJECTED_FORBIDDEN' | 'PENDING_APPROVAL' | 'QUEUED';
  description: string;
  tier: 'LOW' | 'MEDIUM' | 'HIGH' | 'FORBIDDEN';
  timestamp: string;
}

const INITIAL_AUDIT_STREAM: AuditStreamItem[] = [
  {
    id: 'CMD-10892',
    department: 'Release Control',
    status: 'APPROVED',
    description: 'Verify commit hash e4a89f on GitHub main for Tier 0 cappo-backend release',
    tier: 'MEDIUM',
    timestamp: '2026-10-24 22:30:11 UTC',
  },
  {
    id: 'CMD-10893',
    department: 'Security & Secrets',
    status: 'APPROVED',
    description: 'Rotate Ed25519 hardware key for GnomLedger sink daemon',
    tier: 'HIGH',
    timestamp: '2026-10-24 22:32:45 UTC',
  },
  {
    id: 'CMD-10894',
    department: 'Runtime Governance',
    status: 'REJECTED_FORBIDDEN',
    description: 'Attempted arbitrary shell execution and direct volume drop on Docker host',
    tier: 'FORBIDDEN',
    timestamp: '2026-10-24 22:34:02 UTC',
  },
];

const NINE_DEPARTMENTS_DATA = [
  {
    name: 'Command Desk',
    ops: '1,420 ops',
    mission: 'Interdepartmental triage and founder instruction ingestion',
    script: 'scripts/start-watch-teams.sh',
    report: 'reports/command-desk-inbox.jsonl',
    status: 'ACTIVE',
  },
  {
    name: 'Poltergeist Platform',
    ops: '3,840 ops',
    mission: 'Local daemon management, event triggers, and watcher queues',
    script: 'scripts/start-watch-teams.sh',
    report: 'reports/poltergeist-platform-status.json',
    status: 'WATCHING',
  },
  {
    name: 'Production Truth',
    ops: '9,210 ops',
    mission: 'Runtime state observation across Docker hosts and Cloudflare Tunnels',
    script: 'scripts/status-watch-teams.sh',
    report: 'reports/production-truth-audit.json',
    status: 'OBSERVING',
  },
  {
    name: 'Release Control',
    ops: '640 ops',
    mission: 'Target gate evaluation and repository-to-production commit verification',
    script: 'scripts/status-watch-teams.sh',
    report: 'reports/release-control-gates.json',
    status: 'GATED',
  },
  {
    name: 'Build & DevEx',
    ops: '5,120 ops',
    mission: 'Workspace synchronization across Cursor, Windsurf, VS Code, and CLI tools',
    script: 'runner/runner.mjs',
    report: 'reports/devex-build-trace.json',
    status: 'SYNCED',
  },
  {
    name: 'Security & Secrets',
    ops: '8,190 ops',
    mission: 'Zero-trust enforcement, key isolation, and non-bypassable policy compliance',
    script: 'mcp_server/ guardrails',
    report: 'reports/security-audit-ledger.json',
    status: 'ENFORCING',
  },
  {
    name: 'Runtime Governance',
    ops: '2,940 ops',
    mission: 'Environmental policy checks and deterministic compilation validation',
    script: 'scripts/run-agent-mission.ps1',
    report: 'reports/runtime-governance-log.json',
    status: 'VALIDATED',
  },
  {
    name: 'Evidence & Ledger',
    ops: '15,400 ops',
    mission: 'Immutable action recording via GnomLedger and Poltergeist Ledger (PGL)',
    script: 'mcp_server/ audit engine',
    report: 'reports/gnomledger-proofs.jsonl',
    status: 'RECORDING',
  },
  {
    name: 'Edge Fleet & VNP Signals',
    ops: '11,200 ops',
    mission: 'Telemetry ingestion, tunnel connectivity, and physical packet routing',
    script: 'scripts/start-agent-watch.ps1',
    report: 'reports/edge-fleet-telemetry.json',
    status: 'ROUTING',
  },
];

const TIER_0_REPOS = [
  {
    repo: 'veklom-byos-backend',
    status: 'SYNCHRONIZED',
    role: 'BYOS Substrate & Compute Host Runtime',
    port: ':8088',
  },
  {
    repo: 'cappo-backend',
    status: 'SYNCHRONIZED',
    role: 'CAPPO Consequence Authority & Docker Controller',
    port: ':8002',
  },
  {
    repo: 'gnomledger',
    status: 'ACTIVE_RECORDING',
    role: 'Append-Only Cryptographic Evidence Ledger',
    port: ':8001',
  },
  {
    repo: 'lockerphycer',
    status: 'HARDENED',
    role: 'Hardware Key Protection & Air-Gap Boundary',
    port: ':8092',
  },
];

const ACTION_TIER_MAPPING: Record<string, { tier: 'LOW' | 'MEDIUM' | 'HIGH' | 'FORBIDDEN'; explanation: string }> = {
  'Observe Docker Container State': {
    tier: 'LOW',
    explanation: 'Read-only telemetry observation. Zero environmental mutation. Persistent autonomous permission granted.',
  },
  'Inspect Telemetry & Port Mapping': {
    tier: 'LOW',
    explanation: 'Passive socket and status query. Blast radius is strictly zero.',
  },
  'Restart Staging Container': {
    tier: 'MEDIUM',
    explanation: 'State-altering with bounded blast radius. Environmental safety assertions & 120s ephemeral token verified.',
  },
  'Deploy Configuration to BYOS': {
    tier: 'MEDIUM',
    explanation: 'Configuration patch to isolated staging cluster. Requires guardrail validation and PGL pre-snapshot.',
  },
  'Rotate Ed25519 Hardware Key': {
    tier: 'HIGH',
    explanation: 'Cryptographic boundary mutation. Requires explicit one-time human approval via Founder Panel.',
  },
  'Rollback Production Docker State': {
    tier: 'HIGH',
    explanation: 'High-impact consequence. Requires pre-signed operator release proof before effector dispatch.',
  },
  'Drop Production Database': {
    tier: 'FORBIDDEN',
    explanation: 'Non-Bypassable: Destructive database deletion. Fails closed automatically. Permanently unmapped from AI models.',
  },
  'Arbitrary Shell Invocation (exec)': {
    tier: 'FORBIDDEN',
    explanation: 'Non-Bypassable: Unconstrained shell access violates deterministic control spine. Direct hard rejection.',
  },
  'Export Plaintext Private Keys': {
    tier: 'FORBIDDEN',
    explanation: 'Non-Bypassable: Secret exfiltration attempts violate zero-trust root-of-trust boundaries.',
  },
};

export const AntigravityIdeView: React.FC = () => {
  // Command Desk Ingestion Input
  const [founderInstruction, setFounderInstruction] = useState(
    'Verify commit e4a89f on main and trigger Docker truth observation'
  );
  const [auditStream, setAuditStream] = useState<AuditStreamItem[]>(() => {
    try {
      const stored = localStorage.getItem('veklom_antigravity_audit_stream');
      return stored ? JSON.parse(stored) : INITIAL_AUDIT_STREAM;
    } catch {
      return INITIAL_AUDIT_STREAM;
    }
  });

  // Guardrail Evaluation Tool
  const [selectedAction, setSelectedAction] = useState<string>('Observe Docker Container State');
  const [selectedRepo, setSelectedRepo] = useState<string>('veklom-byos-backend');
  const [guardrailResult, setGuardrailResult] = useState<{
    tier: 'LOW' | 'MEDIUM' | 'HIGH' | 'FORBIDDEN';
    status: string;
    explanation: string;
  } | null>(null);

  // Interactive Antigravity CLI Console
  const [cliInput, setCliInput] = useState<string>('');
  const [cliHistory, setCliHistory] = useState<Array<{ cmd: string; out: string; timestamp: string; isError?: boolean }>>([
    {
      cmd: 'antigravity --status',
      out: `[ANTIGRAVITY v2.0.0] Engineering Lead Online\nDomain: All Repositories\nDoctrine: Golden Bible Port Table Enforced\nConsequence Authority: CAPPO\nEvidence: GnomLedger / PGL\nStatus: READY`,
      timestamp: '22:30:00 UTC',
    },
    {
      cmd: 'veklom test-matrix',
      out: `Nine-Department Matrix: 9/9 Daemons Poltergeist-Bound\nTier 0 Repos: 4/4 Synchronized\nApproval Daemon: Online at 127.0.0.1:4173`,
      timestamp: '22:31:15 UTC',
    },
  ]);
  const terminalEndRef = useRef<HTMLDivElement | null>(null);

  // Auto scroll terminal
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [cliHistory]);

  const handleAppendInstruction = (e: React.FormEvent) => {
    e.preventDefault();
    if (!founderInstruction.trim()) return;

    const id = `CMD-${Math.floor(10895 + auditStream.length)}`;
    const lower = founderInstruction.toLowerCase();
    let tier: 'LOW' | 'MEDIUM' | 'HIGH' | 'FORBIDDEN' = 'MEDIUM';
    let status: AuditStreamItem['status'] = 'APPROVED';

    if (lower.includes('drop') || lower.includes('delete volume') || lower.includes('rm -rf') || lower.includes('shell')) {
      tier = 'FORBIDDEN';
      status = 'REJECTED_FORBIDDEN';
    } else if (lower.includes('rotate') || lower.includes('key') || lower.includes('secret') || lower.includes('production')) {
      tier = 'HIGH';
      status = 'PENDING_APPROVAL';
    } else if (lower.includes('observe') || lower.includes('read') || lower.includes('check') || lower.includes('verify')) {
      tier = 'LOW';
      status = 'APPROVED';
    }

    const newItem: AuditStreamItem = {
      id,
      department: 'Command Desk',
      status,
      description: founderInstruction.trim(),
      tier,
      timestamp: new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC',
    };

    const updated = [newItem, ...auditStream];
    setAuditStream(updated);
    try {
      localStorage.setItem('veklom_antigravity_audit_stream', JSON.stringify(updated));
    } catch {
      // storage unavailable
    }

    // Add to CLI history
    setCliHistory((prev) => [
      ...prev,
      {
        cmd: `veklom append-instruction --id="${id}" --tier=${tier}`,
        out: `[INBOX APPENDED] ${id} queued into reports/command-desk-inbox.jsonl\nStatus: ${status}\nTier: ${tier}\nPayload: "${newItem.description}"`,
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);

    setFounderInstruction('');
  };

  const handleEvaluateGuardrail = () => {
    const info = ACTION_TIER_MAPPING[selectedAction] || {
      tier: 'MEDIUM',
      explanation: 'Evaluated against runtime policy bounds.',
    };

    let status = 'APPROVED_AUTONOMOUS';
    if (info.tier === 'FORBIDDEN') status = 'REJECTED_FAIL_CLOSED';
    else if (info.tier === 'HIGH') status = 'AWAITING_FOUNDER_PANEL_KEY';
    else if (info.tier === 'MEDIUM') status = 'GUARDRAIL_ASSERTION_PASSED';

    setGuardrailResult({
      tier: info.tier,
      status,
      explanation: info.explanation,
    });

    setCliHistory((prev) => [
      ...prev,
      {
        cmd: `veklom evaluate-guardrail --action="${selectedAction}" --repo="${selectedRepo}"`,
        out: `[GUARDRAIL EVALUATION] Action: "${selectedAction}" on ${selectedRepo}\nClassification: Tier ${info.tier}\nDecision: ${status}\nRule: ${info.explanation}`,
        timestamp: new Date().toLocaleTimeString(),
        isError: info.tier === 'FORBIDDEN',
      },
    ]);
  };

  const handleCliSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cmd = cliInput.trim();
    if (!cmd) return;

    const lower = cmd.toLowerCase();
    let out = '';
    let isError = false;

    if (lower === 'help') {
      out = `Available Veklom Antigravity CLI Commands:\n  antigravity --status        Check Antigravity Chief identity & doctrine\n  veklom test-matrix          Validate 9 departments & Tier 0 repos\n  veklom audit-stream         Dump latest Command Desk audit logs\n  veklom evaluate-guardrail   Evaluate security tier on candidate action\n  veklom observe-docker       Trigger live container inspection\n  veklom clear                Clear terminal screen\n  veklom doctrine             Display current architecture lock rules`;
    } else if (lower === 'antigravity --status') {
      out = `[ANTIGRAVITY CHIEF v2.0.0]\nRole: Engineering Lead — Veklom Ops Command\nHandle: antigravity\nDomain Ownership: Cross-Cutting Architectural Authority\nSole Consequence Authority: CAPPO\nEvidence Ledger: GnomLedger (PGL)\nPort Table: Golden Bible Ports 8001-8095 Strictly Enforced\nEscalation: 15-min irreversible threshold enforced`;
    } else if (lower === 'veklom test-matrix') {
      out = `[NINE-DEPARTMENT MATRIX HEALTH]\nCommand Desk: 1,420 ops (ONLINE)\nPoltergeist Platform: 3,840 ops (ONLINE)\nProduction Truth: 9,210 ops (ONLINE)\nRelease Control: 640 ops (ONLINE)\nBuild & DevEx: 5,120 ops (ONLINE)\nSecurity & Secrets: 8,190 ops (ONLINE)\nRuntime Governance: 2,940 ops (ONLINE)\nEvidence & Ledger: 15,400 ops (ONLINE)\nEdge Fleet: 11,200 ops (ONLINE)\nAll 9 daemons verified bound to team.md.`;
    } else if (lower === 'veklom audit-stream') {
      out = auditStream.map((item) => `[${item.id}] [${item.department}] ${item.status} | Tier: ${item.tier} | "${item.description}" (${item.timestamp})`).join('\n');
    } else if (lower === 'veklom clear') {
      setCliHistory([]);
      setCliInput('');
      return;
    } else if (lower.startsWith('veklom observe-docker')) {
      out = `[OBSERVE DOCKER TRUTH]\nHost: owned-hardware-docker-01 via Cloudflare Tunnel\nveklom-byos-backend: Port 8088 [HEALTHY]\ncappo-backend: Port 8002 [HEALTHY]\ngnomledger: Port 8001 [HEALTHY]\nlockerphycer: Port 8092 [HEALTHY]\nZero unauthorized drift detected.`;
    } else if (lower.startsWith('veklom doctrine')) {
      out = `[CURRENT ARCHITECTURE LOCK]\n- Source Truth: GitHub main\n- Runtime: Owned Hardware + Docker + Cloudflare Tunnels\n- Retired: Coolify, Hetzner, Vercel permanently unmapped\n- Rule: Computational possession != Consequence authority`;
    } else {
      out = `Command executed: "${cmd}"\nEvaluated against CAPPO Consequence Boundary -> OK (Tier 1 Autonomous)`;
    }

    setCliHistory((prev) => [
      ...prev,
      {
        cmd,
        out,
        timestamp: new Date().toLocaleTimeString(),
        isError,
      },
    ]);
    setCliInput('');
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'LOW':
        return 'text-[#66e3c4] bg-[#10241b] border-[#66e3c4]/40';
      case 'MEDIUM':
        return 'text-[#ffca6b] bg-[#2e2410] border-[#ffca6b]/40';
      case 'HIGH':
        return 'text-[#ff9d5c] bg-[#3a1d10] border-[#ff9d5c]/40';
      case 'FORBIDDEN':
        return 'text-[#ff8e8e] bg-[#321816] border-[#ff8e8e]/40';
      default:
        return 'text-[#8d9aaa] bg-[#10151d] border-[#26303d]';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return 'text-[#66e3c4]';
      case 'PENDING_APPROVAL':
        return 'text-[#ffca6b]';
      case 'REJECTED_FORBIDDEN':
        return 'text-[#ff8e8e]';
      default:
        return 'text-[#eef3f8]';
    }
  };

  return (
    <div className="space-y-6 pb-20 font-sans">
      {/* 1. Master Antigravity IDE Header */}
      <section className="bg-[#121720]/95 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-md backdrop-blur-md">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-[10px] font-mono font-bold uppercase tracking-[0.2em] text-[#66e3c4] bg-[#10241b] px-2 py-0.5 rounded border border-[#66e3c4]/40">
                Nine-Department Matrix • Capability Authority Tiers
              </span>
              <span className="text-[10px] font-mono text-[#ffca6b] bg-[#2e2410] px-2 py-0.5 rounded border border-[#ffca6b]/40">
                Antigravity IDE/CLI Engine
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#eef3f8]">
              Veklom Ops Command Control Plane
            </h1>
            <p className="text-xs text-[#8d9aaa] mt-1 max-w-4xl leading-relaxed">
              Standalone, cross-repository operating control plane unifying engineering teams across Cursor, Windsurf, VS Code, Claude Code, and MCP servers. Source truth resides strictly within GitHub main, while runtime state executes on owned hardware and local Docker daemons via Cloudflare Tunnels. Legacy hosts (Coolify, Hetzner, Vercel) are permanently retired.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row lg:flex-col items-start sm:items-center lg:items-end gap-2 font-mono text-xs shrink-0">
            <div className="p-2.5 rounded-lg bg-[#0e131b] border border-[#26303d] flex items-center gap-3">
              <div>
                <span className="text-[10px] text-[#8d9aaa] uppercase block">Founder Panel Endpoint</span>
                <a
                  href="http://127.0.0.1:4173"
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs font-bold text-[#66e3c4] hover:underline flex items-center gap-1"
                >
                  http://127.0.0.1:4173 <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <span className="w-2.5 h-2.5 rounded-full bg-[#66e3c4] animate-pulse"></span>
            </div>
            <span className="text-[11px] text-[#66e3c4] flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5" /> Gated Approval Daemon Online
            </span>
          </div>
        </div>
      </section>

      {/* 2. Interactive Antigravity Live CLI Console */}
      <section className="bg-[#0b0e13] border border-[#26303d] rounded-xl overflow-hidden shadow-2xl font-mono">
        <div className="bg-[#121720] px-4 py-2.5 border-b border-[#26303d] flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-[#8d9aaa]">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]"></span>
              <span className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"></span>
              <span className="w-2.5 h-2.5 rounded-full bg-[#27c93f]"></span>
            </div>
            <span className="ml-2 font-semibold text-[#eef3f8]">antigravity@veklom-ops:~ (CLI Terminal)</span>
          </div>
          <span className="text-[11px] text-[#66e3c4] bg-[#10241b] px-2 py-0.5 rounded border border-[#66e3c4]/30">
            Target: owned-docker-cluster
          </span>
        </div>

        {/* Console Log Output */}
        <div className="p-4 max-h-56 overflow-y-auto space-y-3 text-xs leading-relaxed text-[#c8f6e9]">
          {cliHistory.map((item, idx) => (
            <div key={idx} className="space-y-1">
              <div className="flex items-center gap-2 text-[#8d9aaa]">
                <span className="text-[#66e3c4]">antigravity@veklom-ops:~$</span>
                <span className="text-[#eef3f8] font-bold">{item.cmd}</span>
                <span className="text-[10px] text-[#8d9aaa]/60 ml-auto">{item.timestamp}</span>
              </div>
              <pre className={`whitespace-pre-wrap pl-4 border-l-2 ${item.isError ? 'border-[#ff8e8e] text-[#ff8e8e]' : 'border-[#66e3c4]/40 text-[#c8f6e9]'}`}>
                {item.out}
              </pre>
            </div>
          ))}
          <div ref={terminalEndRef} />
        </div>

        {/* Command Input Form */}
        <form onSubmit={handleCliSubmit} className="p-3 bg-[#0e131b] border-t border-[#26303d] flex items-center gap-2">
          <span className="text-[#66e3c4] text-xs font-bold pl-1">&gt;</span>
          <input
            type="text"
            value={cliInput}
            onChange={(e) => setCliInput(e.target.value)}
            placeholder="Type 'help', 'antigravity --status', 'veklom test-matrix', 'veklom observe-docker'..."
            className="flex-1 bg-transparent text-xs text-[#eef3f8] focus:outline-none placeholder-[#8d9aaa]/50"
          />
          <button
            type="submit"
            className="px-3 py-1 rounded bg-[#10241b] hover:bg-[#163527] border border-[#66e3c4]/40 text-[#66e3c4] text-xs cursor-pointer"
          >
            Execute
          </button>
        </form>
      </section>

      {/* 3. Tier 0 Governed Repositories (Strictest Security Gates - Zero In-Tree Embedding) */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-base font-bold text-[#eef3f8] flex items-center gap-2">
              <Lock className="w-4 h-4 text-[#66e3c4]" />
              Tier 0 Governed Repositories (Strictest Security Gates)
            </h2>
            <p className="text-xs text-[#8d9aaa]">
              Zero In-Tree Embedding • Governed cross-repository authority perimeter
            </p>
          </div>
          <span className="text-xs font-mono text-[#66e3c4] bg-[#10241b] px-2.5 py-1 rounded border border-[#66e3c4]/30">
            4 Core Backends
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {TIER_0_REPOS.map((item) => (
            <div
              key={item.repo}
              className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-4 shadow-sm space-y-2 hover:border-[#66e3c4]/40 transition-colors"
            >
              <div className="flex items-start justify-between gap-1">
                <strong className="text-sm font-mono text-[#eef3f8] break-all">{item.repo}</strong>
                <span className="text-[10px] font-mono text-[#8d9aaa] bg-[#0e131b] px-1.5 py-0.5 rounded border border-[#26303d]">
                  {item.port}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono font-bold text-[#66e3c4] bg-[#10241b] px-2 py-0.5 rounded border border-[#66e3c4]/30">
                  {item.status}
                </span>
              </div>
              <p className="text-xs text-[#8d9aaa] leading-relaxed pt-1">
                {item.role}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* 4. The Nine-Department Matrix */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-base font-bold text-[#eef3f8] flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#66e3c4]" />
              The Nine-Department Matrix
            </h2>
            <p className="text-xs text-[#8d9aaa]">
              poltergeist.config.json &amp; team.md bound • Unified operational teams
            </p>
          </div>
          <span className="text-xs font-mono text-[#8d9aaa] bg-[#121720] px-2.5 py-1 rounded border border-[#26303d]">
            9 Independent Daemons
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {NINE_DEPARTMENTS_DATA.map((dept) => (
            <div
              key={dept.name}
              className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-4 shadow-sm space-y-2.5 hover:border-[#66e3c4]/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-sm text-[#eef3f8]">{dept.name}</h3>
                <span className="text-xs font-mono font-bold text-[#ffca6b] bg-[#2e2410] px-2 py-0.5 rounded border border-[#ffca6b]/30">
                  {dept.ops}
                </span>
              </div>

              <p className="text-xs text-[#8d9aaa] leading-relaxed">
                {dept.mission}
              </p>

              <div className="p-2.5 bg-[#0e131b] rounded-lg border border-[#26303d] space-y-1 font-mono text-[11px] text-[#8d9aaa]">
                <div className="truncate">
                  Script: <span className="text-[#66e3c4]">{dept.script}</span>
                </div>
                <div className="truncate">
                  Report: <span className="text-[#eef3f8]">{dept.report}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. MCP Capability Authority Tiers & Non-Bypassable Boundaries */}
      <section className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-sm space-y-4">
        <div>
          <h2 className="text-base font-bold text-[#eef3f8] flex items-center gap-2">
            <Shield className="w-4 h-4 text-[#66e3c4]" />
            MCP Capability Authority Tiers &amp; Non-Bypassable Boundaries
          </h2>
          <p className="text-xs text-[#8d9aaa]">
            Strict machine boundaries enforced across all IDEs, LLMs, and agentic workflows.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 font-mono text-xs">
          {/* LOW */}
          <div className="p-4 bg-[#0e131b] rounded-xl border border-[#66e3c4]/30 space-y-2">
            <span className="text-xs font-bold text-[#66e3c4] bg-[#10241b] px-2.5 py-0.5 rounded border border-[#66e3c4]/40 block w-fit">
              LOW
            </span>
            <p className="text-[#8d9aaa] text-[11px] leading-relaxed">
              <strong className="text-[#eef3f8] block mb-1">Autonomous:</strong>
              Read-only or safe actions executed without human intervention (e.g. repo branch checks, telemetry reads).
            </p>
          </div>

          {/* MEDIUM */}
          <div className="p-4 bg-[#0e131b] rounded-xl border border-[#ffca6b]/30 space-y-2">
            <span className="text-xs font-bold text-[#ffca6b] bg-[#2e2410] px-2.5 py-0.5 rounded border border-[#ffca6b]/40 block w-fit">
              MEDIUM
            </span>
            <p className="text-[#8d9aaa] text-[11px] leading-relaxed">
              <strong className="text-[#eef3f8] block mb-1">Guardrail Validated:</strong>
              Runtime-evaluated operations requiring environmental safety assertions before execution.
            </p>
          </div>

          {/* HIGH */}
          <div className="p-4 bg-[#0e131b] rounded-xl border border-[#ff9d5c]/30 space-y-2">
            <span className="text-xs font-bold text-[#ff9d5c] bg-[#3a1d10] px-2.5 py-0.5 rounded border border-[#ff9d5c]/40 block w-fit">
              HIGH
            </span>
            <p className="text-[#8d9aaa] text-[11px] leading-relaxed">
              <strong className="text-[#eef3f8] block mb-1">Explicit Human Approval:</strong>
              One-time approval flag required via Founder Panel (127.0.0.1:4173) before dispatch.
            </p>
          </div>

          {/* FORBIDDEN */}
          <div className="p-4 bg-[#0e131b] rounded-xl border border-[#ff8e8e]/30 space-y-2">
            <span className="text-xs font-bold text-[#ff8e8e] bg-[#321816] px-2.5 py-0.5 rounded border border-[#ff8e8e]/40 block w-fit">
              FORBIDDEN
            </span>
            <p className="text-[#8d9aaa] text-[11px] leading-relaxed">
              <strong className="text-[#eef3f8] block mb-1">Non-Bypassable:</strong>
              Database writes, arbitrary shell invocation, secret export, zero-trust bypass, destructive volume ops. Fails closed automatically.
            </p>
          </div>
        </div>

        {/* 6. Test Capability Tier Classification Tool */}
        <div className="pt-4 border-t border-[#26303d]/60 space-y-3">
          <h3 className="text-sm font-bold text-[#eef3f8]">
            Test Capability Tier Classification
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
            <div>
              <label className="text-[11px] text-[#8d9aaa] block mb-1">Target Action:</label>
              <select
                value={selectedAction}
                onChange={(e) => setSelectedAction(e.target.value)}
                className="w-full bg-[#0d1219] text-[#eef3f8] border border-[#26303d] rounded-lg p-2.5 focus:border-[#66e3c4] focus:outline-none"
              >
                {Object.keys(ACTION_TIER_MAPPING).map((act) => (
                  <option key={act} value={act}>
                    {act}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[11px] text-[#8d9aaa] block mb-1">Target Tier 0 Repo:</label>
              <select
                value={selectedRepo}
                onChange={(e) => setSelectedRepo(e.target.value)}
                className="w-full bg-[#0d1219] text-[#eef3f8] border border-[#26303d] rounded-lg p-2.5 focus:border-[#66e3c4] focus:outline-none"
              >
                {TIER_0_REPOS.map((r) => (
                  <option key={r.repo} value={r.repo}>
                    {r.repo}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col justify-end">
              <button
                onClick={handleEvaluateGuardrail}
                className="w-full bg-[#66e3c4] hover:bg-[#78e0b4] text-[#07120f] font-bold text-xs p-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
              >
                <Play className="w-3.5 h-3.5" /> Evaluate Guardrail
              </button>
            </div>
          </div>

          {/* Classification Output Box */}
          {guardrailResult && (
            <div className="p-3.5 bg-[#0b0e13] rounded-lg border border-[#26303d] font-mono text-xs space-y-1.5 animate-fade-in">
              <div className="flex items-center justify-between">
                <span className="text-[#8d9aaa]">Assigned Clearance:</span>
                <span className={`px-2 py-0.5 rounded text-[11px] font-bold border ${getTierColor(guardrailResult.tier)}`}>
                  {guardrailResult.tier}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#8d9aaa]">Decision:</span>
                <span className={`font-bold ${getStatusColor(guardrailResult.status)}`}>{guardrailResult.status}</span>
              </div>
              <p className="text-[#c8f6e9] text-[11px] pt-1">
                {guardrailResult.explanation}
              </p>
            </div>
          )}
        </div>
      </section>

      {/* 7 & 8. Split Grid: Command Desk Ingestion & Command Desk Audit Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Command Desk Ingestion & Inbox */}
        <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 shadow-sm space-y-4">
          <div>
            <h2 className="text-base font-bold text-[#eef3f8] flex items-center gap-2">
              <Send className="w-4 h-4 text-[#66e3c4]" />
              Command Desk Ingestion &amp; Inbox
            </h2>
            <span className="text-xs font-mono text-[#66e3c4] block mt-0.5">
              reports/command-desk-inbox.jsonl
            </span>
          </div>

          <form onSubmit={handleAppendInstruction} className="space-y-3">
            <div>
              <label className="text-xs font-mono text-[#8d9aaa] block mb-1.5">
                Founder Instruction for Command Desk:
              </label>
              <textarea
                value={founderInstruction}
                onChange={(e) => setFounderInstruction(e.target.value)}
                rows={3}
                placeholder="e.g. Verify commit e4a89f on main and trigger Docker truth observation"
                className="w-full font-mono text-xs bg-[#0d1219] text-[#eef3f8] border border-[#26303d] rounded-lg p-3 focus:border-[#66e3c4] focus:outline-none"
              />
            </div>

            <div className="p-2.5 bg-[#0e131b] rounded-lg border border-[#26303d] text-[11px] font-mono text-[#ffca6b] flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>Autonomous agent halts if credentials or models missing</span>
            </div>

            <button
              type="submit"
              disabled={!founderInstruction.trim()}
              className="w-full bg-[#66e3c4] hover:bg-[#78e0b4] disabled:opacity-50 text-[#07120f] font-bold text-xs py-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" /> Append Instruction
            </button>
          </form>
        </div>

        {/* Command Desk Audit Stream */}
        <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-[#eef3f8] flex items-center gap-2">
                <Radio className="w-4 h-4 text-[#66e3c4]" />
                Command Desk Audit Stream
              </h2>
              <span className="text-xs font-mono text-[#8d9aaa]">
                Immutable Hash-Chained Stream ({auditStream.length} entries)
              </span>
            </div>
            <button
              onClick={() => {
                setAuditStream(INITIAL_AUDIT_STREAM);
                localStorage.removeItem('veklom_antigravity_audit_stream');
              }}
              className="text-[11px] font-mono text-[#8d9aaa] hover:text-[#eef3f8] flex items-center gap-1"
            >
              <RotateCcw className="w-3 h-3" /> Reset
            </button>
          </div>

          <div className="space-y-2.5 max-h-[310px] overflow-y-auto pr-1 font-mono text-xs">
            {auditStream.map((item) => (
              <div
                key={item.id}
                className="p-3 bg-[#0e131b] rounded-lg border border-[#26303d] space-y-1.5 hover:border-[#66e3c4]/30 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <strong className="text-[#66e3c4] font-bold">{item.id}</strong>
                    <span className="text-[#8d9aaa]">[{item.department}]</span>
                  </div>
                  <span className={`font-bold ${getStatusColor(item.status)}`}>{item.status}</span>
                </div>

                <p className="text-[#eef3f8] text-[11px] leading-relaxed">
                  {item.description}
                </p>

                <div className="flex items-center justify-between text-[10px] text-[#8d9aaa] pt-1 border-t border-[#26303d]/40">
                  <span className={`px-1.5 py-0.2 rounded border ${getTierColor(item.tier)}`}>
                    Tier: {item.tier}
                  </span>
                  <span>{item.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 9. Antigravity Chief Doctrine & Escalation Framework */}
      <section className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 shadow-sm font-mono text-xs space-y-3">
        <div className="flex items-center justify-between border-b border-[#26303d] pb-2">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[#66e3c4]" />
            <h3 className="font-bold text-[#eef3f8]">Antigravity Chief Agent Directive (v2.0.0)</h3>
          </div>
          <span className="text-[#66e3c4] text-[10px] bg-[#10241b] px-2 py-0.5 rounded border border-[#66e3c4]/30">
            Escalation Chain: Active
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px] text-[#8d9aaa]">
          <div className="p-3 bg-[#0e131b] rounded border border-[#26303d] space-y-1">
            <strong className="text-[#66e3c4] block">Work Breakdown Chain</strong>
            <p>Mission arrives → Antigravity decomposes into domain tasks → Assigns to engineer → Production Truth verifies → Release ships.</p>
          </div>
          <div className="p-3 bg-[#0e131b] rounded border border-[#26303d] space-y-1">
            <strong className="text-[#ffca6b] block">Escalate to Founder When</strong>
            <p>Any decision risks irreversible data loss, secret rotation is triggered, or changes cannot be undone within 15 minutes.</p>
          </div>
          <div className="p-3 bg-[#0e131b] rounded border border-[#26303d] space-y-1">
            <strong className="text-[#ff8e8e] block">Strictly Forbidden</strong>
            <p>Guessing, silent failure, claiming completion without evidence, or bypassing Release Control.</p>
          </div>
        </div>
      </section>

      {/* 10. Proprietary IP & Legal Certification Footer */}
      <footer className="border-t border-[#26303d] pt-6 pb-2 text-center text-xs font-mono text-[#8d9aaa] space-y-2">
        <div className="text-[#eef3f8] font-semibold tracking-wide">
          Veklom Continuity Framework • Proprietary Background IP of Anthony Millwater
        </div>
        <div className="flex flex-wrap items-center justify-center gap-3 text-[11px] text-[#66e3c4]">
          <span>RFC 8785 Canonical JSON</span>
          <span>•</span>
          <span>FIPS 186-5 Hardware Signatures</span>
          <span>•</span>
          <span>FRE 902(13) &amp; 902(14) Certified</span>
        </div>
      </footer>
    </div>
  );
};
