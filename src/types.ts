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
