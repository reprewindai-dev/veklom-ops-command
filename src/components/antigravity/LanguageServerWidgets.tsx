import React, { useState } from 'react';
import {
  Sparkles,
  AlertTriangle,
  Lightbulb,
  Search,
  Check,
  FileCode,
  Layers,
  Code,
  ExternalLink,
  X,
  ChevronRight,
  Terminal,
  Zap,
  Box
} from 'lucide-react';
import { WORKSPACE_FILES, WorkspaceFileItem } from '../../data/workspaceFiles';

// ==========================================
// 1. COMPLETION WIDGET (Matches complete.png)
// ==========================================
interface AutocompleteWidgetProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (item: { label: string; detail: string; documentation: string }) => void;
  activeFile: WorkspaceFileItem;
}

export function AutocompleteWidget({ isOpen, onClose, onSelect, activeFile }: AutocompleteWidgetProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  if (!isOpen) return null;

  const items = activeFile.completions || [
    { label: 'slice', detail: '(size_t Start, size_t End) const  StringRef', kind: 'method', documentation: 'Returns a substring from [Start, End) within the StringRef.' },
    { label: 'str', detail: '() const  std::string', kind: 'method', documentation: 'Converts StringRef into an owned std::string instance.' },
    { label: 'substr', detail: '(size_t Start, size_t N = StringRef::npos) const', kind: 'method', documentation: 'Extracts up to N characters starting from index Start.' },
    { label: 'append', detail: '(SmallVectorImpl<char> &Buffer) const', kind: 'method', documentation: 'Appends characters from this string reference into target vector.' },
    { label: 'assign', detail: '(StringRef RHS) const', kind: 'method', documentation: 'Assigns new string contents to reference buffer.' },
    { label: 'c_str', detail: '() const  const char*', kind: 'method', documentation: 'Returns a null-terminated pointer if null-termination is guaranteed.' },
    { label: 'compare', detail: '(StringRef RHS) const', kind: 'method', documentation: 'Performs lexicographical comparison against RHS.' },
    { label: 'compare_lower', detail: '(StringRef RHS) const', kind: 'method', documentation: 'Case-insensitive lexicographical comparison against RHS.' }
  ];

  const currentItem = items[selectedIndex] || items[0];

  return (
    <div className="absolute top-28 left-48 z-40 flex shadow-2xl rounded border border-[#2b3345] bg-[#161a22] text-[#e6edf3] font-mono text-xs overflow-hidden select-none animate-fadeIn">
      {/* Suggestions List */}
      <div className="w-80 max-h-64 overflow-y-auto divide-y divide-[#1e2330]">
        {items.map((it, idx) => {
          const isSelected = selectedIndex === idx;
          return (
            <div
              key={it.label}
              onClick={() => onSelect(it)}
              onMouseEnter={() => setSelectedIndex(idx)}
              className={`flex items-center justify-between px-2.5 py-1.5 cursor-pointer transition-colors ${
                isSelected ? 'bg-[#094771] text-white' : 'hover:bg-[#1f2633] text-[#c9d1d9]'
              }`}
            >
              <div className="flex items-center gap-2 truncate">
                <div className="w-3.5 h-3.5 flex items-center justify-center text-[#d2a8ff]">
                  <Box className="w-3 h-3 text-[#bc8cff]" />
                </div>
                <span className="font-semibold">{it.label}</span>
                <span className="text-[11px] text-[#8b949e] truncate">{it.detail.split('->')[0]}</span>
              </div>
              <span className="text-[10px] text-[#58a6ff] shrink-0 font-medium ml-2">
                {it.detail.includes('->') ? it.detail.split('->')[1].trim() : 'const'}
              </span>
            </div>
          );
        })}
      </div>

      {/* Side Documentation Card */}
      <div className="w-72 bg-[#0d1117] border-l border-[#262f40] p-3 flex flex-col justify-between text-[11px] leading-relaxed">
        <div>
          <div className="text-white font-bold font-mono text-xs pb-1 border-b border-[#21262d]">
            {currentItem.label}
          </div>
          <div className="text-[#a5d6ff] font-mono text-[10px] mt-1.5">
            {currentItem.detail}
          </div>
          <div className="text-[#8b949e] mt-2">
            {currentItem.documentation}
          </div>
        </div>
        <div className="pt-2 border-t border-[#1e232d] flex items-center justify-between text-[10px] text-[#6e7681]">
          <span>Press Enter or Tab to select</span>
          <button onClick={onClose} className="hover:text-white">Esc</button>
        </div>
      </div>
    </div>
  );
}

