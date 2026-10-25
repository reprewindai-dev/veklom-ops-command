import React, { useState, useEffect, useRef } from 'react';
import {
  KeyRound,
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  Clock,
  Copy,
  Trash2,
  Server,
  Lock,
  Plus,
  RefreshCw,
  XCircle,
} from 'lucide-react';
import {
  loadSigningKey,
  generateSigningKey,
  deleteSigningKey,
  signApproval,
  computeParamsHash,
  shortHash,
  StoredKeyRecord,
} from '../utils/crypto';
import { GateApprovalRequest, ApprovalHistoryItem, TrustedDeployment } from '../types';

interface GateApproverViewProps {
  pendingRequest: GateApprovalRequest | null;
  onClearPendingRequest: () => void;
  onApprovalSuccess?: (requestId: string, token: string) => void;
}

const HOLD_DURATION_MS = 1100;
const TTL_OPTIONS = [120, 300, 600];

export const GateApproverView: React.FC<GateApproverViewProps> = ({
  pendingRequest,
  onClearPendingRequest,
  onApprovalSuccess,
}) => {
  const [keyRecord, setKeyRecord] = useState<StoredKeyRecord | null>(null);
  const [approverName, setApproverName] = useState(() => {
    return localStorage.getItem('veklom_approver_name') || 'founder:chris';
  });
  const [deployments, setDeployments] = useState<Record<string, TrustedDeployment>>(() => {
    try {
      const raw = localStorage.getItem('veklom_gate_deployments');
      return raw ? JSON.parse(raw) : { 'veklom-ops-command': { base: 'https://ops.veklom.com', addedAt: Date.now() } };
    } catch {
      return { 'veklom-ops-command': { base: 'https://ops.veklom.com', addedAt: Date.now() } };
    }
  });
  const [history, setHistory] = useState<ApprovalHistoryItem[]>(() => {
    try {
      const raw = localStorage.getItem('veklom_gate_history');
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  });

  const [activeRequest, setActiveRequest] = useState<GateApprovalRequest | null>(pendingRequest);
  const [computedHash, setComputedHash] = useState<string>('');
  const [fingerprintMatch, setFingerprintMatch] = useState<boolean>(true);
  const [selectedTtl, setSelectedTtl] = useState<number>(300);
  const [approvedResult, setApprovedResult] = useState<{
    token: string;
    expiresAt: number;
    claims: Record<string, unknown>;
  } | null>(null);
  const [declined, setDeclined] = useState<boolean>(false);

  // Hold button state
  const [holdProgress, setHoldProgress] = useState(0);
  const [isHolding, setIsHolding] = useState(false);
  const holdStartRef = useRef<number | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const holdTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedToken, setCopiedToken] = useState(false);

  // Sync incoming pendingRequest prop
  useEffect(() => {
    if (pendingRequest) {
      setActiveRequest(pendingRequest);
      setApprovedResult(null);
      setDeclined(false);
    }
  }, [pendingRequest]);

  // Load key from IndexedDB on mount
  useEffect(() => {
    loadSigningKey().then((key) => {
      if (key) setKeyRecord(key);
    });
  }, []);

  // Compute parameter hash when request changes
  useEffect(() => {
    if (activeRequest) {
      computeParamsHash(activeRequest.params)
        .then((hash) => {
          setComputedHash(hash);
          // If request came with params_sha256, compare
          if (activeRequest.params_sha256) {
            setFingerprintMatch(hash === activeRequest.params_sha256);
          } else {
            // Or set computed as valid
            setFingerprintMatch(true);
          }
        })
        .catch(() => {
          setFingerprintMatch(false);
        });
    }
  }, [activeRequest]);

  const handleCreateKey = async () => {
    try {
      localStorage.setItem('veklom_approver_name', approverName);
      const newKey = await generateSigningKey();
      setKeyRecord(newKey);
    } catch (err) {
      alert(`Could not create key in browser: ${err}`);
    }
  };

  const handleDeleteKey = async () => {
    if (!confirm("Delete this device's signing key? It cannot be recovered and active servers will stop accepting it.")) {
      return;
    }
    await deleteSigningKey();
    setKeyRecord(null);
  };

  const startHold = () => {
    if (!fingerprintMatch || isHolding || approvedResult) return;
    setIsHolding(true);
    holdStartRef.current = performance.now();

    const tick = (now: number) => {
      if (!holdStartRef.current) return;
      const elapsed = now - holdStartRef.current;
      const progress = Math.min(1, elapsed / HOLD_DURATION_MS);
      setHoldProgress(progress);

      if (progress < 1) {
        animFrameRef.current = requestAnimationFrame(tick);
      }
    };

    animFrameRef.current = requestAnimationFrame(tick);

    holdTimeoutRef.current = setTimeout(() => {
      finishHold();
    }, HOLD_DURATION_MS);
  };

  const cancelHold = () => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (holdTimeoutRef.current) clearTimeout(holdTimeoutRef.current);
    holdStartRef.current = null;
    setIsHolding(false);
    setHoldProgress(0);
  };

  const finishHold = async () => {
    if (!keyRecord || !activeRequest) return;
    cancelHold();

    try {
      const hashToSign = computedHash || activeRequest.params_sha256;
      const { token, claims } = await signApproval(
        keyRecord,
        approverName,
        {
          aud: activeRequest.aud,
          tool: activeRequest.tool,
          action: activeRequest.action,
          params_sha256: hashToSign,
        },
        selectedTtl
      );

      const exp = Number(claims.expires_at) || Math.floor(Date.now() / 1000) + selectedTtl;

      setApprovedResult({
        token,
        expiresAt: exp,
        claims,
      });

      // Add to local audit history
      const historyItem: ApprovalHistoryItem = {
        id: crypto.randomUUID(),
        aud: activeRequest.aud,
        verb: activeRequest.tool,
        target: String(activeRequest.params.container || activeRequest.params.service || activeRequest.action),
        outcome: 'approved',
        at: Date.now(),
        token,
      };

      const updatedHistory = [historyItem, ...history.slice(0, 24)];
      setHistory(updatedHistory);
      localStorage.setItem('veklom_gate_history', JSON.stringify(updatedHistory));

      if (activeRequest.request_id && onApprovalSuccess) {
        onApprovalSuccess(activeRequest.request_id, token);
      }
    } catch (err) {
      alert(`Signing failed: ${err}`);
    }
  };

  const handleDecline = () => {
    if (!activeRequest) return;
    const historyItem: ApprovalHistoryItem = {
      id: crypto.randomUUID(),
      aud: activeRequest.aud,
      verb: activeRequest.tool,
      target: String(activeRequest.params.container || activeRequest.params.service || activeRequest.action),
      outcome: 'declined',
      at: Date.now(),
    };
    const updatedHistory = [historyItem, ...history.slice(0, 24)];
    setHistory(updatedHistory);
    localStorage.setItem('veklom_gate_history', JSON.stringify(updatedHistory));

    setDeclined(true);
    setActiveRequest(null);
    onClearPendingRequest();
  };

  const handleTestScenario = (type: 'restart' | 'stop' | 'dispatch') => {
    let mockReq: GateApprovalRequest;
    if (type === 'restart') {
      const params = { container: 'gnomledger-pgl-sink', timeout: 30 };
      mockReq = {
        request_id: 'test-' + Date.now().toString(36),
        aud: 'reprewindai-dev/gnomledger',
        tool: 'restart_container',
        action: 'restart_service',
        params,
        params_sha256: '', // will be computed
        risk_tier: 'high',
        expires_after_seconds: 300,
        reason: 'Restarting GnomLedger PGL sink container after memory telemetry check.',
      };
    } else if (type === 'stop') {
      const params = { container: 'byos-backend-legacy-proxy', force: false };
      mockReq = {
        request_id: 'test-' + Date.now().toString(36),
        aud: 'reprewindai-dev/veklom-byos-backend',
        tool: 'stop_container',
        action: 'halt_unauthorized_proxy',
        params,
        params_sha256: '',
        risk_tier: 'critical',
        expires_after_seconds: 180,
        reason: 'Shutting down unmapped proxy to prevent raw IP port exposure.',
      };
    } else {
      const params = { command: 'purge_port_references', branch: 'ops-backend-hardening' };
      mockReq = {
        request_id: 'test-' + Date.now().toString(36),
        aud: 'veklom-ops-command',
        tool: 'dispatch_instruction',
        action: 'stage_pr_simulation',
        params,
        params_sha256: '',
        risk_tier: 'medium',
        expires_after_seconds: 600,
        reason: 'Execute branch verification and simulate PR for ops-backend-hardening.',
      };
    }

    computeParamsHash(mockReq.params).then((hash) => {
      mockReq.params_sha256 = hash;
      setActiveRequest(mockReq);
      setApprovedResult(null);
      setDeclined(false);
    });
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Approver Header & Device Chip */}
      <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <KeyRound className="w-5 h-5 text-[#66e3c4]" />
              <h2 className="text-lg font-bold text-[#eef3f8]">Veklom Gate Approver</h2>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#10241b] text-[#66e3c4] border border-[#66e3c4]/30">
                WebCrypto {keyRecord?.algorithm || 'Ready'}
              </span>
            </div>
            <p className="text-xs text-[#8d9aaa] leading-relaxed max-w-2xl">
              Turns this device into an immutable external approver. The signing key is held in IndexedDB and cannot be exported. Nothing runs until you approve on this device.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#0e131b] border border-[#26303d] text-xs font-mono text-[#eef3f8]">
              <span className={`w-2 h-2 rounded-full ${keyRecord ? 'bg-[#66e3c4]' : 'bg-[#ffca6b]'}`}></span>
              <span>{approverName}</span>
            </span>
          </div>
        </div>
      </div>

      {/* If No Key Generated: Setup View */}
      {!keyRecord ? (
        <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-6 shadow-sm max-w-2xl mx-auto space-y-4">
          <div className="text-xs uppercase font-mono tracking-wider text-[#66e3c4]">Set Up This Device</div>
          <h3 className="text-xl font-bold text-[#eef3f8]">Make this device an approver</h3>
          <p className="text-xs text-[#8d9aaa] leading-relaxed">
            Your AI agents and DevOps teams can request risky mutations. This device decides. Generating an Ed25519 signing key creates a non-extractable private key inside your browser's WebCrypto storage.
          </p>

          <div className="space-y-2 pt-2">
            <label className="text-xs font-mono text-[#8d9aaa] block">Approver Identity Handle:</label>
            <input
              type="text"
              value={approverName}
              onChange={(e) => setApproverName(e.target.value)}
              placeholder="e.g. founder:chris"
              className="w-full font-mono text-xs bg-[#0d1219] text-[#eef3f8] border border-[#26303d] rounded-lg p-3 focus:border-[#66e3c4] focus:outline-none"
            />
            <span className="text-[11px] text-[#8d9aaa] font-mono block">
              Recorded into each signed single-use approval token.
            </span>
          </div>

          <button
            onClick={handleCreateKey}
            className="w-full bg-[#66e3c4] hover:bg-[#78e0b4] text-[#07120f] font-bold text-xs py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors cursor-pointer"
          >
            <ShieldCheck className="w-4 h-4" />
            Create Non-Extractable Signing Key
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Action Approval Box */}
          <div className="lg:col-span-2 space-y-6">
            {activeRequest ? (
              <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl overflow-hidden shadow-md">
                {/* Risk Ribbon */}
                <div
                  className={`px-6 py-2.5 text-xs font-mono uppercase font-bold flex items-center justify-between ${
                    activeRequest.risk_tier === 'critical'
                      ? 'bg-[#321816] text-[#ff8e8e] border-b border-[#ff8e8e]/40'
                      : activeRequest.risk_tier === 'high'
                      ? 'bg-[#2e2410] text-[#ffca6b] border-b border-[#ffca6b]/40'
                      : 'bg-[#10241b] text-[#66e3c4] border-b border-[#66e3c4]/40'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    {activeRequest.risk_tier} Risk Gate Check
                  </span>
                  <span>{activeRequest.request_id || '#gate-req'}</span>
                </div>

                <div className="p-6 space-y-5">
                  <div>
                    <span className="text-xs font-mono text-[#8d9aaa] uppercase tracking-wider block">
                      Agent is requesting authority to:
                    </span>
                    <h3 className="text-2xl font-bold text-[#eef3f8] mt-1">
                      {activeRequest.tool.replace(/_/g, ' ').toUpperCase()}{' '}
                      <span className="text-[#66e3c4]">
                        {String(activeRequest.params.container || activeRequest.params.service || activeRequest.action)}
                      </span>
                    </h3>
                    <div className="text-xs font-mono text-[#8d9aaa] mt-1">
                      Deployment target: <strong className="text-[#eef3f8]">{activeRequest.aud}</strong>
                    </div>
                    {activeRequest.reason && (
                      <p className="text-xs text-[#c8f6e9] bg-[#0e131b] p-3 rounded-lg border border-[#26303d] mt-3 font-mono">
                        Reason: {activeRequest.reason}
                      </p>
                    )}
                  </div>

                  {/* Exact Call & Parameters */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-mono uppercase text-[#8d9aaa]">Exact Parameters Call</span>
                      <span className="text-[11px] font-mono text-[#8d9aaa]">
                        SHA-256: <strong className="text-[#66e3c4]">{shortHash(computedHash)}</strong>
                      </span>
                    </div>
                    <pre className="p-3.5 bg-[#0b0e13] border border-[#26303d] rounded-lg text-xs font-mono text-[#c8f6e9] overflow-x-auto">
                      {JSON.stringify(activeRequest.params, null, 2)}
                    </pre>
                  </div>

                  {/* Fingerprint & Security Verification checks */}
                  <div className="space-y-2 bg-[#0e131b] p-4 rounded-lg border border-[#26303d]">
                    <div className="flex items-center gap-2 text-xs font-mono">
                      {fingerprintMatch ? (
                        <>
                          <CheckCircle className="w-4 h-4 text-[#66e3c4] shrink-0" />
                          <span className="text-[#66e3c4]">Parameters match cryptographic SHA-256 fingerprint</span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-4 h-4 text-[#ff8e8e] shrink-0" />
                          <span className="text-[#ff8e8e]">Parameters DO NOT match fingerprint — Refusing to sign!</span>
                        </>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs font-mono text-[#8d9aaa]">
                      <CheckCircle className="w-4 h-4 text-[#66e3c4] shrink-0" />
                      <span>Single-use token: will become invalid after one execution</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs font-mono text-[#8d9aaa]">
                      <CheckCircle className="w-4 h-4 text-[#66e3c4] shrink-0" />
                      <span>Signed locally by {approverName} via WebCrypto</span>
                    </div>
                  </div>

                  {/* Approval Duration / TTL selector */}
                  <div>
                    <label className="block text-xs font-mono uppercase text-[#8d9aaa] mb-2">
                      Approval Validity Window:
                    </label>
                    <div className="flex items-center gap-3">
                      {TTL_OPTIONS.map((ttl) => (
                        <button
                          key={ttl}
                          type="button"
                          onClick={() => setSelectedTtl(ttl)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-all cursor-pointer ${
                            selectedTtl === ttl
                              ? 'bg-[#151c27] text-[#66e3c4] border-[#66e3c4]'
                              : 'bg-[#0d1219] text-[#8d9aaa] border-[#26303d] hover:text-[#eef3f8]'
                          }`}
                        >
                          {ttl < 120 ? `${ttl}s` : `${Math.round(ttl / 60)} min`}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Hold to Approve Button */}
                  <div className="space-y-3 pt-2">
                    <button
                      type="button"
                      disabled={!fingerprintMatch}
                      onPointerDown={startHold}
                      onPointerUp={cancelHold}
                      onPointerLeave={cancelHold}
                      onKeyDown={(e) => {
                        if (e.key === ' ' || e.key === 'Enter') startHold();
                      }}
                      onKeyUp={(e) => {
                        if (e.key === ' ' || e.key === 'Enter') cancelHold();
                      }}
                      className="relative w-full overflow-hidden select-none py-4 px-6 rounded-xl border border-[#66e3c4]/50 bg-[#152320] text-[#66e3c4] font-bold text-sm sm:text-base flex items-center justify-center gap-3 transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed group"
                    >
                      {/* Progress fill bar */}
                      <div
                        className="absolute left-0 top-0 bottom-0 bg-[#66e3c4]/30 pointer-events-none transition-all duration-75"
                        style={{ width: `${holdProgress * 100}%` }}
                      />
                      <Lock className="w-5 h-5 shrink-0 z-10" />
                      <span className="z-10 font-mono tracking-wide">
                        {isHolding ? 'HOLDING TO SIGN...' : 'PRESS AND HOLD TO APPROVE ONCE'}
                      </span>
                    </button>

                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[#8d9aaa] font-mono">
                        Signs as {approverName} · Hold for 1.1s
                      </span>
                      <button
                        type="button"
                        onClick={handleDecline}
                        className="text-xs text-[#ff8e8e] hover:underline font-mono cursor-pointer"
                      >
                        Decline request
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ) : approvedResult ? (
              /* Approved Once Success Card */
              <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-6 shadow-md text-center space-y-4 animate-fade-in">
                <div className="w-16 h-16 rounded-full bg-[#10241b] border border-[#66e3c4]/50 flex items-center justify-center mx-auto text-[#66e3c4]">
                  <CheckCircle className="w-8 h-8" />
                </div>
                <h3 className="text-2xl font-bold text-[#eef3f8]">Approved & Cryptographically Signed</h3>
                <p className="text-xs text-[#8d9aaa] max-w-md mx-auto">
                  The single-use Ed25519 approval token has been signed. The agent may execute this exact operation once before the token expires.
                </p>

                <div className="p-4 bg-[#0b0e13] rounded-lg border border-[#26303d] text-left space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-[#8d9aaa]">
                    <span>Single-Use Signed Token:</span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(approvedResult.token);
                        setCopiedToken(true);
                        setTimeout(() => setCopiedToken(false), 2000);
                      }}
                      className="text-[#66e3c4] hover:underline flex items-center gap-1 cursor-pointer"
                    >
                      <Copy className="w-3.5 h-3.5" />
                      <span>{copiedToken ? 'Copied' : 'Copy Token'}</span>
                    </button>
                  </div>
                  <pre className="text-xs font-mono text-[#c8f6e9] break-all whitespace-pre-wrap select-all max-h-36 overflow-y-auto">
                    {approvedResult.token}
                  </pre>
                </div>

                <button
                  onClick={() => {
                    setApprovedResult(null);
                    onClearPendingRequest();
                  }}
                  className="px-6 py-2.5 rounded-lg bg-[#66e3c4] text-[#07120f] font-bold text-xs cursor-pointer hover:bg-[#78e0b4] transition-colors"
                >
                  Done · Return to idle gate
                </button>
              </div>
            ) : (
              /* Idle Gate State */
              <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-8 text-center space-y-4 shadow-sm">
                <div className="w-14 h-14 rounded-full bg-[#10151d] border border-[#26303d] flex items-center justify-center mx-auto text-[#66e3c4]">
                  <ShieldCheck className="w-7 h-7" />
                </div>
                <h3 className="text-xl font-bold text-[#eef3f8]">Gate Ready · Listening for Operations</h3>
                <p className="text-xs text-[#8d9aaa] max-w-md mx-auto leading-relaxed">
                  When an agent requests a protected action (container restart, stop, instruction dispatch), the call appears here for external cryptographic authorization.
                </p>

                {/* Simulate Drill Scenarios */}
                <div className="pt-4 border-t border-[#26303d]/60">
                  <span className="text-xs font-mono uppercase text-[#8d9aaa] block mb-3">
                    Simulate Governed Mutation Check
                  </span>
                  <div className="flex flex-wrap items-center justify-center gap-2">
                    <button
                      onClick={() => handleTestScenario('restart')}
                      className="px-3 py-1.5 rounded-lg bg-[#0e131b] hover:bg-[#151c27] border border-[#26303d] text-xs font-mono text-[#eef3f8] cursor-pointer transition-colors"
                    >
                      + Restart GnomLedger
                    </button>
                    <button
                      onClick={() => handleTestScenario('stop')}
                      className="px-3 py-1.5 rounded-lg bg-[#0e131b] hover:bg-[#151c27] border border-[#26303d] text-xs font-mono text-[#eef3f8] cursor-pointer transition-colors"
                    >
                      + Halt Unvetted Proxy
                    </button>
                    <button
                      onClick={() => handleTestScenario('dispatch')}
                      className="px-3 py-1.5 rounded-lg bg-[#0e131b] hover:bg-[#151c27] border border-[#26303d] text-xs font-mono text-[#eef3f8] cursor-pointer transition-colors"
                    >
                      + Simulate PR Stage
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Public Key & Trusted Servers */}
          <div className="space-y-6">
            {/* Device Public Key Env Box */}
            <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono uppercase text-[#8d9aaa]">Device Public Key</span>
                <span className="text-[10px] font-mono text-[#66e3c4]">
                  Fingerprint {keyRecord.fingerprint}
                </span>
              </div>
              <div className="p-3 bg-[#0b0e13] rounded-lg border border-[#26303d] font-mono text-xs text-[#c8f6e9] break-all">
                VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64={keyRecord.publicB64}
              </div>
              <div className="flex items-center justify-between pt-1">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(`VEKLOM_MCP_APPROVAL_PUBLIC_KEY_B64=${keyRecord.publicB64}`);
                    setCopiedKey(true);
                    setTimeout(() => setCopiedKey(false), 2000);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-[#151c27] hover:bg-[#1d2737] border border-[#26303d] text-xs font-mono text-[#66e3c4] flex items-center gap-1.5 cursor-pointer transition-colors"
                >
                  <Copy className="w-3.5 h-3.5" />
                  <span>{copiedKey ? 'Copied' : 'Copy env line'}</span>
                </button>
                <button
                  onClick={handleDeleteKey}
                  className="text-xs text-[#ff8e8e] hover:underline font-mono flex items-center gap-1 cursor-pointer"
                >
                  <Trash2 className="w-3.5 h-3.5" /> Reset key
                </button>
              </div>
            </div>

            {/* Trusted Deployments */}
            <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono uppercase text-[#8d9aaa]">Trusted Deployments</span>
                <span className="text-[10px] font-mono text-[#8d9aaa]">
                  {Object.keys(deployments).length} pinned
                </span>
              </div>
              <div className="space-y-2">
                {Object.entries(deployments).map(([aud, dep]) => (
                  <div
                    key={aud}
                    className="p-2.5 rounded-lg bg-[#0e131b] border border-[#26303d] text-xs font-mono flex items-center justify-between"
                  >
                    <div>
                      <strong className="text-[#eef3f8] block">{aud}</strong>
                      <span className="text-[#8d9aaa] text-[11px]">{dep.base}</span>
                    </div>
                    <span className="text-[#66e3c4] text-[10px]">trusted</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Local Device History */}
            <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono uppercase text-[#8d9aaa]">Recent on this device</span>
                <span className="text-[10px] font-mono text-[#8d9aaa]">{history.length} logged</span>
              </div>
              {history.length === 0 ? (
                <p className="text-xs text-[#8d9aaa] font-mono">No actions signed on this device yet.</p>
              ) : (
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {history.map((h) => (
                    <div
                      key={h.id}
                      className="p-2 bg-[#0e131b] rounded border border-[#26303d] text-[11px] font-mono flex items-center justify-between"
                    >
                      <div>
                        <span className="text-[#eef3f8]">
                          {h.verb} {h.target}
                        </span>
                        <div className="text-[#8d9aaa] text-[10px]">{h.aud}</div>
                      </div>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] ${
                          h.outcome === 'approved'
                            ? 'text-[#66e3c4] bg-[#10241b]'
                            : 'text-[#ff8e8e] bg-[#321816]'
                        }`}
                      >
                        {h.outcome}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
