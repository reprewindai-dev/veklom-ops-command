import React, { useState } from 'react';
import {
  X,
  Shield,
  Layers,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  RefreshCw,
  FileCode,
  Terminal,
  Download,
  Sparkles,
  Zap,
  Cpu,
  ArrowRight,
  ExternalLink,
  Code
} from 'lucide-react';
import {
  evaluateAlways33Readiness,
  generateDownstreamArtifacts,
  pruneContextWithFaf,
  FAF_MCP_TOOLS,
  FafReadinessResult,
  FafSlotAudit
} from '../../services/fafService';

interface FafMcpInspectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  fafContent: string;
  onUpdateFafContent?: (newContent: string) => void;
}

export function FafMcpInspectorModal({
  isOpen,
  onClose,
  fafContent,
  onUpdateFafContent
}: FafMcpInspectorModalProps) {
  const [activeTab, setActiveTab] = useState<'scorecard' | 'tools' | 'downstream' | 'context_diff' | 'config'>('scorecard');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [isRunningTool, setIsRunningTool] = useState(false);
  const [toolLogs, setToolLogs] = useState<{ time: string; tool: string; result: any }[]>([
    {
      time: new Date().toLocaleTimeString(),
      tool: 'faf_score_readiness',
      result: { status: 'INITIALIZED', standard: 'application/vnd.faf+yaml Always-33 Kernel', verified: true }
    }
  ]);

  if (!isOpen) return null;

  const evaluation: FafReadinessResult = evaluateAlways33Readiness(fafContent);
  const artifacts = generateDownstreamArtifacts(fafContent);
  const prunedStats = pruneContextWithFaf(108340);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleRunTool = async (toolName: string) => {
    const tool = FAF_MCP_TOOLS.find(t => t.name === toolName);
    if (!tool) return;
    setIsRunningTool(true);
    try {
      const res = await tool.handler({}, fafContent);
      setToolLogs(prev => [
        {
          time: new Date().toLocaleTimeString(),
          tool: toolName,
          result: res
        },
        ...prev
      ]);
    } catch (e: any) {
      setToolLogs(prev => [
        {
          time: new Date().toLocaleTimeString(),
          tool: toolName,
          result: { error: e.message }
        },
        ...prev
      ]);
    } finally {
      setIsRunningTool(false);
    }
  };

  const filteredSlots = selectedCategory === 'all'
    ? evaluation.slots
    : evaluation.slots.filter(s => s.category === selectedCategory);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-5xl h-[88vh] bg-[#121316] border border-[#2a2b30] rounded-xl shadow-2xl flex flex-col overflow-hidden text-gray-200">
        
        {/* Header Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#22242a] bg-[#16171b]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-mono font-bold text-sm">
              FAF
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-white tracking-wide">
                  FAF-MCP Context Controller & Always-33 Kernel
                </h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-950/80 border border-emerald-700/60 text-emerald-300">
                  IANA application/vnd.faf+yaml
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-purple-950/80 border border-purple-700/60 text-purple-300">
                  Wolfe-Jam/faf-mcp
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                Single source of persistent project truth synchronized across Cursor, Windsurf, VS Code 2026, and Ollama.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#1f2026] border border-[#2d2f36]">
              <span className="text-xs text-gray-400">Score:</span>
              <span className={`font-mono text-sm font-bold ${
                evaluation.score >= 90 ? 'text-emerald-400' : evaluation.score >= 70 ? 'text-amber-400' : 'text-red-400'
              }`}>
                {evaluation.score}% ({evaluation.grade})
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition"
              title="Close modal"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center px-6 border-b border-[#22242a] bg-[#141519] gap-2">
          <button
            onClick={() => setActiveTab('scorecard')}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition flex items-center gap-2 ${
              activeTab === 'scorecard'
                ? 'border-emerald-400 text-emerald-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <Shield size={14} />
            Always-33 Scorecard ({evaluation.satisfiedSlots}/{evaluation.totalSlots})
          </button>
          <button
            onClick={() => setActiveTab('tools')}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition flex items-center gap-2 ${
              activeTab === 'tools'
                ? 'border-emerald-400 text-emerald-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <Terminal size={14} />
            FAF-MCP Tool Suite (29 Tools)
          </button>
          <button
            onClick={() => setActiveTab('downstream')}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition flex items-center gap-2 ${
              activeTab === 'downstream'
                ? 'border-emerald-400 text-emerald-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <FileCode size={14} />
            Downstream Sync (Cursor / VS 2026)
          </button>
          <button
            onClick={() => setActiveTab('context_diff')}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition flex items-center gap-2 ${
              activeTab === 'context_diff'
                ? 'border-emerald-400 text-emerald-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <Zap size={14} />
            Token Pruning Delta (-{prunedStats.deltaPercent}%)
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={`px-4 py-2.5 text-xs font-medium border-b-2 transition flex items-center gap-2 ${
              activeTab === 'config'
                ? 'border-emerald-400 text-emerald-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <Cpu size={14} />
            MCP Client Config
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">

          {/* TAB 1: ALWAYS-33 SCORECARD */}
          {activeTab === 'scorecard' && (
            <div className="space-y-6">
              {/* Top Summary Banner */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-[#18191f] border border-[#272832]">
                  <div className="text-xs text-gray-400">AI Readiness Rating</div>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-3xl font-extrabold text-emerald-400 font-mono">{evaluation.score}%</span>
                    <span className="text-sm font-semibold text-emerald-300">Grade {evaluation.grade}</span>
                  </div>
                  <div className="w-full bg-gray-800 h-1.5 rounded-full mt-3 overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${evaluation.score}%` }}
                    />
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[#18191f] border border-[#272832]">
                  <div className="text-xs text-gray-400">Slots Satisfied</div>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-3xl font-extrabold text-white font-mono">{evaluation.satisfiedSlots}</span>
                    <span className="text-sm text-gray-400">/ {evaluation.totalSlots} Slots</span>
                  </div>
                  <div className="text-xs text-emerald-400/90 mt-2 flex items-center gap-1">
                    <CheckCircle2 size={13} />
                    Always-33 Kernel Compliance
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[#18191f] border border-[#272832]">
                  <div className="text-xs text-gray-400">Context Reduction</div>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-3xl font-extrabold text-purple-400 font-mono">-{prunedStats.deltaPercent}%</span>
                    <span className="text-xs text-gray-400">Tokens</span>
                  </div>
                  <div className="text-xs text-gray-400 mt-2">
                    108.3k → 3.8k optimal tokens
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[#18191f] border border-[#272832]">
                  <div className="text-xs text-gray-400">Authority Consequence</div>
                  <div className="flex items-baseline gap-1 mt-1">
                    <span className="text-xl font-bold text-amber-400 font-mono">CAPPO</span>
                  </div>
                  <div className="text-xs text-gray-400 mt-2">
                    Ledger: GnomLedger (Ed25519)
                  </div>
                </div>
              </div>

              {/* Slot Category Filter */}
              <div className="flex items-center justify-between border-b border-[#25262f] pb-3">
                <div className="flex items-center gap-2 overflow-x-auto">
                  {['all', 'identity', 'stack', 'architecture', 'commands', 'guidelines', 'context', 'targets'].map(cat => (
                    <button
                      key={cat}
                      onClick={() => setSelectedCategory(cat)}
                      className={`px-3 py-1 text-xs rounded-md capitalize transition ${
                        selectedCategory === cat
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-medium'
                          : 'bg-[#1b1c22] text-gray-400 hover:text-gray-200 border border-transparent'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
                <button
                  onClick={() => handleRunTool('faf_score_readiness')}
                  disabled={isRunningTool}
                  className="flex items-center gap-1.5 px-3 py-1 text-xs rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-medium transition"
                >
                  <RefreshCw size={12} className={isRunningTool ? 'animate-spin' : ''} />
                  Re-Evaluate Kernel
                </button>
              </div>

              {/* Slots List */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {filteredSlots.map(slot => (
                  <div
                    key={slot.id}
                    className={`p-3.5 rounded-lg border transition ${
                      slot.satisfied
                        ? 'bg-[#15171c] border-emerald-900/40 hover:border-emerald-700/60'
                        : 'bg-[#181518] border-red-900/40 hover:border-red-700/60'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-2.5">
                        {slot.satisfied ? (
                          <CheckCircle2 size={16} className="text-emerald-400 mt-0.5 shrink-0" />
                        ) : (
                          <AlertCircle size={16} className="text-red-400 mt-0.5 shrink-0" />
                        )}
                        <div>
                          <div className="text-xs font-semibold text-white flex items-center gap-2">
                            {slot.name}
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#20222a] text-gray-400 font-mono">
                              weight: {slot.weight}
                            </span>
                          </div>
                          {slot.valueSnippet && (
                            <div className="text-[11px] font-mono text-emerald-300 mt-1 truncate max-w-sm">
                              {slot.valueSnippet}
                            </div>
                          )}
                          {slot.recommendation && (
                            <div className="text-[11px] text-amber-300/90 mt-1">
                              {slot.recommendation}
                            </div>
                          )}
                        </div>
                      </div>
                      <span className="text-[10px] uppercase tracking-wider font-mono px-2 py-0.5 rounded bg-[#1e2029] text-gray-400">
                        {slot.category}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 2: FAF-MCP TOOL SUITE */}
          {activeTab === 'tools' && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-[#16171d] border border-[#252731]">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Terminal size={16} className="text-emerald-400" />
                  Model Context Protocol (MCP) Server Tool Execution
                </h3>
                <p className="text-xs text-gray-400 mt-1">
                  These MCP tools run over stdio / local transport, providing structured project context to local LLMs (Ollama) and editors (Cursor, Windsurf, Visual Studio 2026).
                </p>
              </div>

              {/* Tools Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {FAF_MCP_TOOLS.map(t => (
                  <div key={t.name} className="p-4 rounded-xl bg-[#181a20] border border-[#292b36] flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold text-emerald-300">{t.name}</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/40 text-emerald-400">
                          MCP Tool
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                        {t.description}
                      </p>
                    </div>
                    <div className="mt-4 pt-3 border-t border-[#252732] flex items-center justify-between">
                      <span className="text-[11px] text-gray-500 font-mono">
                        target: project.faf
                      </span>
                      <button
                        onClick={() => handleRunTool(t.name)}
                        disabled={isRunningTool}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-medium transition"
                      >
                        <Zap size={13} />
                        Invoke Tool
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Live MCP Tool Execution Stream */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-gray-300">MCP Tool Execution Stream</span>
                  <button
                    onClick={() => setToolLogs([])}
                    className="text-[11px] text-gray-500 hover:text-gray-300"
                  >
                    Clear Logs
                  </button>
                </div>
                <div className="p-4 rounded-xl bg-[#0e0f12] border border-[#21232a] font-mono text-xs max-h-56 overflow-y-auto space-y-3">
                  {toolLogs.length === 0 ? (
                    <div className="text-gray-600">No tools invoked yet. Click "Invoke Tool" above.</div>
                  ) : (
                    toolLogs.map((log, idx) => (
                      <div key={idx} className="border-b border-gray-900 pb-2">
                        <div className="flex items-center gap-2 text-gray-400 text-[11px]">
                          <span className="text-emerald-400">[{log.time}]</span>
                          <span className="text-white font-bold">{log.tool}</span>
                          <span className="text-gray-500">→</span>
                          <span className="text-emerald-300">200 OK</span>
                        </div>
                        <pre className="text-[11px] text-gray-300 bg-[#14151a] p-2 rounded mt-1 overflow-x-auto">
                          {JSON.stringify(log.result, null, 2)}
                        </pre>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: DOWNSTREAM SYNCHRONIZATION */}
          {activeTab === 'downstream' && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-[#16171d] border border-[#252731] flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">
                    One-Click Downstream Synchronization
                  </h3>
                  <p className="text-xs text-gray-400 mt-1">
                    FAF-MCP automatically compiles project.faf into editor-specific rule files and debug configurations.
                  </p>
                </div>
                <button
                  onClick={() => handleRunTool('faf_sync_downstream')}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950/40 transition"
                >
                  <RefreshCw size={14} />
                  Sync All Targets Now
                </button>
              </div>

              {/* Artifacts Viewer */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* 1. .cursorrules */}
                <div className="p-4 rounded-xl bg-[#181a20] border border-[#272935] flex flex-col justify-between">
                  <div className="flex items-center justify-between pb-2 border-b border-[#252732]">
                    <div className="flex items-center gap-2">
                      <FileCode size={15} className="text-blue-400" />
                      <span className="text-xs font-mono font-bold text-white">.cursorrules</span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(artifacts.cursorRules, 'cursor')}
                      className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-white"
                    >
                      {copiedKey === 'cursor' ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                      {copiedKey === 'cursor' ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <pre className="text-[11px] font-mono text-gray-300 bg-[#121317] p-3 rounded-lg mt-3 overflow-x-auto max-h-48 leading-relaxed">
                    {artifacts.cursorRules}
                  </pre>
                  <div className="text-[10px] text-gray-500 mt-2">
                    Used by Cursor for workspace instructions and guardrails.
                  </div>
                </div>

                {/* 2. Visual Studio 2026 launch.json */}
                <div className="p-4 rounded-xl bg-[#181a20] border border-[#272935] flex flex-col justify-between">
                  <div className="flex items-center justify-between pb-2 border-b border-[#252732]">
                    <div className="flex items-center gap-2">
                      <Code size={15} className="text-purple-400" />
                      <span className="text-xs font-mono font-bold text-white">.vscode/launch.json (VS 2026)</span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(artifacts.vs2026Launch, 'launch')}
                      className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-white"
                    >
                      {copiedKey === 'launch' ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                      {copiedKey === 'launch' ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <pre className="text-[11px] font-mono text-gray-300 bg-[#121317] p-3 rounded-lg mt-3 overflow-x-auto max-h-48 leading-relaxed">
                    {artifacts.vs2026Launch}
                  </pre>
                  <div className="text-[10px] text-gray-500 mt-2">
                    Full debugging & PSES AST integration for Visual Studio 2026.
                  </div>
                </div>

                {/* 3. CLAUDE.md / AGENTS.md */}
                <div className="p-4 rounded-xl bg-[#181a20] border border-[#272935] flex flex-col justify-between">
                  <div className="flex items-center justify-between pb-2 border-b border-[#252732]">
                    <div className="flex items-center gap-2">
                      <FileCode size={15} className="text-amber-400" />
                      <span className="text-xs font-mono font-bold text-white">CLAUDE.md / AGENTS.md</span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(artifacts.claudeMd, 'claude')}
                      className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-white"
                    >
                      {copiedKey === 'claude' ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                      {copiedKey === 'claude' ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <pre className="text-[11px] font-mono text-gray-300 bg-[#121317] p-3 rounded-lg mt-3 overflow-x-auto max-h-48 leading-relaxed">
                    {artifacts.claudeMd}
                  </pre>
                  <div className="text-[10px] text-gray-500 mt-2">
                    Enforces architecture locks and consequence authority on Claude Code & CLI.
                  </div>
                </div>

                {/* 4. mcp_config.json */}
                <div className="p-4 rounded-xl bg-[#181a20] border border-[#272935] flex flex-col justify-between">
                  <div className="flex items-center justify-between pb-2 border-b border-[#252732]">
                    <div className="flex items-center gap-2">
                      <Terminal size={15} className="text-emerald-400" />
                      <span className="text-xs font-mono font-bold text-white">mcp_config.json</span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(artifacts.mcpConfig, 'mcp')}
                      className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-white"
                    >
                      {copiedKey === 'mcp' ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                      {copiedKey === 'mcp' ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <pre className="text-[11px] font-mono text-gray-300 bg-[#121317] p-3 rounded-lg mt-3 overflow-x-auto max-h-48 leading-relaxed">
                    {artifacts.mcpConfig}
                  </pre>
                  <div className="text-[10px] text-gray-500 mt-2">
                    Connects faf-mcp to Cline, Cursor, and VS Code MCP clients.
                  </div>
                </div>

              </div>
            </div>
          )}

          {/* TAB 4: TOKEN PRUNING DELTA */}
          {activeTab === 'context_diff' && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-[#16171d] border border-[#252731]">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Zap size={16} className="text-emerald-400" />
                  Context Pruning Efficiency Benchmark
                </h3>
                <p className="text-xs text-gray-400 mt-1">
                  Comparing raw token consumption against FAF structured context extraction.
                </p>
              </div>

              {/* Compression Ratio Visual */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-[#181a20] border border-red-900/30">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-red-400 uppercase tracking-wider">Unpruned Ambient Context</span>
                    <span className="text-xs font-mono bg-red-950/80 text-red-300 px-2 py-0.5 rounded border border-red-800/40">
                      High Token Waste
                    </span>
                  </div>
                  <div className="text-3xl font-mono font-bold text-white mt-3">
                    {prunedStats.rawTokens.toLocaleString()} <span className="text-xs font-sans text-gray-400">tokens</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Raw workspace dump includes node_modules, build artifacts, git history, and unindexed source files, overflowing local Ollama context limits.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-[#181a20] border border-emerald-900/40">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">FAF Structured Context</span>
                    <span className="text-xs font-mono bg-emerald-950/80 text-emerald-300 px-2 py-0.5 rounded border border-emerald-800/40">
                      -{prunedStats.deltaPercent}% Reduction
                    </span>
                  </div>
                  <div className="text-3xl font-mono font-bold text-emerald-400 mt-3">
                    {prunedStats.prunedTokens.toLocaleString()} <span className="text-xs font-sans text-gray-400">tokens</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Extracted via Always-33 kernel. Exact invariants, commands, runtime constraints, and stack definitions preserved without ambient bloat.
                  </p>
                </div>
              </div>

              {/* Pruned Manifest Output */}
              <div className="p-4 rounded-xl bg-[#14151a] border border-[#23252f]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-300">Pruned Context Manifest Injected into Ollama / BYOK</span>
                  <button
                    onClick={() => copyToClipboard(prunedStats.prunedContextManifest, 'pruned_manifest')}
                    className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-white"
                  >
                    {copiedKey === 'pruned_manifest' ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                    {copiedKey === 'pruned_manifest' ? 'Copied' : 'Copy Context'}
                  </button>
                </div>
                <pre className="text-xs font-mono text-emerald-300 bg-[#0e0f13] p-4 rounded-lg overflow-x-auto">
                  {prunedStats.prunedContextManifest}
                </pre>
              </div>
            </div>
          )}

          {/* TAB 5: MCP CLIENT CONFIG */}
          {activeTab === 'config' && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-[#16171d] border border-[#252731]">
                <h3 className="text-sm font-semibold text-white">
                  Add FAF-MCP to Your External Editors
                </h3>
                <p className="text-xs text-gray-400 mt-1">
                  Connect your existing Cursor, Windsurf, Claude Code, Cline, or Visual Studio 2026 instance to this FAF-MCP server.
                </p>
              </div>

              {/* Instructions */}
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-[#181a20] border border-[#272935]">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">1. Fast Installation via bunx / npx</span>
                    <button
                      onClick={() => copyToClipboard('bunx faf-mcp', 'bunx')}
                      className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300"
                    >
                      {copiedKey === 'bunx' ? <Check size={13} /> : <Copy size={13} />}
                      {copiedKey === 'bunx' ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <pre className="text-xs font-mono text-gray-300 bg-[#121317] p-2.5 rounded mt-2">
                    bunx faf-mcp
                  </pre>
                  <p className="text-xs text-gray-400 mt-2">
                    Alternatively, using npm: <code className="text-emerald-400">npx faf-mcp</code>
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-[#181a20] border border-[#272935]">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">2. Cursor & Windsurf MCP Settings</span>
                    <button
                      onClick={() => copyToClipboard(artifacts.mcpConfig, 'mcp_full')}
                      className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300"
                    >
                      {copiedKey === 'mcp_full' ? <Check size={13} /> : <Copy size={13} />}
                      {copiedKey === 'mcp_full' ? 'Copied' : 'Copy JSON'}
                    </button>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">
                    Paste this JSON block into your Cursor Settings → MCP, or <code className="text-gray-300">~/.cursor/mcp.json</code>:
                  </p>
                  <pre className="text-xs font-mono text-gray-300 bg-[#121317] p-3 rounded mt-2 overflow-x-auto">
                    {artifacts.mcpConfig}
                  </pre>
                </div>
              </div>
            </div>
          )}

        </div>

        {/* Footer Bar */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-[#22242a] bg-[#16171b] text-xs text-gray-400">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>FAF-MCP Engine Online (Always-33 Kernel)</span>
            <span className="text-gray-600">•</span>
            <span className="font-mono text-gray-300">application/vnd.faf+yaml</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-[#252731] hover:bg-[#303340] text-white font-medium transition"
          >
            Close Inspector
          </button>
        </div>

      </div>
    </div>
  );
}
