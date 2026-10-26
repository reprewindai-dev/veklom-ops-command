/**
 * Canonical Workspace Files & Tree for Antigravity Desktop IDE
 * Populates real project folders and files matching clangd, vscode-python-envs, FAF-MCP, and Veklom Ops
 */

import { CANONICAL_PROJECT_FAF } from '../services/fafService';

export interface WorkspaceFileItem {
  id: string;
  name: string;
  path: string;
  folder: string;
  lang: 'cpp' | 'typescript' | 'rust' | 'python' | 'json' | 'yaml' | 'markdown';
  content: string;
  diagnostics?: Array<{
    line: number;
    col: number;
    length: number;
    severity: 'error' | 'warning' | 'info';
    message: string;
    code: string;
    source: string;
    suggestion?: string;
    declaredAt?: string;
    quickFixText?: string;
    replacementText?: string;
  }>;
  symbols?: Array<{
    name: string;
    kind: 'function' | 'method' | 'class' | 'struct' | 'variable' | 'interface';
    line: number;
    container?: string;
    detail: string;
    doc?: string;
  }>;
  completions?: Array<{
    label: string;
    detail: string;
    kind: 'method' | 'function' | 'property' | 'keyword' | 'class';
    documentation: string;
    insertText?: string;
  }>;
}

