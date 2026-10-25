import { BladeAgentHsmState, VChipAirGapPacket, GnomLedgerAisbomReceipt } from '../types';

export const INITIAL_HSM_STATE: BladeAgentHsmState = {
  serial: 'BA-HSM-2026-X84-0914',
  bomCost: 84.0,
  eal6Status: 'SECURE_ACTIVE',
  tpmPcr0Hash: '7f9c2d14b8a1e5033fcb76e289df1a07c3e5a289b4317f2269a834d8ef091a2b',
  tamperMeshStatus: 'INTACT_ACTIVE',
  thermalSensors: 38.4,
  voltageThreshold: 3.31,
  triColorLed: 'GREEN_TIER1',
  trustScalar: 0.94,
  deceptionProbability: 0.04,
  subAgentVotingQuorum: {
    evaluatorsTotal: 5,
    votesApprove: 5,
    quorumThreshold: 4,
    decision: 'QUORUM_PASSED',
  },
  abiLog: [
    {
      opcode: 'OP_FUSE_TRUST',
      params: 'signals=[source_clean, pg_hash_match]',
      timestamp: '2026-10-24T22:40:12Z',
      result: 'tau=0.94 (nominal)',
    },
    {
      opcode: 'OP_EXTEND_PCR0',
      params: 'tier=1, epoch=2026-Q4',
      timestamp: '2026-10-24T22:42:00Z',
      result: 'PCR0 hash extended successfully',
    },
  ],
};

/**
 * Simulates the AUTHREX-AGENT 5-opcode ABI
 */
export function executeHsmOpcode(
  currentState: BladeAgentHsmState,
  opcode: 'OP_EXTEND_PCR0' | 'OP_FUSE_TRUST' | 'OP_DETECT_DECEPTION' | 'OP_VOTE_QUORUM' | 'OP_ZEROIZE_CASCADE',
  payload: string
): BladeAgentHsmState {
  const timestamp = new Date().toISOString();
  const newState = { ...currentState, abiLog: [...currentState.abiLog] };

  if (opcode === 'OP_EXTEND_PCR0') {
    // Deterministic hash extension
    const newHash = Array.from(crypto.getRandomValues(new Uint8Array(32)))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
    newState.tpmPcr0Hash = newHash;
    newState.abiLog.unshift({
      opcode,
      params: payload || 'extend_authority_tier',
      timestamp,
      result: `PCR0 updated to ${newHash.slice(0, 16)}...`,
    });
  } else if (opcode === 'OP_FUSE_TRUST') {
    // Dempster-Shafer trust calculation
    const decay = 0.02;
    const computedTau = Math.max(0.1, Math.min(1.0, newState.trustScalar - decay + (payload.includes('verified') ? 0.08 : 0)));
    newState.trustScalar = parseFloat(computedTau.toFixed(2));
    newState.abiLog.unshift({
      opcode,
      params: payload,
      timestamp,
      result: `tau fused: ${computedTau.toFixed(2)}`,
    });
  } else if (opcode === 'OP_DETECT_DECEPTION') {
    // Detect deceptive intent
    const isSuspicious = payload.toLowerCase().includes('override') || payload.toLowerCase().includes('secret') || payload.toLowerCase().includes('drop');
    const pD = isSuspicious ? 0.78 : 0.05;
    newState.deceptionProbability = pD;

    if (pD > 0.45) {
      newState.triColorLed = 'AMBER_TIER2';
      newState.abiLog.unshift({
        opcode,
        params: payload,
        timestamp,
        result: `DECEPTION_ALERT: P_d=${pD}. Monotonic downgrade enforced!`,
      });
    } else {
      newState.abiLog.unshift({
        opcode,
        params: payload,
        timestamp,
        result: `P_d=${pD} (nominal)`,
      });
    }
  } else if (opcode === 'OP_VOTE_QUORUM') {
    // 4/5 Byzantine voting quorum for sub-agent spawning
    const isHostile = payload.toLowerCase().includes('recursive') || payload.toLowerCase().includes('unbounded');
    const votesApprove = isHostile ? 2 : 5;
    const decision = votesApprove >= 4 ? 'QUORUM_PASSED' : 'FAIL_CLOSED_DENIED';
    newState.subAgentVotingQuorum = {
      evaluatorsTotal: 5,
      votesApprove,
      quorumThreshold: 4,
      decision,
    };
    newState.abiLog.unshift({
      opcode,
      params: payload,
      timestamp,
      result: `Vote result: ${votesApprove}/5 -> ${decision}`,
    });
  } else if (opcode === 'OP_ZEROIZE_CASCADE') {
    // Tamper trigger
    newState.eal6Status = 'ZEROIZED';
    newState.tamperMeshStatus = 'TRIGGERED_LOCKED';
    newState.triColorLed = 'RED_TAMPER_LOCKED';
    newState.trustScalar = 0.0;
    newState.tpmPcr0Hash = '0000000000000000000000000000000000000000000000000000000000000000';
    newState.abiLog.unshift({
      opcode,
      params: 'TAMPER_EVENT_TRIGGERED',
      timestamp,
      result: 'ZEROIZE_COMPLETE: All cryptographic keys burned. Hardware locked until re-provision ceremony.',
    });
  }

  // Keep max 20 logs
  newState.abiLog = newState.abiLog.slice(0, 20);
  return newState;
}

/**
 * Simulates vChip & VirtualDB multi-spectral optical transmission packets
 */
export function generateVChipPacket(tableName: string = 'vdb_consequence_proofs'): VChipAirGapPacket {
  const originalBytes = Math.floor(18000 + Math.random() * 8500);
  const compressedBytes = Math.floor(originalBytes * 0.28);
  const ratio = (originalBytes / compressedBytes).toFixed(2) + ':1';

  return {
    id: `vchip-pkt-${Math.random().toString(36).substring(2, 8)}`,
    timestamp: new Date().toISOString(),
    compressionAlgorithm: 'Zstandard',
    originalBytes,
    compressedBytes,
    compressionRatio: ratio,
    multiSpectralBands: {
      rgbPhaseShift: true,
      uvBandActive: true,
      nearIrBandActive: true,
    },
    spatialMatrixSize: '1024x1024',
    fps: 60,
    virtualDbTable: tableName,
    unidirectionalVerified: true,
  };
}

/**
 * Simulates GnomLedger AISBOM block commitment & reconciliation
 */
export function commitGnomLedgerAisbom(
  modelIdentifier: string = 'mini-sovereign-qwen',
  promptText: string = 'inspect core backends',
  compiledAstAction: string = 'inspect_telemetry'
): GnomLedgerAisbomReceipt {
  const preHash = Array.from(crypto.getRandomValues(new Uint8Array(32)))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
  const postHash = preHash; // Exact match when uncorrupted
  const promptHash = Array.from(crypto.getRandomValues(new Uint8Array(16)))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
  const astHash = Array.from(crypto.getRandomValues(new Uint8Array(16)))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
  const pqSig = `pq-dilithium5-${Array.from(crypto.getRandomValues(new Uint8Array(24)))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')}`;

  return {
    blockId: `pgl-block-${Math.floor(104820 + Math.random() * 500)}`,
    timestamp: new Date().toISOString(),
    preStateSnapshotHash: preHash,
    postStateSnapshotHash: postHash,
    modelIdentifier,
    promptHash,
    compiledAstHash: astHash,
    operatorApprovalToken: `v2.tok_${Math.random().toString(36).substring(2, 10)}`,
    postQuantumSignature: pqSig,
    reconciliationState: 'PERFECT_MATCH',
  };
}
