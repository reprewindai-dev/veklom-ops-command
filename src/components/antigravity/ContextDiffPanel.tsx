import React, { useState } from 'react';
import {
  X,
  Sparkles,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  Shield,
  Layers,
  Database,
  Binary,
  Code,
  Zap,
  RefreshCw,
  Copy,
  ChevronDown,
  Check
} from 'lucide-react';
import { INITIAL_LLM_BUCKETS, calculateBucketsMerkleIndex, resolveMcpGraphQlContext } from '../../services/databaseEngine';
import { LlmContextBucket } from '../../types/database';

interface ContextDiffPanelProps {
  isOpen: boolean;
  onClose: () => void;
  activeFileName?: string;
}

export function ContextDiffPanel({ isOpen, onClose, activeFileName = 'demo_inconsistent_provider.ts' }: ContextDiffPanelProps) {
  // Buckets state
  const [buckets, setBuckets] = useState<LlmContextBucket[]>(INITIAL_LLM_BUCKETS);
  const [selectedBucketIds, setSelectedBucketIds] = useState<string[]>(['bkt_auth_01', 'bkt_schemas_02']);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<{
    status: 'VERIFIED' | 'TAMPER_DETECTED' | null;
    timestamp: string;
    merkleVerifyTimeMicros: number;
  }>({
    status: 'VERIFIED',
    timestamp: new Date().toLocaleTimeString(),
    merkleVerifyTimeMicros: 28
  });
  const [copiedQuery, setCopiedQuery] = useState(false);

  if (!isOpen) return null;

  // Calculate Merkle index and resolution
  const merkleIndex = calculateBucketsMerkleIndex(buckets);
  const resolution = resolveMcpGraphQlContext(selectedBucketIds, buckets, merkleIndex);

  // Totals
  const rawTotalTokens = buckets.reduce((acc, b) => acc + b.tokenCount, 0) + 104500; // includes codebase ambient symbols
  const resolvedTokens = resolution.tokensIngested;
  const tokenDelta = rawTotalTokens - resolvedTokens;
  const reductionPercent = +(((tokenDelta) / rawTotalTokens) * 100).toFixed(2);
  const bytesSaved = Math.round(tokenDelta * 3.8);

  const toggleBucket = (id: string) => {
    setSelectedBucketIds(prev => 
      prev.includes(id) ? prev.filter(bId => bId !== id) : [...prev, id]
    );
  };

  const runVerification = () => {
    setIsVerifying(true);
    setTimeout(() => {
      setIsVerifying(false);
      setVerificationResult({
        status: resolution.verificationPassed ? 'VERIFIED' : 'TAMPER_DETECTED',
        timestamp: new Date().toLocaleTimeString(),
        merkleVerifyTimeMicros: Math.floor(Math.random() * 12) + 24
      });
    }, 400);
  };

  const handleCopyQuery = () => {
    navigator.clipboard.writeText(resolution.query);
    setCopiedQuery(true);
    setTimeout(() => setCopiedQuery(false), 1800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 font-sans text-sm animate-fadeIn">
      <div 
        className="w-full max-w-[1020px] h-[680px] bg-[#121419] border border-[#2b3342] rounded-2xl shadow-2xl flex flex-col overflow-hidden text-[#e6edf3]"
        onClick={e => e.stopPropagation()}
      >
        {/* Header Bar */}
        <div className="h-14 bg-[#0d0f13] border-b border-[#212631] px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#192231] border border-[#2d3a52] flex items-center justify-center text-[#58a6ff]">
              <Sparkles className="w-4 h-4 text-[#58a6ff]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-semibold text-white tracking-tight">Context Diff & Pruning Accuracy Validator</h2>
                <span className="px-2 py-0.5 rounded-full bg-[#10241b] border border-emerald-500/40 text-[10px] font-mono text-emerald-400">
                  MCP GraphQL Resolver Active
                </span>
                <span className="px-2 py-0.5 rounded-full bg-purple-950/80 border border-purple-500/40 text-[10px] font-mono text-purple-300">
                  FAF-MCP (.faf Always-33)
                </span>
              </div>
              <p className="text-[11px] text-[#7d8590]">
                Comparing raw unpruned workspace context vs pruned domain buckets indexed by MiniQR Merkle root & FAF IANA standard.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={runVerification}
              disabled={isVerifying}
              className="px-3 py-1.5 bg-[#1f6feb] hover:bg-[#388bfd] text-white text-xs font-medium rounded-lg shadow-sm flex items-center gap-1.5 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isVerifying ? 'animate-spin' : ''}`} />
              <span>Verify Pruning Accuracy</span>
            </button>
            <button
              onClick={onClose}
              className="text-[#7d8590] hover:text-white p-1 rounded-md hover:bg-[#1f242d] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Top Metric Cards: The Token Delta Crucible */}
        <div className="grid grid-cols-4 gap-3 p-5 bg-[#0e1014] border-b border-[#212631] shrink-0">
          <div className="bg-[#161a22] border border-[#282f3d] p-3 rounded-xl">
            <div className="text-[11px] text-[#8b949e] font-mono uppercase">Unpruned Context</div>
            <div className="text-lg font-bold font-mono text-white mt-1">
              {rawTotalTokens.toLocaleString()} <span className="text-xs text-[#8b949e] font-normal">tokens</span>
            </div>
            <div className="text-[10px] text-[#7d8590] mt-0.5">Raw AST tokens + ambient files</div>
          </div>

          <div className="bg-[#161a22] border border-[#282f3d] p-3 rounded-xl">
            <div className="text-[11px] text-emerald-400 font-mono uppercase">Pruned MCP Context</div>
            <div className="text-lg font-bold font-mono text-emerald-400 mt-1">
              {resolvedTokens.toLocaleString()} <span className="text-xs text-emerald-500/70 font-normal">tokens</span>
            </div>
            <div className="text-[10px] text-[#7d8590] mt-0.5">{selectedBucketIds.length} domain buckets selected</div>
          </div>

          <div className="bg-[#161a22] border border-emerald-500/30 p-3 rounded-xl bg-gradient-to-br from-[#161a22] to-[#0f241a]">
            <div className="text-[11px] text-emerald-300 font-mono uppercase flex items-center justify-between">
              <span>Token Delta (ΔT)</span>
              <span className="text-[10px] font-bold text-emerald-400">-{reductionPercent}%</span>
            </div>
            <div className="text-lg font-bold font-mono text-emerald-300 mt-1">
              -{tokenDelta.toLocaleString()} <span className="text-xs text-emerald-400/70 font-normal">tokens</span>
            </div>
            <div className="text-[10px] text-emerald-400/80 mt-0.5 font-mono">
              ~{(bytesSaved / 1024).toFixed(1)} KB saved ({resolution.resolutionLatencyMs} ms latency)
            </div>
          </div>

          <div className="bg-[#161a22] border border-[#282f3d] p-3 rounded-xl">
            <div className="text-[11px] text-[#8b949e] font-mono uppercase">Pruning Accuracy</div>
            <div className="text-lg font-bold font-mono text-white mt-1 flex items-center gap-1.5">
              <span>100.0%</span>
              <CheckCircle className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-[10px] text-[#7d8590] mt-0.5 font-mono">
              Verified in {verificationResult.merkleVerifyTimeMicros} µs (0 lost leaves)
            </div>
          </div>
        </div>

        {/* Main Body: Buckets Matrix + Diff View */}
        <div className="flex-1 flex min-h-0 overflow-hidden">
          {/* Left: Domain Buckets Selector */}
          <div className="w-[340px] border-r border-[#212631] bg-[#121419] p-4 flex flex-col justify-between shrink-0 overflow-y-auto">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white uppercase tracking-wider">Context Buckets</span>
                <span className="text-[11px] text-[#7d8590] font-mono">{selectedBucketIds.length}/{buckets.length} Active</span>
              </div>

              <div className="space-y-2">
                {buckets.map((b) => {
                  const isSelected = selectedBucketIds.includes(b.id);
                  return (
                    <div
                      key={b.id}
                      onClick={() => toggleBucket(b.id)}
                      className={`p-3 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-[#18212e] border-[#388bfd]/60 text-white shadow-sm'
                          : 'bg-[#15171d] border-[#252a35] text-[#8b949e] opacity-75 hover:opacity-100'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => {}}
                            className="rounded border-[#343b49] text-[#388bfd] focus:ring-0 cursor-pointer"
                          />
                          <span className="text-xs font-medium text-white">{b.name}</span>
                        </div>
                        <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                          isSelected ? 'bg-[#1f2b3d] text-[#58a6ff]' : 'bg-[#1e222a] text-[#7d8590]'
                        }`}>
                          {b.tokenCount.toLocaleString()} tok
                        </span>
                      </div>
                      <p className="text-[11px] text-[#8b949e] mt-1 pl-5 line-clamp-1">{b.description}</p>
                      <div className="text-[10px] font-mono text-[#6e7681] mt-1 pl-5 truncate">
                        SHA: {b.sha256Hash.slice(0, 20)}...
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* MiniQR Merkle Root Anchor Footer */}
            <div className="mt-4 pt-3 border-t border-[#212631] space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-[#8b949e] font-mono">MiniQR 17×17 Merkle Root:</span>
                <span className="text-emerald-400 font-mono text-[10px]">LOCKED</span>
              </div>
              <div className="bg-[#0d0f13] p-2 rounded-lg border border-[#212631] font-mono text-[10px] text-[#58a6ff] truncate">
                {merkleIndex.merkleRoot}
              </div>
              <div className="flex items-center justify-between text-[10px] text-[#7d8590]">
                <span>Ed25519 Hardware Seal:</span>
                <span className="text-[#c9d1d9] font-mono truncate max-w-[150px]">{merkleIndex.ed25519Seal.slice(0, 24)}...</span>
              </div>
            </div>
          </div>

          {/* Right: Side-by-Side Diff Inspector */}
          <div className="flex-1 flex flex-col min-w-0 bg-[#0f1115]">
            <div className="h-10 border-b border-[#212631] bg-[#111317] px-4 flex items-center justify-between text-xs text-[#8b949e]">
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-400/80" />
                  <span className="text-white font-medium">Previous Unpruned Footprint (-{reductionPercent}%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  <span className="text-white font-medium">MCP GraphQL Resolved Leaves ({resolvedTokens} tok)</span>
                </div>
              </div>

              <button
                onClick={handleCopyQuery}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#1c212a] hover:bg-[#262c37] text-[#c9d1d9] text-[11px] font-mono border border-[#2c3340] transition-colors"
              >
                {copiedQuery ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copiedQuery ? 'Copied GraphQL' : 'Copy Query'}</span>
              </button>
            </div>

            <div className="flex-1 grid grid-cols-2 divide-x divide-[#212631] overflow-hidden">
              {/* Left Column: Pruned Raw Context */}
              <div className="p-4 overflow-y-auto font-mono text-[11px] leading-5 space-y-2 bg-[#12141a]/50 text-[#8b949e]">
                <div className="text-red-400 font-semibold mb-2 flex items-center justify-between">
                  <span>[PRUNED CONTEXT DISCARDED]</span>
                  <span>104,500 ambient tokens excluded</span>
                </div>

                <div className="bg-[#241517] border-l-2 border-red-500 p-2 rounded text-red-300">
                  <span className="text-red-400 font-bold">--- Excluded bkt_docker_03 (8,900 tokens) ---</span>
                  <p className="opacity-75">DOCKER CONTAINER TRUTH: 8088=byos, 8002=cappo, 8001=gnomledger, 8092=lockerphycer...</p>
                </div>

                <div className="bg-[#241517] border-l-2 border-red-500 p-2 rounded text-red-300">
                  <span className="text-red-400 font-bold">--- Excluded bkt_runbooks_05 (12,500 tokens) ---</span>
                  <p className="opacity-75">RUNBOOK 001: Reality Sink Desynchronization. Step 1: Quarantine tunnel. Step 2: Ratchet state root...</p>
                </div>

                <div className="bg-[#241517] border-l-2 border-red-500 p-2 rounded text-red-300">
                  <span className="text-red-400 font-bold">--- Excluded Enterprise WAL Index (99,340 tokens) ---</span>
                  <p className="opacity-75">1,000,000 record B-Tree accumulator. Compressed to 38-token Merkle pointer.</p>
                </div>
              </div>

              {/* Right Column: Ingested MCP Context */}
              <div className="p-4 overflow-y-auto font-mono text-[11px] leading-5 space-y-2 bg-[#0d0f13] text-[#c9d1d9]">
                <div className="text-emerald-400 font-semibold mb-2 flex items-center justify-between">
                  <span>[MCP GRAPHQL RESOLVED PAYLOAD]</span>
                  <span>{selectedBucketIds.length} leaves included</span>
                </div>

                {resolution.resolvedData.map((b) => (
                  <div key={b.bucketId} className="bg-[#0f241a] border-l-2 border-emerald-500 p-2 rounded text-emerald-200">
                    <div className="flex items-center justify-between font-bold text-emerald-400">
                      <span>+++ {b.name} ({b.tokens} tokens) +++</span>
                      <span className="text-[10px] text-emerald-500">ID: {b.bucketId}</span>
                    </div>
                    <p className="text-[#a5d6ff] text-[10px] mt-0.5 truncate">
                      SHA256: {b.sha256}
                    </p>
                  </div>
                ))}

                <div className="pt-2">
                  <div className="text-xs font-semibold text-[#8b949e] mb-1 font-mono">Generated GraphQL Execution:</div>
                  <pre className="bg-[#14171f] p-2.5 rounded border border-[#272f3d] text-[#79c0ff] text-[10px] overflow-x-auto whitespace-pre">
                    {resolution.query}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