// ==========================================
// 2. DIAGNOSTICS & QUICK FIX (Matches diagnostics.png)
// ==========================================
interface DiagnosticHoverCardProps {
  diagnostic: {
    message: string;
    code: string;
    source: string;
    declaredAt?: string;
    quickFixText?: string;
  };
  onApplyQuickFix: () => void;
  onClose: () => void;
}

export function DiagnosticHoverCard({ diagnostic, onApplyQuickFix, onClose }: DiagnosticHoverCardProps) {
  return (
    <div className="absolute top-36 left-28 z-40 w-[540px] bg-[#1e222b] border border-[#3b4458] rounded-lg shadow-2xl p-3 font-sans text-xs text-[#e6edf3] animate-fadeIn">
      <div className="flex items-start justify-between">
        <div className="leading-relaxed">
          <p className="font-mono text-white text-[12px]">
            {diagnostic.message}
          </p>
          <span className="text-[#7d8590] text-[11px] font-mono">
            {diagnostic.code}
          </span>
          {diagnostic.declaredAt && (
            <p className="text-[#58a6ff] text-[11px] font-mono mt-1">
              {diagnostic.declaredAt}
            </p>
          )}
        </div>
        <button onClick={onClose} className="text-[#7d8590] hover:text-white p-1">
          <X size={14} />
        </button>
      </div>

      <div className="flex items-center gap-4 mt-3 pt-2 border-t border-[#2d3545]">
        <button
          onClick={onApplyQuickFix}
          className="text-[#58a6ff] hover:text-[#79c0ff] font-medium flex items-center gap-1 hover:underline"
        >
          <Zap size={12} className="text-[#e3b341]" />
          <span>Quick Fix: {diagnostic.quickFixText || "Apply fix"}</span>
        </button>
        <button className="text-[#7d8590] hover:text-[#c9d1d9]">
          Peek Problem
        </button>
      </div>
    </div>
  );
}

// ==========================================
// 3. HOVER TOOLTIP (Matches hover.png)
// ==========================================
interface SymbolHoverCardProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SymbolHoverCard({ isOpen, onClose }: SymbolHoverCardProps) {
  if (!isOpen) return null;

  return (
    <div className="absolute top-20 left-64 z-40 w-[560px] bg-[#161a22] border border-[#2d3748] rounded-xl shadow-2xl p-4 font-mono text-xs text-[#e6edf3] animate-fadeIn">
      <div className="flex items-center justify-between pb-2 border-b border-[#242c3d]">
        <div className="flex items-center gap-2">
          <span className="px-1.5 py-0.5 rounded bg-[#21262d] text-[#e3b341] text-[10px] font-bold">
            instance-method
          </span>
          <span className="text-white font-bold text-sm">size</span>
        </div>
        <button onClick={onClose} className="text-[#7d8590] hover:text-white">
          <X size={14} />
        </button>
      </div>

      <div className="mt-2 space-y-2 text-[11px] leading-relaxed">
        <div className="flex items-center gap-1.5 text-[#58a6ff]">
          <span>→</span>
          <span className="font-semibold">std::basic_string&lt;char&gt;::size_type</span>
          <span className="text-[#8b949e]">(aka unsigned long)</span>
        </div>

        <div className="text-[#c9d1d9] font-sans">
          <span className="font-semibold text-white">Capacity:</span>
          <p className="mt-0.5 text-[#8b949e]">
            Returns the number of characters in the string, not including any null-termination.
          </p>
        </div>

        <div className="bg-[#0d1117] p-2.5 rounded-lg border border-[#1e2330] text-[#7ee787]">
          <span className="text-[#8b949e]">// In basic_string&lt;char&gt;</span>
          <br />
          <span className="text-[#ff7b72]">public:</span> std::basic_string&lt;char&gt;::size_type{' '}
          <span className="text-[#d2a8ff]">size</span>() <span className="text-[#ff7b72]">const noexcept</span>
        </div>
      </div>
    </div>
  );
}

// ==========================================
// 4. LIGHTBULB CODE ACTIONS (Matches extract.png & include.png)
// ==========================================
interface LightbulbMenuProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectAction: (actionText: string) => void;
}