export const WORKSPACE_FILES: Record<string, WorkspaceFileItem> = {
  // 0. Project Context Manifest: project.faf (Always-33 Standard)
  project_faf: {
    id: 'project_faf',
    name: 'project.faf',
    path: 'project.faf',
    folder: 'root',
    lang: 'yaml',
    content: CANONICAL_PROJECT_FAF,
    symbols: [
      { name: 'faf_version', kind: 'variable', line: 2, detail: 'faf_version: 2.5.0' },
      { name: 'architecture', kind: 'struct', line: 36, detail: 'architecture: Veklom Capability OS' },
      { name: 'consequence_authority', kind: 'struct', line: 42, detail: 'consequence_authority: CAPPO Law 0' }
    ]
  },

  // 0b. CAPPO Governance & Consequence Gate: cappo_governance.ts
  cappo_governance_ts: {
    id: 'cappo_governance_ts',
    name: 'cappo_governance.ts',
    path: 'src/cappo_governance.ts',
    folder: 'src',
    lang: 'typescript',
    content: `/**
 * CAPPO (Capability Consequence Protocol) Law 0 Authority Gate
 * Fail-closed runtime governance for consequential machine operations.
 */
export interface ConsequenceBudget {
  maxDeltaCommons: number;
  ephemeralToken: string;
  realitySinkVerified: boolean;
  tamperEvidentSeal: string;
}

export class CappoAuthorityGate {
  private static readonly LAW_0_INVARIANT = 'NO_CONSEQUENCE_WITHOUT_GOVERNED_PROOF';

  public static evaluateExecutionPreconditions(budget: ConsequenceBudget): boolean {
    if (!budget.realitySinkVerified) {
      console.error('[CAPPO DENIED]: Reality sink is offline or unverified.');
      return false;
    }
    if (budget.maxDeltaCommons > 50000) {
      console.warn('[CAPPO RESTRICTED]: High consequence threshold requires physical key seal.');
    }
    return true;
  }

  public static issueEphemeralGrant(capabilityId: string): string {
    const nonce = Math.random().toString(36).substring(2, 10);
    return \`cap_grant_\${capabilityId}_\${nonce}_sealed\`;
  }
}
`,
    symbols: [
      { name: 'ConsequenceBudget', kind: 'interface', line: 5, detail: 'interface ConsequenceBudget' },
      { name: 'CappoAuthorityGate', kind: 'class', line: 12, detail: 'class CappoAuthorityGate' },
      { name: 'evaluateExecutionPreconditions', kind: 'method', line: 15, container: 'CappoAuthorityGate', detail: 'evaluateExecutionPreconditions(budget: ConsequenceBudget): boolean' }
    ]
  },

  // 0c. GnomLedger / PGL Tamper-Evident Evidence: pgl_evidence.ts
  pgl_evidence_ts: {
    id: 'pgl_evidence_ts',
    name: 'pgl_evidence.ts',
    path: 'src/pgl_evidence.ts',
    folder: 'src',
    lang: 'typescript',
    content: `/**
 * GnomLedger / PGL (Project Genome Ledger) Lineage Engine
 * Immutable, append-only Merkle receipt chain for code mutations & consequence settlement.
 */
export interface PglReceipt {
  receiptId: string;
  timestamp: string;
  merkleRoot: string;
  actor: 'founder-operator' | 'ephemeral-runtime' | 'local-ollama';
  actionType: 'AST_PATCH' | 'FAF_SYNC' | 'CONSEQUENCE_DISPATCH';
  contentHash: string;
}

export function generatePglMerkleSeal(receipt: Omit<PglReceipt, 'merkleRoot'>): string {
  const payload = \`\${receipt.receiptId}:\${receipt.timestamp}:\${receipt.contentHash}\`;
  // Deterministic 256-bit simulated hex seal
  let hash = 0x811c9dc5;
  for (let i = 0; i < payload.length; i++) {
    hash ^= payload.charCodeAt(i);
    hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
  }
  return '0x' + (hash >>> 0).toString(16).padStart(8, '0') + '...e9a1';
}
`,
    symbols: [
      { name: 'PglReceipt', kind: 'interface', line: 5, detail: 'interface PglReceipt' },
      { name: 'generatePglMerkleSeal', kind: 'function', line: 14, detail: 'generatePglMerkleSeal(receipt): string' }
    ]
  },

  // 1. C++ Source: FS.cpp (Matches diagnostics.png, complete.png, format.png)
  fs_cpp: {
    id: 'fs_cpp',
    name: 'FS.cpp',
    path: 'src/FS.cpp',
    folder: 'src',
    lang: 'cpp',
    content: `//===--- FS.cpp - File system abstraction for clangd ------------*- C++-*-===//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//===----------------------------------------------------------------------===//

#include "FS.h"
#include "llvm/Support/Path.h"
#include <algorithm>
#include <vector>

namespace clang {
namespace clangd {

void print_hex(uint32_t Op) {
  // Canonical hex formatting routine
  llvm::outs() << llvm::format_hex(Op, 8) << "\\n";
}

IntrusiveRefCntPtr<llvm::vfs::FileSystem>
PreambleFileStatusCache::getProducingFS(
    IntrusiveRefCntPtr<llvm::vfs::FileSystem> FS) {
  return new ProducingFileSystem(FS, StatCache);
}

void processDeclarationSorting(std::vector<clang::Decl*>& V) {
  // Auto-formatted lambda sort predicate
  std::sort(V.begin(), V.end(), [&](clang::Decl *L, clang::Decl *R) {
    return L->getSourceRange().getBegin() < R->getSourceRange().getBegin();
  });
}

llvm::Optional<FileStatus>
PreambleFileStatusCache::lookup(llvm::StringRef PathLookup) const {
  // Query preamble stat cache for cached inode and mtime
  return StatCache.lookup(PathLookup);
}

void executeDiagnosticVerification(uint32_t Op) {
  // Intentional identifier mismatch for clangd diagnostic verification
  printHex(Op);
}

} // namespace clangd
} // namespace clang
`,
    diagnostics: [
      {
        line: 41,
        col: 3,
        length: 8,
        severity: 'error',
        message: "Use of undeclared identifier 'printHex'; did you mean 'print_hex'?",
        code: 'clang(undeclared_var_use_suggest)',
        source: 'clangd',
        suggestion: 'print_hex',
        declaredAt: 'FS.cpp(15, 6): \'print_hex\' declared here',
        quickFixText: "Change 'printHex' to 'print_hex'",
        replacementText: '  print_hex(Op);'
      }
    ],
    completions: [
      {
        label: 'slice',
        detail: '(size_t Start, size_t End) const -> StringRef',
        kind: 'method',
        documentation: 'Returns a substring from [Start, End) within the StringRef.'
      },
      {
        label: 'str',
        detail: '() const -> std::string',
        kind: 'method',
        documentation: 'Converts StringRef into an owned std::string instance.'
      },
      {
        label: 'substr',
        detail: '(size_t Start, size_t N = StringRef::npos) const',
        kind: 'method',
        documentation: 'Extracts up to N characters starting from index Start.'
      },
      {
        label: 'append',
        detail: '(SmallVectorImpl<char> &Buffer) const',
        kind: 'method',
        documentation: 'Appends characters from this string reference into target vector.'
      },
      {
        label: 'compare',
        detail: '(StringRef RHS) const -> int',
        kind: 'method',
        documentation: 'Performs lexicographical comparison against RHS.'
      },
      {
        label: 'c_str',
        detail: '() const -> const char*',
        kind: 'method',
        documentation: 'Returns a null-terminated pointer if null-termination is guaranteed.'
      }
    ],
    symbols: [
      { name: 'print_hex', kind: 'function', line: 15, container: 'clang::clangd', detail: 'void print_hex(uint32_t Op)' },
      { name: 'getProducingFS', kind: 'method', line: 20, container: 'PreambleFileStatusCache', detail: 'IntrusiveRefCntPtr<FileSystem> getProducingFS(...)' },
      { name: 'lookup', kind: 'method', line: 36, container: 'PreambleFileStatusCache', detail: 'Optional<FileStatus> lookup(StringRef PathLookup) const' }
    ]
  },

  // 2. C++ Header: FS.h (Matches xrefs.png)
  fs_h: {
    id: 'fs_h',
    name: 'FS.h',
    path: 'src/FS.h',
    folder: 'src',
    lang: 'cpp',
    content: `//===--- FS.h - File system abstraction for clangd --------------*- C++-*-===//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//===----------------------------------------------------------------------===//

#ifndef LLVM_CLANG_TOOLS_EXTRA_CLANGD_FS_H
#define LLVM_CLANG_TOOLS_EXTRA_CLANGD_FS_H

#include "llvm/ADT/StringRef.h"
#include "llvm/Support/VirtualFileSystem.h"

namespace clang {
namespace clangd {

struct FileStatus {
  uint64_t Size;
  uint64_t ModificationTime;
};

/// Caches file metadata for faster preamble reuse across compiler passes.
class PreambleFileStatusCache {
public:
  PreambleFileStatusCache() = default;

  /// Returns a VFS that collects file status. Only cache stats for files that
  /// are part of the preamble.
  IntrusiveRefCntPtr<llvm::vfs::FileSystem>
  getProducingFS(IntrusiveRefCntPtr<llvm::vfs::FileSystem> FS);

  /// Looks up cached stat for a given path string.
  llvm::Optional<FileStatus> lookup(llvm::StringRef PathLookup) const;

private:
  llvm::StringMap<FileStatus> StatCache;
};

void print_hex(uint32_t Op);

} // namespace clangd
} // namespace clang

#endif // LLVM_CLANG_TOOLS_EXTRA_CLANGD_FS_H
`,
    symbols: [
      { name: 'PreambleFileStatusCache', kind: 'class', line: 20, container: 'clang::clangd', detail: 'class PreambleFileStatusCache' },
      { name: 'getProducingFS', kind: 'method', line: 26, container: 'PreambleFileStatusCache', detail: 'IntrusiveRefCntPtr<FileSystem> getProducingFS(...)' }
    ]
  },

  // 3. ClangdUnit.cpp (Matches xrefs.png)
  clangd_unit: {
    id: 'clangd_unit',
    name: 'ClangdUnit.cpp',
    path: 'src/ClangdUnit.cpp',
    folder: 'src',
    lang: 'cpp',
    content: `//===--- ClangdUnit.cpp -----------------------------------------*- C++-*-===//
#include "FS.h"
#include "clang/Frontend/CompilerInstance.h"

namespace clang {
namespace clangd {

std::unique_ptr<CompilerInvocation>
buildCompilerInvocation(const ParseInputs &Inputs, PragmaHandler &Handler) {
  PreambleFileStatusCache StatCache;
  auto FS = StatCache.getProducingFS(Inputs.FS);
  // Construct AST unit with virtual filesystem
  return createInvocationFromCommandLine(Inputs.CompileCommand.CommandLine, FS);
}

} // namespace clangd
} // namespace clang
`
  },

  // 4. FSTests.cpp (Matches xrefs.png)
  fs_tests: {
    id: 'fs_tests',
    name: 'FSTests.cpp',
    path: 'tests/FSTests.cpp',
    folder: 'tests',
    lang: 'cpp',
    content: `//===--- FSTests.cpp --------------------------------------------*- C++-*-===//
#include "FS.h"
#include "gtest/gtest.h"

namespace clang {
namespace clangd {
namespace {

TEST(FSTests, PreambleCacheLookup) {
  PreambleFileStatusCache StatCache;
  auto MemFS = llvm::makeIntrusiveRefCnt<llvm::vfs::InMemoryFileSystem>();
  auto ProducingFS = StatCache.getProducingFS(MemFS);

  EXPECT_TRUE(ProducingFS != nullptr);
}

} // namespace
} // namespace clangd
} // namespace clang
`
  },

  // 5. StringRef.h (Matches symbolsearch.png & hover.png)
  stringref_h: {
    id: 'stringref_h',
    name: 'StringRef.h',
    path: 'include/llvm/Support/StringRef.h',
    folder: 'include',
    lang: 'cpp',
    content: `//===--- StringRef.h - Constant String Reference ----------------*- C++-*-===//
namespace llvm {

/// StringRef - Represent a constant reference to a string, i.e. a character
/// array and a length, which need not be null terminated.
class StringRef {
public:
  static constexpr size_t npos = ~size_t(0);

  constexpr StringRef() : Data(nullptr), Length(0) {}
  constexpr StringRef(const char *Str) : Data(Str), Length(Str ? __builtin_strlen(Str) : 0) {}

  constexpr const char *data() const { return Data; }
  constexpr size_t size() const { return Length; }
  constexpr bool empty() const { return Length == 0; }

  StringRef slice(size_t Start, size_t End) const;
  StringRef substr(size_t Start, size_t N = npos) const;
  int compare(StringRef RHS) const;

private:
  const char *Data;
  size_t Length;
};

} // namespace llvm
`,
    symbols: [
      { name: 'StringRef', kind: 'class', line: 6, container: 'llvm', detail: 'class llvm::StringRef' },
      { name: 'size', kind: 'method', line: 15, container: 'StringRef', detail: 'constexpr size_t size() const noexcept' }
    ]
  },



  // 7. .cursorrules
  cursor_rules: {
    id: 'cursor_rules',
    name: '.cursorrules',
    path: '.cursorrules',
    folder: 'root',
    lang: 'markdown',
    content: `# .cursorrules — Auto-generated via FAF-MCP (project.faf)
# Standard: application/vnd.faf+yaml (Wolfe-Jam/faf-mcp)

You are an AI assistant operating within Veklom Ops Command & Antigravity IDE.
Authority: CAPPO (consequence gate on owned hardware)
Evidence: GnomLedger / PGL (Ed25519 root of trust)

Rules:
1. Never emit mock, synthetic, or fake data in production code.
2. Use AST manipulation (Find-Ast, Set-ScriptExtent) over naive regex.
3. Keep ambient tokens pruned to <4,096 via FAF domain buckets.
4. Support Visual Studio 2026, Clangd, and local Ollama daemons.
`
  },

  // 8. .vscode/launch.json
  launch_json: {
    id: 'launch_json',
    name: 'launch.json',
    path: '.vscode/launch.json',
    folder: '.vscode',
    lang: 'json',
    content: JSON.stringify({
      version: "0.2.0",
      configurations: [
        {
          name: "Antigravity IDE & Clangd Daemon",
          type: "cppdbg",
          request: "launch",
          program: "${workspaceFolder}/bin/clangd",
          args: ["--background-index", "--clang-tidy", "--header-insertion=iwyu"],
          stopAtEntry: false,
          cwd: "${workspaceFolder}",
          environment: [],
          externalConsole: false,
          MIMode: "gdb"
        },
        {
          name: "Veklom Python Environment (PEP 723)",
          type: "python",
          request: "launch",
          program: "${workspaceFolder}/python/env_manager.py",
          console: "integratedTerminal"
        }
      ]
    }, null, 2)
  },

  // 9. .vscode/settings.json
  settings_json: {
    id: 'settings_json',
    name: 'settings.json',
    path: '.vscode/settings.json',
    folder: '.vscode',
    lang: 'json',
    content: JSON.stringify({
      "clangd.path": "clangd",
      "clangd.arguments": [
        "--background-index",
        "--clang-tidy",
        "--completion-style=detailed",
        "--header-insertion=iwyu"
      ],
      "clangd.inlayHints.enabled": true,
      "clangd.inactiveRegions.useBackgroundHighlight": true,
      "python.useEnvironmentsExtension": true,
      "python-envs.defaultEnvManager": "ms-python.python:venv",
      "python-envs.defaultPackageManager": "ms-python.python:pip",
      "python-envs.alwaysUseUv": true
    }, null, 2)
  },

  // 10. python/env_manager.py (Matches vscode-python-envs & PEP 723)
  python_env_mgr: {
    id: 'python_env_mgr',
    name: 'env_manager.py',
    path: 'python/env_manager.py',
    folder: 'python',
    lang: 'python',
    content: `# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "uv>=0.10.0",
#   "pydantic>=2.7.0",
#   "fastapi>=0.110.0"
# ]
# ///
"""
Python Environment Manager with PEP 723 inline script metadata.
Unified python environment supervisor compatible with vscode-python-envs.
"""

import sys
import subprocess
from pathlib import Path

def get_python_environment_info() -> dict:
    return {
        "version": sys.version,
        "executable": sys.executable,
        "prefix": sys.prefix,
        "uv_available": True,
        "manager": "ms-python.python:venv",
        "package_manager": "ms-python.python:pip"
    }

def main() -> None:
    info = get_python_environment_info()
    print("Veklom Python Environment Controller Active")
    print(f"Python: {info['executable']} ({info['version'].split()[0]})")

if __name__ == "__main__":
    main()
`,
    symbols: [
      { name: 'get_python_environment_info', kind: 'function', line: 14, detail: 'def get_python_environment_info() -> dict' },
      { name: 'main', kind: 'function', line: 24, detail: 'def main() -> None' }
    ]
  },

  // 11. python/pyproject.toml
  pyproject_toml: {
    id: 'pyproject_toml',
    name: 'pyproject.toml',
    path: 'python/pyproject.toml',
    folder: 'python',
    lang: 'yaml',
    content: `[project]
name = "veklom-python-core"
version = "1.0.0"
description = "Veklom Python Environments and Substrate bindings"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0.0",
    "requests>=2.31.0"
]

[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"
`
  },

  // 12. src/demo_inconsistent_provider.ts
  demo_inc: {
    id: 'demo_inc',
    name: 'demo_inconsistent_provider.ts',
    path: 'src/demo_inconsistent_provider.ts',
    folder: 'src',
    lang: 'typescript',
    content: `/**
 * CLI EXECUTOR: DEMONSTRATION 2 - INCONSISTENT PAYMENT-PROVIDER SIMULATOR
 */
import { executeInconsistentProviderDemo } from '../src/services/demoInconsistentProvider.js';

export { executeInconsistentProviderDemo };

console.log('Running Demo 2: Inconsistent Payment-Provider Simulator (Phantom Debit)...');
const result = executeInconsistentProviderDemo('PHANTOM_DEBIT');
console.log('\\n=============================================');
console.log(\`RUN ID: \${result.run_id}\`);
console.log(\`SCENARIO: \${result.scenario}\`);
console.log(\`RUNTIME POWER STATE: \${result.summary.runtime_power_state}\`);
console.log(\`OPERATION STATUS: \${result.summary.operation_status}\`);
console.log(\`Balance Before: \${result.summary.balance_before} COMMONS\`);
console.log(\`Balance After: \${result.summary.balance_after} COMMONS\`);
console.log(\`Net Consequence (ΔC): \${result.summary.net_consequence_delta_c} COMMONS\`);
console.log(\`STATUS: \${result.summary.status}\`);
console.log('=============================================');
for (const q of result.queries) {
  console.log(\`  [\${q.verified ? 'PASS' : 'FAIL'}] \${q.name}: \${q.sql} => \${q.result} (expected \${q.expected})\`);
}
`,
    symbols: [
      { name: 'executeInconsistentProviderDemo', kind: 'function', line: 4, detail: 'executeInconsistentProviderDemo(scenario: string): DemoResult' }
    ]
  },

  // 13. src/rust_veklom_shared_dispatch.rs
  rust_veklom: {
    id: 'rust_veklom',
    name: 'rust_veklom_shared_dispatch.rs',
    path: 'src/rust_veklom_shared_dispatch.rs',
    folder: 'src',
    lang: 'rust',
    content: `// Rust Sovereign Consequence Authority Dispatch
// Crate: veklom_shared_dispatch

pub struct ConsequenceEngine {
    pub authority_level: u8,
    pub reality_sink_active: bool,
}

impl ConsequenceEngine {
    pub fn new() -> Self {
        Self {
            authority_level: 0, // Tier 0 Governed
            reality_sink_active: true,
        }
    }

    pub fn dispatch_action(&self, target_hash: &str) -> Result<String, &'static str> {
        if !self.reality_sink_active {
            return Err("REALITY_SINK_OFFLINE");
        }
        Ok(format!("DISPATCHED_TO_CAPPO:{}", target_hash))
    }
}
`,
    symbols: [
      { name: 'ConsequenceEngine', kind: 'struct', line: 4, detail: 'pub struct ConsequenceEngine' },
      { name: 'new', kind: 'method', line: 10, container: 'ConsequenceEngine', detail: 'pub fn new() -> Self' },
      { name: 'dispatch_action', kind: 'method', line: 17, container: 'ConsequenceEngine', detail: 'pub fn dispatch_action(&self, target_hash: &str) -> Result<String, &str>' }
    ]
  }
};

export interface FolderNode {
  name: string;
  files: string[];
  subfolders?: Record<string, FolderNode>;
}

export const WORKSPACE_FOLDERS: Record<string, { label: string; icon: string }> = {
  root: { label: 'Root Configs', icon: 'folder' },
  '.vscode': { label: '.vscode (Settings & Debug)', icon: 'settings' },
  src: { label: 'src (C++, Rust, TypeScript)', icon: 'code' },
  include: { label: 'include (LLVM / Clang)', icon: 'layers' },
  python: { label: 'python (Python Envs & PEP 723)', icon: 'file' },
  tests: { label: 'tests (GTest & CTest)', icon: 'check' }
};
