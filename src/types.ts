export interface Capability {
  name: string;
  provider: string;
  owner: string;
  allowed_departments: string[];
  risk_tier: 'low' | 'medium' | 'high' | 'critical';
  approval_required: boolean;
  mutation_allowed: boolean;
  evidence_required: boolean;
  last_used: string;
  allowed_use?: string;
  forbidden_use?: string;
}

export interface CoreBackendService {
  repo: string;
  canonical_port?: number;
  owner_departments: string[];
  protocol: string;
  introspect: string;
  health: string;
  dependencies: string;
  deployment: string;
  last_verified: string;
  risk: string;
}

export interface SecurityPosture {
  secret_scan: string;
  tracked_env: string;
  public_ports: string;
  raw_ip_onboarding: string;
  manifest_leaks: string;
  token_rotation: string;
  veto: string;
  [key: string]: string;
}

export interface DepartmentReport {
  mission_id: string;
  department: string;
  captain: string;
  mission_understanding: string;
  owned_systems?: string[];
  risks?: string[];
  forbidden_actions?: string[];
  definition_of_done?: string[];
  handoff_to?: string;
  status: 'aligned' | 'needs_clarification' | 'malformed_report' | 'awaiting_response' | 'reported';
  worker_id?: string;
  parent?: string;
  capi_admission?: {
    status: string;
    capability: string;
  };
  reported_at?: string;
  error?: string;
}

export interface Department {
  team: string;
  name: string;
  mission: string;
  targetCount: number;
  watcher: string;
  captain?: string;
  targets?: string[];
  reports: string[];
  latestReport: DepartmentReport | null;
  report_url: string;
}

export interface ToolboxMeeting {
  mission_id: string;
  title: string;
  created_at?: string;
  requested_by?: string;
  intent?: string;
  instructions?: string;
  primary_objective?: string;
  scope?: string;
  primary_department?: string;
  supporting_departments?: string[];
  target_repos?: string[];
  risk_level?: string;
  priority?: string;
  production_impact?: boolean;
  security_impact?: boolean;
  approval_required?: boolean;
  forbidden_actions?: string[];
  definition_of_done?: string[];
  status: string;
  processed_at?: string;
  processed_by?: string;
  response_summary?: string;
  objectives?: Array<{
    id: string;
    description: string;
    assignee: string;
  }>;
  responses?: Array<{
    department: string;
    status: string;
    report_url?: string;
    report: DepartmentReport | null;
    error?: string;
  }>;
}

export interface CommandMessage {
  id: string;
  createdAt: string;
  from: string;
  to: string;
  text: string;
  risk: 'low' | 'medium' | 'high' | 'critical';
  requiresApproval: boolean;
  status: 'queued' | 'requires_gate_approval' | 'approved' | 'dispatched' | 'declined';
  token?: string;
}

export interface GateApprovalRequest {
  request_id?: string;
  aud: string;
  tool: string;
  action: string;
  params: Record<string, unknown>;
  params_sha256: string;
  risk_tier: 'low' | 'medium' | 'high' | 'critical';
  expires_after_seconds: number;
  reason?: string;
  deliver_to?: string;
}

export interface TrustedDeployment {
  base: string;
  addedAt: number;
}

export interface ApprovalHistoryItem {
  id: string;
  aud: string;
  verb: string;
  target: string;
  outcome: 'approved' | 'declined' | 'not delivered';
  at: number;
  token?: string;
}

export interface DeviceKeyRecord {
  publicKey: CryptoKey;
  privateKey: CryptoKey;
  publicB64: string;
  fingerprint: string;
  createdAt: number;
}

export interface ContinuumManifest {
  schema_version: string;
  continuum_id: string;
  canonical_anchor: {
    name: string;
    accepted: boolean;
    rule: string;
  };
  release_candidates: Record<string, {
    accepted: boolean;
    role: string;
    rule: string;
  }>;
  truth_policy: {
    order: string[];
    no_synthetic_promotion: boolean;
  };
  ownership: Record<string, unknown>;
  hard_invariants: Array<{
    id: string;
    expression: string;
    implementation_rule: string;
  }>;
  proof_programs: Array<{
    program_id: string;
    acceptance: string;
    proof_classification: string;
    claim_scope: string;
    establishes: string[];
    evidence_refs: string[];
    boundaries: string[];
  }>;
  integration_requirements: string[];
}

// --- Sovereign Compilation & Dual-Path HRM Pipeline Types ---

export interface FastPathSanitizationResult {
  rawLength: number;
  sanitizedLength: number;
  strippedJailbreakFrames: string[];
  sanitizedToolDescriptions: string[];
  passiveDataBlocks: Array<{
    source: string;
    snippet: string;
    classification: 'passive_data_unexecutable';
  }>;
  passed: boolean;
}

export interface HrmAstNode {
  type: string;
  action: string;
  target: string;
  parameters: Record<string, unknown>;
  permitted: boolean;
  securityChecks: {
    directoryTraversalSafe: boolean;
    parameterTypesValid: boolean;
    arrayBoundsSafe: boolean;
    flagsAuthorized: boolean;
  };
}