export function LightbulbMenu({ isOpen, onClose, onSelectAction }: LightbulbMenuProps) {
  if (!isOpen) return null;

  return (
    <div className="absolute top-24 left-20 z-40 w-80 bg-[#161a22] border border-[#2b3342] rounded-xl shadow-2xl overflow-hidden font-sans text-xs select-none animate-fadeIn">
      <div className="px-3 py-1.5 bg-[#0e1116] border-b border-[#21252d] text-[10px] font-bold uppercase tracking-wider text-[#8b949e] flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Lightbulb className="w-3 h-3 text-amber-400 fill-amber-400" />
          <span>Quick Fix & Refactor Actions</span>
        </div>
        <button onClick={onClose} className="hover:text-white">✕</button>
      </div>

      <div className="divide-y divide-[#1e232d]">
        <button
          onClick={() => onSelectAction('Extract subexpression to variable')}
          className="w-full text-left px-3 py-2 bg-[#1f6feb]/20 hover:bg-[#1f6feb]/30 text-white font-medium flex items-center gap-2 transition"
        >
          <Sparkles className="w-3.5 h-3.5 text-[#58a6ff]" />
          <span>Extract subexpression to variable</span>
        </button>

        <button
          onClick={() => onSelectAction('Add include "llvm/Testing/Support/Annotations.h"')}
          className="w-full text-left px-3 py-2 hover:bg-[#1c212a] text-[#c9d1d9] flex items-center gap-2 transition"
        >
          <Code className="w-3.5 h-3.5 text-[#7ee787]" />
          <span>Add include "llvm/Testing/Support/Annotations.h" for symbol llvm::Annotations</span>
        </button>

        <button
          onClick={() => onSelectAction('Replace printHex with print_hex')}
          className="w-full text-left px-3 py-2 hover:bg-[#1c212a] text-[#c9d1d9] flex items-center gap-2 transition"
        >
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span>Change 'printHex' to 'print_hex'</span>
        </button>

        <button
          onClick={() => onSelectAction('Format Document')}
          className="w-full text-left px-3 py-2 hover:bg-[#1c212a] text-[#8b949e] flex items-center gap-2 transition"
        >
          <Check className="w-3.5 h-3.5 text-[#388bfd]" />
          <span>Format selection with Clang-Format</span>
        </button>
      </div>
    </div>
  );
}

// ==========================================
// 5. SYMBOL SEARCH / GO TO SYMBOL (Matches symbolsearch.png)
// ==========================================
interface SymbolSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectSymbol: (symbol: any) => void;
}

