// VirtualDB & vChip Software Silicon Types

export type TableName = 'accounts' | 'transactions' | 'component_passports' | 'airgap_tokens';

export interface ColumnSchema {
  name: string;
  type: 'UUID' | 'VARCHAR' | 'DECIMAL' | 'MERKLE_ROOT' | 'ED25519_KEY' | 'TIMESTAMP' | 'JSON' | 'INTEGER';
  isPrimary?: boolean;
  isIndex?: boolean;
  nullable?: boolean;
}

export interface TableRow {
  id: string;
  [key: string]: any;
}

export interface DatabaseTable {
  name: TableName;
  displayName: string;
  description: string;
  rowCount: number;
  columns: ColumnSchema[];
  rows: TableRow[];
  merkleStateRoot: string;
  lastRatchetedAt: string;
}

export type DatabaseBranch = 'main' | 'staging-hotfix' | 'dev-preview';

export interface BranchInfo {
  name: DatabaseBranch;
  description: string;
  parentBranch?: DatabaseBranch;
  createdAt: string;
  commitHash: string;
  isDurable: boolean;
  unmergedMutationsCount: number;
}

export interface QueryExecutionResult {
  query: string;
  executionTimeMicros: number;
  rowCount: number;
  stateRoot: string;
  columns: string[];
  rows: any[];
  executionPlan: {
    step: string;
    operator: string;
    costMicros: number;
    details: string;
  }[];
  timestamp: string;
  isError?: boolean;
  errorMessage?: string;
}

// LLM Context Bucketing & MiniQR Merkle Indexing Types
export interface LlmContextBucket {
  id: string;
  name: string;
  category: 'auth' | 'schemas' | 'telemetry' | 'routes' | 'runbooks';
  tokenCount: number;
  byteSize: number;
  sha256Hash: string;
  sampleContent: string;
  isTampered: boolean;
  tamperedContent?: string;
  description: string;
}

export interface MiniQrMerkleIndex {
  merkleRoot: string;
  totalTokens: number;
  bucketCount: number;
  cr3BudgetCeiling: number;
  ed25519Seal: string;
  activeBucketsManifest: string[];
  timestamp: string;
}

export interface McpGraphQlResolution {
  query: string;
  selectedBucketIds: string[];
  tokensIngested: number;
  tokensRawFullContext: number;
  tokenReductionPercent: number;
  resolutionLatencyMs: number;
  merkleVerificationMicros: number;
  verificationPassed: boolean;
  securityVerdict: 'VERIFIED_CLEAN' | 'HASH_VERIFICATION_FAILED';
  errorMessage?: string;
  resolvedData: {
    bucketId: string;
    name: string;
    tokens: number;
    sha256: string;
  }[];
}

// vChip Optical Air-Gap Gateway Types
export type OpticalFormat = 'chromatic_m4' | 'rmqr' | 'standard_qr';

export interface OpticalModule {
  x: number;
  y: number;
  color: 'K' | 'W' | 'C' | 'M'; // Black, White, Cyan, Magenta
  colorHex: string;
  type: 'finder' | 'timing' | 'alignment' | 'data';
  bits: string; // '00', '01', '10', '11'
  reflectance: {
    c: number;
    m: number;
    y: number;
    k: number;
  };
}

export interface MaterializedRecordPacket {
  recordId: string;
  tableName: TableName;
  originalJson: string;
  originalBytes: number;
  cborBytes: number;
  tansCompressedBytes: number;
  compressionRatio: number; // e.g. 2.13x
  stateRoot: string;
  ed25519Signature: string;
  opticalFormat: OpticalFormat;
  matrixSize: number; // e.g. 17
  modules: OpticalModule[][];
}

// Sovereign Storage Vault Capsule
export interface SovereignCapsule {
  id: string;
  title: string;
  category: 'Offline Wallet' | 'App License' | 'Merkle Anchor' | 'Hardware Passport';
  stateRoot: string;
  signerPublicKey: string;
  signature: string;
  payloadJson: string;
  byteSize: number;
  createdAt: string;
  verifiedOffline: boolean;
}