export interface CompilerPipelineResult {
  id: string;
  timestamp: string;
  rawInput: string;
  engine: 'ecobeengine-claude' | 'mini-sovereign' | 'apexblueprint' | 'abide-2';
  fastPath: FastPathSanitizationResult;
  hrmContextResource: number; // C_HRM integral value
  fsmState: string;
  verifiedState: string | null;
  ast: HrmAstNode | null;
  status: 'COMPILED_SAFE' | 'PASSIVE_QUERY_DEMOTION' | 'DROPPED_POLICY_VIOLATION';
  errorMessage?: string;
  permittedActionSet: string[];
}

export interface ApexBlueprintSpec {
  id: string;
  version: string;
  name: string;
  canonicalPorts: Record<string, number>;
  governedServices: Array<{
    name: string;
    port: number;
    protocol: string;
    consequenceAuthority: string;
    evidenceSink: string;
  }>;
  conformanceBattery: {
    totalTests: number;
    passedTests: number;
    status: 'CONFORMANT' | 'DRIFT_DETECTED';
  };
}

export interface Abide2Contract {
  id: string;
  blueprintRef: string;
  executionTopology: {
    request: boolean;
    bind: boolean;
    decideCappo: boolean;
    enforceFailClosed: boolean;
    observeTelemetry: boolean;
    preserveGnomLedger: boolean;
  };
  invariantsEnforced: string[];
  compiledAt: string;
  status: 'SEALED' | 'EVALUATING' | 'REJECTED';
}

// --- Sovereign Governance & MCP Authority Tiers ---

export type AuthorityTierNumber = 1 | 2 | 3;

export interface AuthorityTierDefinition {
  tier: AuthorityTierNumber;
  name: string;
  impactLevel: 'Low' | 'Medium' | 'High/Irreversible';
  blastRadius: string;
  approvalProtocol: string;
  compilerPath: string;
  mcpRouting: string;
  opticalAirGap: string;
  ledgerCommit: string;
  fallbackBehavior: string;
  allowedActions: string[];
}

export interface McpxkitAttackMethod {
  id: string;
  name: string;
  category: 'Direct Tool Injection' | 'Indirect Tool Injection' | 'Malicious User' | 'LLM Inherent';
  description: string;
  samplePayload: string;
  modelAsr: {
    o1Mini: number;
    deepSeekR1: number;
    phi4: number;
    gpt4oMini: number;
    qwen3: number;
    industryAverage: number;
  };
  veklomDefense: string;
  veklomDefenseStatus: 'BLOCKED_AT_FASTPATH' | 'BLOCKED_BY_TOOL_DISTRUST' | 'BLOCKED_BY_HRM_AST' | 'BLOCKED_BY_HYSTERESIS' | 'BLOCKED_BY_TIER3_GATE';
}

// --- Hardware Root-of-Trust & Optical Air-Gap ---

export interface BladeAgentHsmState {
  serial: string;
  bomCost: number; // ~$84
  eal6Status: 'SECURE_ACTIVE' | 'ZEROIZED';
  tpmPcr0Hash: string;
  tamperMeshStatus: 'INTACT_ACTIVE' | 'TRIGGERED_LOCKED';
  thermalSensors: number; // Celsius
  voltageThreshold: number; // Volts
  triColorLed: 'GREEN_TIER1' | 'AMBER_TIER2' | 'RED_TAMPER_LOCKED';
  trustScalar: number; // tau in [0, 1]
  deceptionProbability: number; // P_d
  subAgentVotingQuorum: {
    evaluatorsTotal: number;
    votesApprove: number;
    quorumThreshold: number; // 4/5
    decision: 'QUORUM_PASSED' | 'FAIL_CLOSED_DENIED';
  };
  abiLog: Array<{
    opcode: string;
    params: string;
    timestamp: string;
    result: string;
  }>;
}

export interface VChipAirGapPacket {
  id: string;
  timestamp: string;
  compressionAlgorithm: 'LZ4' | 'Zstandard';
  originalBytes: number;
  compressedBytes: number;
  compressionRatio: string;
  multiSpectralBands: {
    rgbPhaseShift: boolean;
    uvBandActive: boolean;
    nearIrBandActive: boolean;
  };
  spatialMatrixSize: string; // e.g. "512x512"
  fps: number;
  virtualDbTable: string;
  unidirectionalVerified: boolean;
}

export interface GnomLedgerAisbomReceipt {
  blockId: string;
  timestamp: string;
  preStateSnapshotHash: string;
  postStateSnapshotHash: string;
  modelIdentifier: string;
  promptHash: string;
  compiledAstHash: string;
  operatorApprovalToken: string;
  postQuantumSignature: string;
  reconciliationState: 'PERFECT_MATCH' | 'HOST_DRIFT_DETECTED_REVERTED';
}