export function SymbolSearchModal({ isOpen, onClose, onSelectSymbol }: SymbolSearchModalProps) {
  const [query, setQuery] = useState('#StringR');

  if (!isOpen) return null;

  const allSymbols = [
    { name: 'StringRef', container: 'llvm', file: 'StringRef.h', kind: 'class', line: 6 },
    { name: 'stringRef', container: 'llvm::Twine::Child', file: 'Twine.h', kind: 'field', line: 92 },
    { name: 'StringRef', container: 'llvm::StringRef', file: 'StringRef.h', kind: 'constructor', line: 11 },
    { name: 'PreambleFileStatusCache', container: 'clang::clangd', file: 'FS.h', kind: 'class', line: 20 },
    { name: 'getProducingFS', container: 'PreambleFileStatusCache', file: 'FS.cpp', kind: 'method', line: 20 },
    { name: 'print_hex', container: 'clang::clangd', file: 'FS.cpp', kind: 'function', line: 15 },
    { name: 'ConsequenceEngine', container: 'veklom_shared_dispatch', file: 'rust_veklom_shared_dispatch.rs', kind: 'struct', line: 4 },
    { name: 'get_python_environment_info', container: 'env_manager', file: 'env_manager.py', kind: 'function', line: 14 }
  ];

  const filtered = allSymbols.filter(s => {
    const cleanQ = query.replace('#', '').toLowerCase();
    return s.name.toLowerCase().includes(cleanQ) || s.container.toLowerCase().includes(cleanQ);
  });

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-xl bg-[#1e222a] border border-[#303644] rounded-xl shadow-2xl overflow-hidden font-sans text-xs">
        {/* Search Input Bar */}
        <div className="p-3 bg-[#161a22] border-b border-[#272d3b] flex items-center gap-2.5">
          <Search className="w-4 h-4 text-[#7d8590]" />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Type # to search workspace symbols..."
            autoFocus
            className="flex-1 bg-transparent text-white font-mono text-sm focus:outline-none"
          />
          <button onClick={onClose} className="text-[#7d8590] hover:text-white">Esc</button>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto divide-y divide-[#232936]">
          {filtered.map(s => (
            <div
              key={`${s.name}-${s.file}-${s.line}`}
              onClick={() => onSelectSymbol(s)}
              className="px-4 py-2.5 hover:bg-[#252c3a] cursor-pointer flex items-center justify-between transition-colors group"
            >
              <div className="flex items-center gap-2.5 truncate">
                <Box className="w-3.5 h-3.5 text-[#e3b341] shrink-0" />
                <span className="font-mono text-white font-semibold">{s.name}</span>
                <span className="text-[#8b949e] font-mono text-[11px] truncate">
                  {s.container} — {s.file}
                </span>
              </div>
              <span className="text-[10px] font-mono text-[#58a6ff] shrink-0 opacity-0 group-hover:opacity-100 transition">
                Line {s.line}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ==========================================
// 6. CROSS REFERENCES DRAWER (Matches xrefs.png)
// ==========================================
interface CrossReferencesDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectRef: (fileId: string, line: number) => void;
}

export function CrossReferencesDrawer({ isOpen, onClose, onSelectRef }: CrossReferencesDrawerProps) {
  if (!isOpen) return null;

  const references = [
    {
      file: 'ClangdUnit.cpp',
      dir: 'clang-tools-extra/clangd',
      fileId: 'clangd_unit',
      line: 12,
      snippet: 'StatCache->getProducingFS(Inputs.FS);'
    },
    {
      file: 'FS.cpp',
      dir: 'clang-tools-extra/clangd',
      fileId: 'fs_cpp',
      line: 20,
      snippet: 'PreambleFileStatusCache::getProducingFS(IntrusiveRefCntPtr<...)'
    },
    {
      file: 'FS.h',
      dir: 'clang-tools-extra/clangd',
      fileId: 'fs_h',
      line: 26,
      snippet: 'getProducingFS(IntrusiveRefCntPtr<llvm::vfs::FileSystem> FS);'
    },
    {
      file: 'FSTests.cpp',
      dir: 'clang-tools-extra/clangd',
      fileId: 'fs_tests',
      line: 12,
      snippet: 'StatCache.getProducingFS(MemFS);'
    }
  ];

  return (
    <div className="h-64 bg-[#111317] border-t border-[#262c37] flex flex-col font-mono text-xs animate-fadeIn">
      {/* Header */}
      <div className="h-8 bg-[#161a22] px-4 flex items-center justify-between border-b border-[#21262d] text-[#8b949e]">
        <div className="flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-[#58a6ff]" />
          <span className="text-white font-semibold">4 results in 4 files</span>
          <span className="text-[11px] text-[#7d8590]">for symbol 'getProducingFS'</span>
        </div>
        <button onClick={onClose} className="hover:text-white p-1">
          <X size={14} />
        </button>
      </div>

      {/* Cross-ref List & Preview */}
      <div className="flex-1 flex overflow-hidden">
        {/* Results List */}
        <div className="w-72 border-r border-[#21262d] overflow-y-auto divide-y divide-[#1e2330]">
          {references.map((r, i) => (
            <div
              key={i}
              onClick={() => onSelectRef(r.fileId, r.line)}
              className="p-2.5 hover:bg-[#1a202c] cursor-pointer transition-colors"
            >
              <div className="flex items-center gap-1.5 text-white font-medium">
                <FileCode className="w-3.5 h-3.5 text-[#58a6ff]" />
                <span>{r.file}</span>
                <span className="text-[10px] text-[#7d8590]">:{r.line}</span>
              </div>
              <p className="text-[11px] text-[#8b949e] truncate mt-1">
                {r.snippet}
              </p>
            </div>
          ))}
        </div>

        {/* Live Code Preview */}
        <div className="flex-1 p-4 bg-[#0d0f13] overflow-auto">
          <div className="text-[10px] text-[#7d8590] uppercase tracking-wider mb-1">
            clang-tools-extra › clangd › FS.h › PreambleFileStatusCache
          </div>
          <pre className="text-xs font-mono text-[#e6edf3] bg-[#141820] p-3 rounded-lg border border-[#242c3d]">
            {`Declared in PreambleFileStatusCache:
IntrusiveRefCntPtr<llvm::vfs::FileSystem>
getProducingFS(IntrusiveRefCntPtr<llvm::vfs::FileSystem> FS);

Returns a VFS that collects file status. Only cache stats for files that are
part of the preamble.`}
          </pre>
        </div>
      </div>
    </div>
  );
}
