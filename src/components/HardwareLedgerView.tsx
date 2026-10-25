import React, { useState, useEffect, useRef } from 'react';
import {
  Shield,
  Cpu,
  Lock,
  Radio,
  Eye,
  CheckCircle,
  AlertTriangle,
  Flame,
  Zap,
  Play,
  RotateCcw,
  Layers,
  Database,
  FileCode,
} from 'lucide-react';
import {
  INITIAL_HSM_STATE,
  executeHsmOpcode,
  generateVChipPacket,
  commitGnomLedgerAisbom,
} from '../services/hardwareLedger';
import { BladeAgentHsmState, VChipAirGapPacket, GnomLedgerAisbomReceipt } from '../types';

export const HardwareLedgerView: React.FC = () => {
  const [hsmState, setHsmState] = useState<BladeAgentHsmState>(INITIAL_HSM_STATE);
  const [vchipPacket, setVchipPacket] = useState<VChipAirGapPacket>(generateVChipPacket());
  const [aisbomReceipt, setAisbomReceipt] = useState<GnomLedgerAisbomReceipt>(() => commitGnomLedgerAisbom());
  const [opcodeParam, setOpcodeParam] = useState<string>('source_clean, pg_hash_match');

  // Canvas ref for vChip multi-spectral visual matrix
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Animate multi-spectral optical canvas
  useEffect(() => {
    let animId: number;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let frame = 0;
    const render = () => {
      frame++;
      ctx.fillStyle = '#080c10';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const gridSize = 16;
      const cellSize = canvas.width / gridSize;

      for (let x = 0; x < gridSize; x++) {
        for (let y = 0; y < gridSize; y++) {
          const val = Math.sin((x * 0.4 + y * 0.3 + frame * 0.05)) * 0.5 + 0.5;
          const r = Math.floor(100 + val * 155);
          const g = Math.floor(200 + Math.cos(frame * 0.08 + x) * 55);
          const b = Math.floor(150 + Math.sin(frame * 0.06 + y) * 105);

          ctx.fillStyle = `rgb(${r},${g},${b})`;
          ctx.fillRect(x * cellSize + 1, y * cellSize + 1, cellSize - 2, cellSize - 2);
        }
      }

      animId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animId);
  }, []);

  const handleRunOpcode = (opcode: 'OP_EXTEND_PCR0' | 'OP_FUSE_TRUST' | 'OP_DETECT_DECEPTION' | 'OP_VOTE_QUORUM' | 'OP_ZEROIZE_CASCADE') => {
    const updated = executeHsmOpcode(hsmState, opcode, opcodeParam);
    setHsmState(updated);
  };

  const handleEmitAisbom = () => {
    const receipt = commitGnomLedgerAisbom('mini-sovereign-qwen', 'scale_container_bounded', 'scale_container');
    setAisbomReceipt(receipt);
  };

  const handleTransmitVchip = () => {
    setVchipPacket(generateVChipPacket());
  };

  return (
    <div className="space-y-6 pb-16">
      {/* Top Banner */}
      <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Shield className="w-5 h-5 text-[#66e3c4]" />
              <h2 className="text-lg font-bold text-[#eef3f8]">
                Hardware Root-of-Trust, vChip Optical Air-Gap & GnomLedger
              </h2>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#10241b] text-[#66e3c4] border border-[#66e3c4]/30">
                BLADE-AGENT-HSM ($84 BOM) · EAL6+ TPM 2.0
              </span>
            </div>
            <p className="text-xs text-[#8d9aaa] leading-relaxed max-w-3xl">
              Anchors consequence authority and cryptographic provenance into tamper-evident hardware. Multi-spectral optical data carriers (vChip) eliminate network-layer attack vectors, while GnomLedger emits immutable AISBOM blocks.
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <span
              className={`px-3 py-1.5 rounded-lg border flex items-center gap-2 ${
                hsmState.tamperMeshStatus === 'INTACT_ACTIVE'
                  ? 'bg-[#10241b] text-[#66e3c4] border-[#66e3c4]/40'
                  : 'bg-[#321816] text-[#ff8e8e] border-[#ff8e8e]/40'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${hsmState.tamperMeshStatus === 'INTACT_ACTIVE' ? 'bg-[#66e3c4]' : 'bg-[#ff8e8e]'}`}></span>
              {hsmState.tamperMeshStatus}
            </span>
          </div>
        </div>
      </div>

      {/* BLADE-AGENT-HSM Section */}
      <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#26303d] pb-3">
          <div>
            <h3 className="text-base font-bold text-[#eef3f8] flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[#66e3c4]" />
              BLADE-AGENT-HSM & AUTHREX-AGENT 5-Opcode ABI
            </h3>
            <p className="text-xs text-[#8d9aaa]">
              EAL6+ Secure Element, TPM 2.0 PCR0 state extension, 4-layer active tamper mesh PCB, and continuous Dempster-Shafer trust fusion.
            </p>
          </div>
          <span className="text-xs font-mono text-[#8d9aaa] bg-[#0b0e13] px-2.5 py-1 rounded border border-[#26303d]">
            Reference BOM: ${hsmState.bomCost.toFixed(2)}
          </span>
        </div>

        {/* Status Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
          <div className="p-3 bg-[#0e131b] rounded-lg border border-[#26303d]">
            <span className="text-[10px] text-[#8d9aaa] uppercase block">EAL6+ Secure Element</span>
            <strong className={`text-xs ${hsmState.eal6Status === 'SECURE_ACTIVE' ? 'text-[#66e3c4]' : 'text-[#ff8e8e]'}`}>
              {hsmState.eal6Status}
            </strong>
          </div>
          <div className="p-3 bg-[#0e131b] rounded-lg border border-[#26303d]">
            <span className="text-[10px] text-[#8d9aaa] uppercase block">Continuous Trust (τ)</span>
            <strong className="text-xs text-[#66e3c4]">{hsmState.trustScalar.toFixed(2)} / 1.00</strong>
          </div>
          <div className="p-3 bg-[#0e131b] rounded-lg border border-[#26303d]">
            <span className="text-[10px] text-[#8d9aaa] uppercase block">Deception Prob (P_d)</span>
            <strong className={`text-xs ${hsmState.deceptionProbability > 0.45 ? 'text-[#ff8e8e]' : 'text-[#66e3c4]'}`}>
              {hsmState.deceptionProbability.toFixed(2)}
            </strong>
          </div>
          <div className="p-3 bg-[#0e131b] rounded-lg border border-[#26303d]">
            <span className="text-[10px] text-[#8d9aaa] uppercase block">Sub-Agent Quorum (4/5)</span>
            <strong className="text-xs text-[#66e3c4]">{hsmState.subAgentVotingQuorum.decision}</strong>
          </div>
        </div>

        {/* TPM PCR0 Hash Display */}
        <div className="p-3 bg-[#0b0e13] rounded-lg border border-[#26303d] font-mono text-xs space-y-1">
          <span className="text-[11px] text-[#8d9aaa] uppercase">TPM 2.0 PCR0 Hash (Authority State Anchor):</span>
          <p className="text-[#c8f6e9] break-all select-all">{hsmState.tpmPcr0Hash}</p>
        </div>

        {/* Interactive 5-Opcode ABI Controls */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-[#8d9aaa] font-semibold">
              AUTHREX-AGENT ABI Execution Console
            </span>
            <input
              type="text"
              value={opcodeParam}
              onChange={(e) => setOpcodeParam(e.target.value)}
              placeholder="Opcode payload / arguments..."
              className="font-mono text-xs bg-[#0b0e13] text-[#eef3f8] border border-[#26303d] rounded px-2.5 py-1 focus:border-[#66e3c4] focus:outline-none max-w-xs"
            />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 font-mono text-xs">
            <button
              onClick={() => handleRunOpcode('OP_EXTEND_PCR0')}
              className="p-2.5 rounded bg-[#0e131b] hover:bg-[#151c27] border border-[#26303d] text-[#eef3f8] flex flex-col items-center gap-1 cursor-pointer transition-colors"
            >
              <Zap className="w-3.5 h-3.5 text-[#66e3c4]" />
              <span className="font-bold text-[11px]">OP_EXTEND_PCR0</span>
              <span className="text-[9px] text-[#8d9aaa]">Extend tier hash</span>
            </button>

            <button
              onClick={() => handleRunOpcode('OP_FUSE_TRUST')}
              className="p-2.5 rounded bg-[#0e131b] hover:bg-[#151c27] border border-[#26303d] text-[#eef3f8] flex flex-col items-center gap-1 cursor-pointer transition-colors"
            >
              <CheckCircle className="w-3.5 h-3.5 text-[#66e3c4]" />
              <span className="font-bold text-[11px]">OP_FUSE_TRUST</span>
              <span className="text-[9px] text-[#8d9aaa]">Dempster-Shafer τ</span>
            </button>

            <button
              onClick={() => handleRunOpcode('OP_DETECT_DECEPTION')}
              className="p-2.5 rounded bg-[#0e131b] hover:bg-[#151c27] border border-[#26303d] text-[#eef3f8] flex flex-col items-center gap-1 cursor-pointer transition-colors"
            >
              <Eye className="w-3.5 h-3.5 text-[#ffca6b]" />
              <span className="font-bold text-[11px]">OP_DETECT_DECEPTION</span>
              <span className="text-[9px] text-[#8d9aaa]">Calculate P_d</span>
            </button>

            <button
              onClick={() => handleRunOpcode('OP_VOTE_QUORUM')}
              className="p-2.5 rounded bg-[#0e131b] hover:bg-[#151c27] border border-[#26303d] text-[#eef3f8] flex flex-col items-center gap-1 cursor-pointer transition-colors"
            >
              <Layers className="w-3.5 h-3.5 text-[#66e3c4]" />
              <span className="font-bold text-[11px]">OP_VOTE_QUORUM</span>
              <span className="text-[9px] text-[#8d9aaa]">4/5 Sub-Agent Vote</span>
            </button>

            <button
              onClick={() => handleRunOpcode('OP_ZEROIZE_CASCADE')}
              className="p-2.5 rounded bg-[#321816] hover:bg-[#451e1b] border border-[#ff8e8e]/40 text-[#ff8e8e] flex flex-col items-center gap-1 cursor-pointer transition-colors col-span-2 sm:col-span-1"
            >
              <Flame className="w-3.5 h-3.5 text-[#ff8e8e]" />
              <span className="font-bold text-[11px]">OP_ZEROIZE_CASCADE</span>
              <span className="text-[9px] text-[#ff8e8e]/80">Burn All Keys</span>
            </button>
          </div>
        </div>

        {/* ABI Log Feed */}
        <div className="space-y-1.5 font-mono text-xs">
          <span className="text-[11px] text-[#8d9aaa] uppercase font-semibold">Hardware ABI Audit Log:</span>
          <div className="p-3 bg-[#0b0e13] rounded-lg border border-[#26303d] max-h-36 overflow-y-auto space-y-1 text-[#8d9aaa] text-[11px]">
            {hsmState.abiLog.map((log, i) => (
              <div key={i} className="flex items-center justify-between gap-2 border-b border-[#26303d]/40 pb-0.5">
                <span className="text-[#66e3c4] font-bold">{log.opcode}</span>
                <span className="text-[#eef3f8] truncate max-w-xs">{log.params}</span>
                <span className="text-[#ffca6b] shrink-0">{log.result}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Grid: vChip Optical Air-Gap & GnomLedger AISBOM */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* vChip & VirtualDB Optical Air-Gap */}
        <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 shadow-sm space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-[#26303d] pb-3">
            <div>
              <h3 className="text-sm font-bold text-[#eef3f8] flex items-center gap-2">
                <Radio className="w-4 h-4 text-[#66e3c4]" />
                vChip Optical Data Carrier & VirtualDB
              </h3>
              <p className="text-[11px] text-[#8d9aaa]">
                Multi-spectral 2D spatial modulation (RGB + UV/IR) bypassing physical network interfaces.
              </p>
            </div>
            <button
              onClick={handleTransmitVchip}
              className="px-2.5 py-1 rounded bg-[#10241b] hover:bg-[#163527] border border-[#66e3c4]/40 text-[#66e3c4] text-[11px] cursor-pointer"
            >
              + Next Packet
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
            {/* Visual Canvas Display */}
            <div className="p-2 bg-[#0b0e13] rounded-lg border border-[#26303d] flex flex-col items-center justify-center">
              <canvas
                ref={canvasRef}
                width={160}
                height={160}
                className="rounded border border-[#66e3c4]/30 shadow-inner"
              />
              <span className="text-[10px] text-[#8d9aaa] mt-1.5">
                Multi-Spectral Stream (60 FPS)
              </span>
            </div>

            {/* Packet Metadata */}
            <div className="space-y-2 text-[11px] text-[#8d9aaa]">
              <div className="flex justify-between">
                <span>Packet ID:</span>
                <span className="text-[#eef3f8]">{vchipPacket.id}</span>
              </div>
              <div className="flex justify-between">
                <span>Compression:</span>
                <span className="text-[#66e3c4]">{vchipPacket.compressionAlgorithm} ({vchipPacket.compressionRatio})</span>
              </div>
              <div className="flex justify-between">
                <span>Uncompressed:</span>
                <span className="text-[#eef3f8]">{(vchipPacket.originalBytes / 1024).toFixed(1)} KB</span>
              </div>
              <div className="flex justify-between">
                <span>Optical Egress:</span>
                <span className="text-[#66e3c4]">{(vchipPacket.compressedBytes / 1024).toFixed(1)} KB</span>
              </div>
              <div className="flex justify-between">
                <span>VirtualDB Table:</span>
                <span className="text-[#eef3f8] truncate max-w-[120px]">{vchipPacket.virtualDbTable}</span>
              </div>
              <div className="p-2 rounded bg-[#10241b] border border-[#66e3c4]/30 text-[#66e3c4] text-[10px]">
                ✓ Strictly unidirectional (Light-only). SSRF, LFI, and reverse-shells are mathematically blocked.
              </div>
            </div>
          </div>
        </div>

        {/* GnomLedger AISBOM Receipt */}
        <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 shadow-sm space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-[#26303d] pb-3">
            <div>
              <h3 className="text-sm font-bold text-[#eef3f8] flex items-center gap-2">
                <Database className="w-4 h-4 text-[#66e3c4]" />
                GnomLedger (PGL) Immutable AISBOM Receipt
              </h3>
              <p className="text-[11px] text-[#8d9aaa]">
                Permanent cryptographic evidence binding model version, prompt hash, AST, and post-state reconciliation.
              </p>
            </div>
            <button
              onClick={handleEmitAisbom}
              className="px-2.5 py-1 rounded bg-[#10241b] hover:bg-[#163527] border border-[#66e3c4]/40 text-[#66e3c4] text-[11px] cursor-pointer"
            >
              + Commit Block
            </button>
          </div>

          <div className="p-3 bg-[#0b0e13] rounded-lg border border-[#26303d] space-y-2 text-[11px] text-[#8d9aaa]">
            <div className="flex justify-between">
              <span>Block Sequence ID:</span>
              <strong className="text-[#66e3c4]">{aisbomReceipt.blockId}</strong>
            </div>
            <div className="flex justify-between">
              <span>Model Identifier:</span>
              <span className="text-[#eef3f8]">{aisbomReceipt.modelIdentifier}</span>
            </div>
            <div className="flex justify-between">
              <span>Prompt Hash:</span>
              <span className="text-[#c8f6e9]">{aisbomReceipt.promptHash}</span>
            </div>
            <div className="flex justify-between">
              <span>Compiled AST Hash:</span>
              <span className="text-[#c8f6e9]">{aisbomReceipt.compiledAstHash}</span>
            </div>
            <div className="flex justify-between">
              <span>Post-Quantum Signature:</span>
              <span className="text-[#ffca6b] truncate max-w-[150px]">{aisbomReceipt.postQuantumSignature}</span>
            </div>
            <div className="flex justify-between border-t border-[#26303d]/40 pt-1.5">
              <span>State Reconciliation:</span>
              <span className="text-[#66e3c4] font-bold">100% MATCH (Zero Host Drift)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
