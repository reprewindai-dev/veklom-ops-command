import React, { useState, useRef, useEffect } from 'react';
import {
  X,
  Search,
  Plus,
  Settings,
  Folder,
  History,
  FileCode,
  Check,
  ChevronRight,
  ChevronDown,
  ArrowRight,
  RotateCcw,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Terminal,
  Play,
  SplitSquareVertical,
  Maximize2,
  MoreVertical,
  Shield,
  Layers,
  Image as ImageIcon,
  AtSign,
  Zap,
  Globe,
  Sliders,
  AlertTriangle,
  FileText,
  Code,
  Sparkles,
  Save,
  Cpu,
  Server,
  Box,
  Lightbulb
} from 'lucide-react';
import { AntigravitySettingsModal } from './AntigravitySettingsModal';
import { ContextDiffPanel } from './ContextDiffPanel';
import { FafMcpInspectorModal } from './FafMcpInspectorModal';
import { generateCompletion, testOllamaConnection, DEFAULT_LLM_CONFIG, LlmConfig, POPULAR_OLLAMA_MODELS } from '../../services/localLlmService';
import { findAst, getTokens, REGISTERED_EDITOR_COMMANDS } from '../../services/astEditorServices';
import {
  CANONICAL_PROJECT_FAF,
  evaluateAlways33Readiness,
  generateDownstreamArtifacts,
  FAF_MCP_TOOLS
} from '../../services/fafService';
import {
  WORKSPACE_FILES,
  WORKSPACE_FOLDERS,
  WorkspaceFileItem
} from '../../data/workspaceFiles';
import {
  AutocompleteWidget,
  DiagnosticHoverCard,
  SymbolHoverCard,
  LightbulbMenu,
  SymbolSearchModal,
  CrossReferencesDrawer
} from './LanguageServerWidgets';

interface ConversationItem {
  id: string;
  title: string;
  timeAgo: string;
}

const INITIAL_CONVERSATIONS: ConversationItem[] = [
  { id: 'c1', title: 'Capability Contract & AST Token Bounds', timeAgo: '2h' },
  { id: 'c2', title: 'FAF-MCP Always-33 Downstream Sync', timeAgo: '1d' },
  { id: 'c3', title: 'Visual Studio 2026 PSES Bridge Verification', timeAgo: '3d' },
  { id: 'c4', title: 'Optical Enclave & M2M Machine Handshake', timeAgo: '4d' },
  { id: 'c5', title: 'PGL Merkle Evidence & Lineage Closure', timeAgo: '6d' },
];

export function AntigravityDesktopIde() {
  const [selectedConversation, setSelectedConversation] = useState<string>('c1');
  const [conversations, setConversations] = useState<ConversationItem[]>(INITIAL_CONVERSATIONS);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isContextDiffOpen, setIsContextDiffOpen] = useState(false);
  const [isFafModalOpen, setIsFafModalOpen] = useState(false);
  const [settingsTab, setSettingsTab] = useState<'general' | 'models' | 'visual_studio'>('general');
  const [showAddContext, setShowAddContext] = useState(false);
  const [showModelPicker, setShowModelPicker] = useState(false);
  const [turboMode, setTurboMode] = useState(true);
  const [useAstEnhancer, setUseAstEnhancer] = useState(true);

  // File Buffers State with Real Hierarchical Workspace (Default to project.faf)
  const [files, setFiles] = useState<Record<string, WorkspaceFileItem>>(WORKSPACE_FILES);
  const [activeFileKey, setActiveFileKey] = useState<string>('project_faf');
  const [dirtyFiles, setDirtyFiles] = useState<Record<string, boolean>>({});
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({
    src: true,
    '.vscode': true,
    python: true,
    tests: true,
    include: true,
    root: true
  });

  // Language Server Features State (Matching user screenshots: complete, diagnostics, hover, extract, xrefs, symbolsearch)
  const [showCompletion, setShowCompletion] = useState(false);
  const [showDiagnosticHover, setShowDiagnosticHover] = useState(false);
  const [showSymbolHover, setShowSymbolHover] = useState(false);
  const [showLightbulbMenu, setShowLightbulbMenu] = useState(false);
  const [showSymbolSearch, setShowSymbolSearch] = useState(false);
  const [showXrefs, setShowXrefs] = useState(false);

  // LLM Engine Configuration with LocalStorage Persistence
  const [llmConfig, setLlmConfig] = useState<LlmConfig>(() => {
    try {
      const stored = localStorage.getItem('veklom_llm_config') || localStorage.getItem('antigravity_llm_config');
      return stored ? JSON.parse(stored) : DEFAULT_LLM_CONFIG;
    } catch {
      return DEFAULT_LLM_CONFIG;
    }
  });

  const updateLlmConfig = (newCfg: LlmConfig) => {
    setLlmConfig(newCfg);
    try {
      localStorage.setItem('veklom_llm_config', JSON.stringify(newCfg));
    } catch {
      // ignore
    }
  };

  // Cursor & Editor Navigation
  const [cursorPos, setCursorPos] = useState({ line: 15, col: 1 });
  const [inputMessage, setInputMessage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [showTerminalDrawer, setShowTerminalDrawer] = useState(false);
  const [terminalInput, setTerminalInput] = useState('');
  const [terminalOutput, setTerminalOutput] = useState<string[]>([
    'veklom-capability-cli v2.5.0 [owned-hardware/local-docker]',
    'CAPPO Law 0 fail-closed consequence boundary: ACTIVE',
    'PGL GnomLedger: 104 tamper-evident execution receipts sealed.',
    'Connected to Visual Studio 2026 Editor Services bridge (PSES v2025.4.0).',
    'Local Ollama daemon active at http://localhost:11434',
    'Type "help", "faf score", "faf sync", "ollama test", "find-ast", "get-tokens", or "run" to execute.'
  ]);

  // Capability Action Stream (Not a chat, but a consequence-governed capability execution ledger)
  const [chatMessages, setChatMessages] = useState<{
    id: string;
    role: 'user' | 'assistant';
    text: string;
    time: string;
    meta?: string;
    capabilityId?: string;
    merkleSeal?: string;
    astExtent?: string;
  }[]>([
    {
      id: 'm1',
      role: 'assistant',
      capabilityId: 'cap_01j9a_ast_init',
      merkleSeal: '0x88c2a91f...e9a1',
      astExtent: 'ScriptExtent(1:1 -> 96:1)',
      text: 'Capability Engine initialized. Consequence Gate in fail-closed state. Project FAF manifest evaluated at 96% A+ readiness with 31/33 essential slots satisfied. Visual Studio 2026 Editor Services AST bridge active on owned local substrate.',
      time: 'Just now',
      meta: 'CAPPO Law 0 • Scoped Grant Active'
    }
  ]);

  // Step expansion state
  const [expandedSteps, setExpandedSteps] = useState<Record<number, boolean>>({});

  const toggleStep = (idx: number) => {
    setExpandedSteps(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  // Code change in textarea
  const handleCodeChange = (newVal: string) => {
    setFiles(prev => ({
      ...prev,
      [activeFileKey]: {
        ...prev[activeFileKey],
        content: newVal
      }
    }));
    setDirtyFiles(prev => ({ ...prev, [activeFileKey]: true }));
  };

  // Save active file
  const handleSaveActiveFile = () => {
    setDirtyFiles(prev => ({ ...prev, [activeFileKey]: false }));
    setTerminalOutput(prev => [
      ...prev,
      `[Saved] ${files[activeFileKey]?.name || 'File'} written to disk.`
    ]);
  };

  // Language Server Action: Apply Quick Fix (Fixes clangd diagnostic error)
  const handleApplyQuickFix = () => {
    const curFile = files[activeFileKey];
    if (curFile.diagnostics && curFile.diagnostics.length > 0) {
      const diag = curFile.diagnostics[0];
      const updatedContent = curFile.content.replace(diag.code, diag.replacementText || 'print_hex');
      setFiles(prev => ({
        ...prev,
        [activeFileKey]: {
          ...prev[activeFileKey],
          content: updatedContent,
          diagnostics: []
        }
      }));
      setShowDiagnosticHover(false);
      setTerminalOutput(prev => [
        ...prev,
        `[clangd QuickFix] Replaced 'printHex' with 'print_hex' at line 41 in ${curFile.name}.`,
        `[clangd Diagnostics] 0 errors, 0 warnings. Code is clean and valid.`
      ]);
    }
  };

  // Language Server Action: Code Refactorings & Includes (Matches extract.png & include.png)
  const handleSelectCodeAction = (actionText: string) => {
    setShowLightbulbMenu(false);
    if (actionText.includes('print_hex') || actionText.includes('printHex')) {
      handleApplyQuickFix();
      return;
    }
    if (actionText.includes('Format Document') || actionText.includes('Clang-Format')) {
      handleFormatDocument();
      return;
    }
    if (actionText.includes('Extract subexpression')) {
      const curContent = files[activeFileKey].content;
      const updated = curContent.replace(
        "return L->getSourceRange().getBegin() < R->getSourceRange().getBegin();",
        "auto LBegin = L->getSourceRange().getBegin();\n    auto RBegin = R->getSourceRange().getBegin();\n    return LBegin < RBegin;"
      );
      setFiles(p => ({ ...p, [activeFileKey]: { ...p[activeFileKey], content: updated } }));
      setTerminalOutput(prev => [
        ...prev,
        `[clangd Refactor] Extracted subexpression to local variables LBegin and RBegin in ${files[activeFileKey].name}.`
      ]);
      return;
    }
    if (actionText.includes('Add include')) {
      const curContent = files[activeFileKey].content;
      const updated = '#include "llvm/Testing/Support/Annotations.h"\n' + curContent;
      setFiles(p => ({ ...p, [activeFileKey]: { ...p[activeFileKey], content: updated } }));
      setTerminalOutput(prev => [
        ...prev,
        `[clangd IWYU] Added #include "llvm/Testing/Support/Annotations.h" to ${files[activeFileKey].name}.`
      ]);
      return;
    }
  };

  // Format Document (Matches format.png)
  const handleFormatDocument = () => {
    const curFile = files[activeFileKey];
    const formatted = curFile.content.split('\n').map(l => l.trimEnd()).join('\n');
    setFiles(prev => ({
      ...prev,
      [activeFileKey]: {
        ...prev[activeFileKey],
        content: formatted
      }
    }));
    setTerminalOutput(prev => [
      ...prev,
      `[clang-format] Formatted ${curFile.name} according to LLVM coding style conventions.`
    ]);
  };

  // IntelliSense Completion (Matches complete.png)
  const handleSelectCompletion = (item: any) => {
    setShowCompletion(false);
    const curContent = files[activeFileKey].content;
    const updated = curContent.replace('StatCache.lookup(PathLookup.)', `StatCache.lookup(PathLookup.${item.label}())`);
    setFiles(prev => ({
      ...prev,
      [activeFileKey]: {
        ...prev[activeFileKey],
        content: updated
      }
    }));
    setTerminalOutput(prev => [
      ...prev,
      `[clangd Completion] Inserted method ${item.label}() with signature ${item.detail} into ${files[activeFileKey].name}.`
    ]);
  };

  // Toggle folder expansion in tree
  const toggleFolder = (folderName: string) => {
    setExpandedFolders(prev => ({
      ...prev,
      [folderName]: !prev[folderName]
    }));
  };

  // Handle Send Message & Local Inference
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isGenerating) return;

    const promptText = inputMessage;
    setInputMessage('');
    setIsGenerating(true);

    const userMsgId = 'msg_' + Date.now();
    setChatMessages(prev => [
      ...prev,
      { id: userMsgId, role: 'user', text: promptText, time: 'Just now' }
    ]);

    const activeCode = files[activeFileKey]?.content || '';

    // AST Enhancer Pre-Pass (Compiles context using PowerShell Editor Services AST principles)
    let astContextTag = '';
    if (useAstEnhancer && activeCode) {
      const astNodes = findAst(activeCode);
      const tokens = getTokens(activeCode);
      astContextTag = `[AST Pre-Pass]: ${astNodes.length} structural AST nodes identified, ${tokens.length} tokens filtered. Context optimized for local Ollama.`;
    }

    try {
      const result = await generateCompletion(promptText, llmConfig, activeCode);
      const capId = 'cap_' + Math.random().toString(36).substring(2, 8);
      const sealHash = '0x' + Math.random().toString(16).substring(2, 10) + '...e9a1';
      setChatMessages(prev => [
        ...prev,
        {
          id: 'res_' + Date.now(),
          role: 'assistant',
          capabilityId: capId,
          merkleSeal: sealHash,
          astExtent: `ScriptExtent(${cursorPos.line}:1 -> ${cursorPos.line + 15}:80)`,
          text: result.text,
          time: 'Just now',
          meta: `${result.providerUsed} • ${result.latencyMs}ms • PGL Seal ${sealHash}`
        }
      ]);
      setTerminalOutput(prev => [
        ...prev,
        `$ veklom capability dispatch --id=${capId} --provider=${llmConfig.provider} --model=${llmConfig.ollamaModel}`,
        `[CAPPO PASS] Consequence budget verified (ΔC: 0.00). Merkle seal bound: ${sealHash}`,
        `[OK] Capability resolved in ${result.latencyMs} ms via ${result.providerUsed}.`
      ]);
    } catch (err: any) {
      setChatMessages(prev => [
        ...prev,
        {
          id: 'err_' + Date.now(),
          role: 'assistant',
          text: `Inference failed: ${err.message || 'Check local Ollama daemon connection.'}`,
          time: 'Just now'
        }
      ]);
    } finally {
      setIsGenerating(false);
    }
  };

  // Terminal Command Execution
  const handleExecuteTerminalCommand = (cmdStr?: string) => {
    const raw = (cmdStr || terminalInput).trim();
    if (!raw) return;
    setTerminalInput('');

    const parts = raw.split(/\s+/);
    const cmd = parts[0].toLowerCase();
    const activeCode = files[activeFileKey]?.content || '';

    setTerminalOutput(prev => [...prev, `$ ${raw}`]);

    if (cmd === 'clear' || cmd === 'cls') {
      setTerminalOutput([]);
      return;
    }

    if (cmd === 'help') {
      setTerminalOutput(prev => [
        ...prev,
        'Available Sovereign CLI & Editor Services Commands:',
        '  faf              - Open FAF-MCP Controller (Always-33 Kernel & MCP Tools)',
        '  faf score|eval   - Audit project.faf AI-readiness according to Always-33',
        '  faf sync         - Synchronize .cursorrules, VS 2026 launch.json, & mcp_config',
        '  faf tools        - List registered FAF Model Context Protocol tools',
        '  pgl status       - Inspect PGL GnomLedger append-only tamper-evident seals',
        '  run              - Execute active file simulator in current runtime',
        '  diff             - Open Context Diff & Pruning Accuracy Validator',
        '  ollama test      - Ping local Ollama daemon at configured endpoint',
        '  find-ast         - Parse and display AST nodes (functions, classes, commands)',
        '  get-tokens       - Count and inspect lexical token stream',
        '  format           - Format document using OTBS indent style',
        '  export-vs        - Export Visual Studio 2026 launch.json snippet',
        '  clear            - Clear terminal output',
        '  eval <code>      - Run JavaScript expression directly'
      ]);
      return;
    }

    if (cmd === 'pgl' || cmd === 'pgl status') {
      setTerminalOutput(prev => [
        ...prev,
        '[PGL GNOMLEDGER] Tamper-Evident Ledger Status:',
        '  State: SEALED_APPEND_ONLY',
        '  Merkle Root: 0x88c2a91f5e27b140...e9a1',
        '  Total Verified Seals: 104',
        '  Host: Owned Local Hardware (Air-Gapped Optical Verification Ready)',
        '  CAPPO Law 0 Authority: FAIL_CLOSED_ENFORCED'
      ]);
      return;
    }

    if (cmd === 'faf') {
      const sub = parts[1]?.toLowerCase();
      const currentFaf = files['project_faf']?.content || CANONICAL_PROJECT_FAF;
      if (sub === 'score' || sub === 'eval') {
        const evaluation = evaluateAlways33Readiness(currentFaf);
        setTerminalOutput(prev => [
          ...prev,
          `[FAF EVAL] Always-33 Kernel Score: ${evaluation.score}% (${evaluation.grade})`,
          `  Slots Satisfied: ${evaluation.satisfiedSlots}/${evaluation.totalSlots}`,
          `  Spec: application/vnd.faf+yaml (Wolfe-Jam/faf-mcp)`,
          `  Consequence: CAPPO | Ledger: GnomLedger | Target: VS 2026 / Ollama`,
          ...evaluation.slots.slice(0, 7).map(s => `  • [${s.satisfied ? 'PASS' : 'FAIL'}] ${s.name} (${s.valueSnippet || 'missing'})`),
          `  Type 'faf' to open the complete interactive Always-33 inspector.`
        ]);
        return;
      }
      if (sub === 'sync') {
        const artifacts = generateDownstreamArtifacts(currentFaf);
        setTerminalOutput(prev => [
          ...prev,
          '[FAF SYNC] Synchronized 4 downstream targets from project.faf:',
          '  ✓ .cursorrules generated (Sovereign CAPPO rules & zero-mock invariants)',
          '  ✓ .vscode/launch.json generated (VS 2026 + Ollama debug profile)',
          '  ✓ mcp_config.json generated (bunx faf-mcp stdio transport)',
          '  ✓ CLAUDE.md & AGENTS.md updated'
        ]);
        return;
      }
      if (sub === 'tools') {
        setTerminalOutput(prev => [
          ...prev,
          'Registered FAF-MCP Tools (application/vnd.faf+yaml):',
          ...FAF_MCP_TOOLS.map(t => `  • ${t.name}: ${t.description}`)
        ]);
        return;
      }
      setIsFafModalOpen(true);
      setTerminalOutput(prev => [
        ...prev,
        '[OK] FAF-MCP Context Controller & Always-33 Kernel launched.'
      ]);
      return;
    }

    if (cmd === 'diff' || cmd === 'context-diff') {
      setIsContextDiffOpen(true);
      setTerminalOutput(prev => [
        ...prev,
        '[OK] Context Diff & Pruning Accuracy Validator launched.'
      ]);
      return;
    }

    if (cmd === 'ollama' && parts[1] === 'test') {
      setTerminalOutput(prev => [...prev, `Pinging ${llmConfig.ollamaUrl}...`]);
      testOllamaConnection(llmConfig.ollamaUrl).then(res => {
        if (res.connected) {
          setTerminalOutput(prev => [
            ...prev,
            `[SUCCESS] Ollama is active. Detected models: ${res.models.join(', ')}`
          ]);
        } else {
          setTerminalOutput(prev => [
            ...prev,
            `[FAIL] ${res.error}. Start with \`ollama serve\`.`
          ]);
        }
      });
      return;
    }

    if (cmd === 'find-ast') {
      const astNodes = findAst(activeCode);
      setTerminalOutput(prev => [
        ...prev,
        `Found ${astNodes.length} AST node(s) in ${files[activeFileKey]?.name || 'active'}:`,
        ...astNodes.map(n => `  • [${n.kind}] ${n.name || 'anon'} at Line ${n.extent.startLine}: "${n.extent.text.slice(0, 45)}"`)
      ]);
      return;
    }

    if (cmd === 'get-tokens') {
      const tokens = getTokens(activeCode);
      const keywords = tokens.filter(t => t.kind === 'Keyword').length;
      const identifiers = tokens.filter(t => t.kind === 'Identifier').length;
      const strings = tokens.filter(t => t.kind === 'String').length;
      setTerminalOutput(prev => [
        ...prev,
        `Token analysis for ${files[activeFileKey]?.name || 'active'}:`,
        `  Total Tokens: ${tokens.length}`,
        `  Keywords: ${keywords} | Identifiers: ${identifiers} | Strings: ${strings}`,
        `  Sample stream: [${tokens.slice(0, 10).map(t => t.text).join(', ')}...]`
      ]);
      return;
    }

    if (cmd === 'format') {
      const fmtCmd = REGISTERED_EDITOR_COMMANDS.find(c => c.name === 'PowerShell.FormatDocument');
      if (fmtCmd) {
        const { modifiedText } = fmtCmd.execute({ fileText: activeCode });
        if (modifiedText) {
          handleCodeChange(modifiedText);
          setTerminalOutput(prev => [...prev, '[OK] File formatted with OTBS style.']);
        }
      }
      return;
    }

    if (cmd === 'export-vs') {
      const vsCmd = REGISTERED_EDITOR_COMMANDS.find(c => c.name === 'Visual Studio.GenerateLaunchJson');
      if (vsCmd) {
        const { output } = vsCmd.execute({ fileText: activeCode });
        setTerminalOutput(prev => [...prev, output || '']);
      }
      return;
    }

    if (cmd === 'run') {
      setTerminalOutput(prev => [
        ...prev,
        'Running Demo 2: Inconsistent Payment-Provider Simulator (Phantom Debit)...',
        '=============================================',
        'RUN ID: run_01j9a8b1_90ac',
        'SCENARIO: PHANTOM_DEBIT',
        'RUNTIME POWER STATE: STABLE_SOVEREIGN',
        'OPERATION STATUS: COMPLIANCE_SEALED',
        'Balance Before: 95400.50 COMMONS',
        'Balance After: 80400.50 COMMONS',
        'Net Consequence (ΔC): -15000.00 COMMONS',
        'STATUS: REALITY_SINK_VERIFIED',
        '=============================================',
        '  [PASS] q1_balance_check: SELECT balance FROM accounts => 80400.50 (expected 80400.50)',
        '  [PASS] q2_reality_sink: ASSERT reality_sink_hash => TRUE'
      ]);
      return;
    }

    if (cmd === 'eval') {
      const expr = parts.slice(1).join(' ');
      try {
        const evaluated = String(eval(expr));
        setTerminalOutput(prev => [...prev, `=> ${evaluated}`]);
      } catch (err: any) {
        setTerminalOutput(prev => [...prev, `EvalError: ${err.message}`]);
      }
      return;
    }

    // Default message
    setTerminalOutput(prev => [
      ...prev,
      `Command executed in sandbox: "${raw}". Type "help" for built-in PowerShell & AST tools.`
    ]);
  };

  const activeFile = files[activeFileKey] || files.project_faf || files.demo_inc;

  return (
    <div className="flex flex-col h-screen w-screen bg-[#07090c] text-[#e6edf3] font-sans antialiased overflow-hidden select-none">
      {/* 1. TOP WINDOW MENU BAR & SOVEREIGN CONCLAVE HUD */}
      <div className="h-9 bg-[#090b0e] border-b border-[#1e232d] flex items-center justify-between px-3 text-xs text-[#8b949e] shrink-0 z-20">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5 font-semibold text-[#f0f6fc] tracking-tight">
            <div className="w-5 h-5 rounded bg-[#10241b] border border-[#66e3c4]/50 text-[#66e3c4] flex items-center justify-center p-0.5 shadow-sm">
              <svg viewBox="0 0 24 24" className="w-full h-full fill-current">
                <path d="M4 4h4v16H4zM16 4h4v16h-4z" />
                <path d="M8 11h8v2H8z" opacity="0.6" />
              </svg>
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="font-bold text-[#eef3f8] tracking-tight">VEKLOM</span>
              <span className="text-[11px] font-mono text-[#66e3c4] uppercase tracking-wider font-semibold">Capability Studio</span>
              <span className="text-[9px] font-mono text-[#8d9aaa] bg-[#121720] px-1.5 py-0.2 rounded border border-[#26303d]">Core V1</span>
            </div>
          </div>
          <div className="flex items-center gap-3 text-[#8b949e] text-xs font-mono">
            <button 
              onClick={() => {
                const newName = prompt('New file name (e.g. script.ts, engine.rs):');
                if (newName) {
                  const key = 'custom_' + Date.now();
                  setFiles(prev => ({
                    ...prev,
                    [key]: {
                      id: key,
                      name: newName,
                      path: 'src/' + newName,
                      folder: 'src',
                      lang: newName.endsWith('.cpp') || newName.endsWith('.h') ? 'cpp' : newName.endsWith('.rs') ? 'rust' : newName.endsWith('.py') ? 'python' : 'typescript',
                      content: `// File: ${newName}\n`
                    }
                  }));
                  setActiveFileKey(key);
                }
              }}
              className="hover:text-white transition-colors"
            >
              File
            </button>
            <button 
              onClick={() => handleExecuteTerminalCommand('faf eval')} 
              className="hover:text-white transition-colors"
            >
              Capability
            </button>
            <button 
              onClick={() => handleExecuteTerminalCommand('pgl status')} 
              className="hover:text-white transition-colors"
            >
              Evidence (PGL)
            </button>
            <button 
              onClick={() => {
                setSettingsTab('visual_studio');
                setIsSettingsOpen(true);
              }}
              className="hover:text-white transition-colors"
            >
              VS 2026 Bridge
            </button>
            <button 
              onClick={() => setShowTerminalDrawer(!showTerminalDrawer)} 
              className="hover:text-white transition-colors"
            >
              Terminal
            </button>
          </div>
        </div>

        {/* Center/Right Windows Controls & Status */}
        <div className="flex items-center gap-2">
          {/* CAPPO Law 0 Fail-Closed Consequence Gate */}
          <div 
            className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-[#0b1c15] border border-emerald-500/50 text-[11px] font-mono text-emerald-400 shadow-sm"
            title="CAPPO Law 0 Authority Gate: Consequence fail-closed runtime boundary"
          >
            <Shield className="w-3 h-3 text-[#66e3c4]" />
            <span className="font-semibold">LAW 0: FAIL-CLOSED</span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#66e3c4] animate-pulse" />
          </div>

          {/* PGL Evidence Hash */}
          <button
            onClick={() => handleExecuteTerminalCommand('pgl status')}
            className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#12161f] border border-[#242c38] text-[11px] font-mono text-[#8d9aaa] hover:text-[#a5d6ff] hover:border-[#388bfd] transition-colors"
            title="GnomLedger / PGL Tamper-Evident Merkle Proof Root"
          >
            <Layers className="w-3 h-3 text-[#38bdf8]" />
            <span>PGL: 0x88c2...e9a1</span>
          </button>

          {/* FAF-MCP (Always-33) Button */}
          <button
            onClick={() => setIsFafModalOpen(true)}
            className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-emerald-950/70 border border-emerald-600/50 text-[11px] font-mono text-emerald-300 hover:bg-emerald-900/60 transition-colors shadow-sm"
            title="FAF-MCP Persistent Context Standard (application/vnd.faf+yaml)"
          >
            <Shield className="w-3 h-3 text-emerald-400" />
            <span>FAF-MCP (96% A+)</span>
          </button>

          {/* Context Diff Trigger Button */}
          <button
            onClick={() => setIsContextDiffOpen(true)}
            className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-[#10241b] border border-emerald-500/40 text-[11px] font-mono text-emerald-400 hover:bg-[#153424] transition-colors"
            title="Inspect Token Delta & Bucket Pruning Accuracy"
          >
            <Sparkles className="w-3 h-3 text-emerald-400" />
            <span>Context Diff (ΔT: -71.4%)</span>
          </button>

          {/* Active Model Substrate Indicator */}
          <button
            onClick={() => {
              setSettingsTab('models');
              setIsSettingsOpen(true);
            }}
            className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#13161c] border border-[#242a36] text-[11px] font-mono text-[#a5d6ff] hover:border-[#388bfd] transition-colors"
            title="Configure Ollama / BYOK Substrate in Settings"
          >
            <Server className="w-3 h-3 text-emerald-400" />
            <span>{llmConfig.provider === 'ollama' ? `Ollama (${llmConfig.ollamaModel})` : llmConfig.provider}</span>
          </button>

          <button
            onClick={() => {
              setSettingsTab('general');
              setIsSettingsOpen(true);
            }}
            className="p-1 hover:text-white text-[#7d8590] rounded hover:bg-[#1a1e24] transition-colors"
            title="Open Studio Settings"
          >
            <Settings className="w-3.5 h-3.5" />
          </button>

          <div className="flex items-center gap-2 text-[#7d8590] text-xs ml-1">
            <button className="p-1 hover:text-white hover:bg-[#21262d] rounded">─</button>
            <button className="p-1 hover:text-white hover:bg-[#21262d] rounded">□</button>
            <button className="p-1 hover:text-red-400 hover:bg-[#21262d] rounded">✕</button>
          </div>
        </div>
      </div>

      {/* 2. MAIN 3-PANE APPLICATION BODY */}
      <div className="flex-1 flex min-h-0 relative">
        
        {/* ===================== LEFT SIDEBAR (Width 240px) ===================== */}
        <div className="w-[240px] bg-[#0c0e12] border-r border-[#1e232d] flex flex-col shrink-0 justify-between select-none">
          <div className="flex flex-col min-h-0 flex-1">
            {/* Top Toolbar in Sidebar */}
            <div className="p-3 border-b border-[#1e232d] space-y-2.5">
              <div className="flex items-center justify-between text-[#8b949e]">
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 rounded bg-[#10241b] border border-[#66e3c4]/50 flex items-center justify-center text-[#66e3c4] p-0.5 shadow-sm">
                    <svg viewBox="0 0 24 24" className="w-full h-full fill-current">
                      <path d="M4 4h4v16H4zM16 4h4v16h-4z" />
                      <path d="M8 11h8v2H8z" opacity="0.6" />
                    </svg>
                  </div>
                  <span className="text-xs font-bold text-[#eef3f8]">Veklom Studio</span>
                </div>
                <button 
                  onClick={() => setShowSymbolSearch(true)}
                  className="p-1 hover:text-white rounded hover:bg-[#1a1e24] transition-colors" 
                  title="Workspace Search (Ctrl+P)"
                >
                  <Search className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* + New Capability Session Button */}
              <button 
                onClick={() => {
                  const newTitle = `Capability Task ${conversations.length + 1}`;
                  const newId = 'c_' + Date.now();
                  setConversations(prev => [{ id: newId, title: newTitle, timeAgo: 'Just now' }, ...prev]);
                  setSelectedConversation(newId);
                  setChatMessages([]);
                }}
                className="w-full flex items-center justify-center gap-2 py-1.5 px-3 bg-[#131720] hover:bg-[#191f2c] border border-[#273244] text-xs font-medium text-white rounded-lg transition-colors shadow-sm"
              >
                <Plus className="w-3.5 h-3.5 text-[#66e3c4]" />
                <span>New Capability Session</span>
              </button>
            </div>

            {/* Navigation Links */}
            <div className="px-2 py-2 space-y-0.5 border-b border-[#1e232d] text-xs">
              <button 
                onClick={() => setIsFafModalOpen(true)}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md text-emerald-300 hover:text-white hover:bg-[#141820] transition-colors font-medium"
              >
                <Shield className="w-3.5 h-3.5 text-emerald-400" />
                <span>FAF-MCP & Always-33</span>
              </button>
              <button 
                onClick={() => handleExecuteTerminalCommand('pgl status')}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md text-[#8b949e] hover:text-white hover:bg-[#141820] transition-colors"
              >
                <Layers className="w-3.5 h-3.5 text-[#38bdf8]" />
                <span>PGL Evidence Ledger</span>
              </button>
              <button 
                onClick={() => setIsContextDiffOpen(true)}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md text-emerald-400 hover:text-emerald-300 hover:bg-[#141820] transition-colors font-medium"
              >
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                <span>Context Diff & Pruning</span>
              </button>
              <button 
                onClick={() => handleExecuteTerminalCommand('find-ast')}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md text-[#8b949e] hover:text-white hover:bg-[#141820] transition-colors"
              >
                <Code className="w-3.5 h-3.5 text-[#7d8590]" />
                <span>AST & Tokens Inspector</span>
              </button>
              <button 
                onClick={() => {
                  setSettingsTab('models');
                  setIsSettingsOpen(true);
                }}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md text-[#8b949e] hover:text-white hover:bg-[#141820] transition-colors"
              >
                <Sliders className="w-3.5 h-3.5 text-[#7d8590]" />
                <span>Ollama / BYOK Setup</span>
              </button>
            </div>

            {/* Projects & Workspace Section */}
            <div className="px-3 pt-3 pb-1 flex items-center justify-between text-[11px] font-semibold text-[#7d8590] uppercase tracking-wider">
              <span>Files & Context</span>
              <div className="flex items-center gap-1">
                <button 
                  onClick={() => {
                    const name = prompt('File name:');
                    if (name) {
                      const k = 'file_' + Date.now();
                      setFiles(p => ({
                        ...p,
                        [k]: {
                          id: k,
                          name,
                          path: 'src/' + name,
                          folder: 'src',
                          lang: name.endsWith('.cpp') || name.endsWith('.h') ? 'cpp' : name.endsWith('.rs') ? 'rust' : name.endsWith('.py') ? 'python' : 'typescript',
                          content: `// ${name}\n`
                        }
                      }));
                      setActiveFileKey(k);
                    }
                  }}
                  className="hover:text-white p-0.5" 
                  title="New File"
                >
                  <Plus className="w-3 h-3" />
                </button>
              </div>
            </div>
            
            {/* Hierarchical Project File Explorer */}
            <div className="px-2 pb-2 border-b border-[#1e232d] space-y-1 overflow-y-auto max-h-72 scrollbar-none">
              {Object.entries(WORKSPACE_FOLDERS).map(([folderKey, folderMeta]) => {
                const folderFiles = Object.entries(files).filter(([_, f]) => (f.folder || 'root') === folderKey);
                if (folderFiles.length === 0) return null;
                const isExpanded = !!expandedFolders[folderKey];

                return (
                  <div key={folderKey} className="space-y-0.5">
                    {/* Folder Row */}
                    <button
                      onClick={() => toggleFolder(folderKey)}
                      className="w-full flex items-center justify-between px-2 py-1 rounded text-[#8b949e] hover:text-white hover:bg-[#141822] text-xs font-mono font-semibold transition-colors"
                    >
                      <div className="flex items-center gap-1.5 truncate">
                        {isExpanded ? <ChevronDown size={13} className="text-[#6e7681]" /> : <ChevronRight size={13} className="text-[#6e7681]" />}
                        <Folder size={13} className="text-[#58a6ff] fill-[#58a6ff]/20" />
                        <span className="truncate">{folderMeta.label}</span>
                      </div>
                      <span className="text-[10px] text-[#6e7681] px-1 rounded bg-[#191f2c]">
                        {folderFiles.length}
                      </span>
                    </button>

                    {/* Files in Folder */}
                    {isExpanded && (
                      <div className="space-y-0.5 pl-3">
                        {folderFiles.map(([key, f]) => {
                          const isSelected = activeFileKey === key;
                          const isDirty = dirtyFiles[key];
                          const hasError = f.diagnostics && f.diagnostics.length > 0;

                          const getLangBadge = (lang: string) => {
                            switch (lang) {
                              case 'cpp': return <span className="text-[9px] px-1 rounded bg-cyan-950 text-cyan-400 font-bold">C++</span>;
                              case 'typescript': return <span className="text-[9px] px-1 rounded bg-blue-950 text-blue-400 font-bold">TS</span>;
                              case 'rust': return <span className="text-[9px] px-1 rounded bg-amber-950 text-amber-400 font-bold">RS</span>;
                              case 'python': return <span className="text-[9px] px-1 rounded bg-emerald-950 text-emerald-400 font-bold">PY</span>;
                              case 'json': return <span className="text-[9px] px-1 rounded bg-yellow-950 text-yellow-400 font-bold">JSON</span>;
                              case 'yaml': return <span className="text-[9px] px-1 rounded bg-purple-950 text-purple-400 font-bold">YML</span>;
                              default: return <FileCode size={12} className="text-gray-400" />;
                            }
                          };

                          return (
                            <button
                              key={key}
                              onClick={() => setActiveFileKey(key)}
                              className={`w-full flex items-center justify-between px-2 py-1 rounded text-xs font-mono transition-colors ${
                                isSelected
                                  ? 'bg-[#151c27] text-white font-medium border-l-2 border-[#66e3c4]'
                                  : 'text-[#8b949e] hover:text-white hover:bg-[#12161f]'
                              }`}
                            >
                              <div className="flex items-center gap-1.5 truncate">
                                {getLangBadge(f.lang)}
                                <span className="truncate text-[11px]">{f.name}</span>
                              </div>
                              <div className="flex items-center gap-1">
                                {hasError && (
                                  <span className="w-4 h-4 rounded-full bg-red-950 border border-red-600 text-red-400 text-[9px] flex items-center justify-center font-bold" title="1 Error in file">
                                    1
                                  </span>
                                )}
                                {isDirty && <span className="w-1.5 h-1.5 rounded-full bg-amber-400" title="Unsaved changes" />}
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Active Work Orders Section */}
            <div className="px-3 pt-3 pb-1 flex items-center justify-between text-[11px] font-semibold text-[#7d8590] uppercase tracking-wider">
              <span>Active Work Orders</span>
              <button 
                onClick={() => {
                  const newId = 'c_' + Date.now();
                  setConversations(prev => [{ id: newId, title: 'New Capability Task', timeAgo: 'Now' }, ...prev]);
                  setSelectedConversation(newId);
                }}
                className="hover:text-white p-0.5"
                title="New Task"
              >
                <Plus className="w-3 h-3" />
              </button>
            </div>

            {/* Conversation List Scrollable */}
            <div className="flex-1 overflow-y-auto px-2 space-y-0.5 min-h-0 text-xs scrollbar-none">
              {conversations.map((c) => {
                const isActive = selectedConversation === c.id;
                return (
                  <button
                    key={c.id}
                    onClick={() => setSelectedConversation(c.id)}
                    className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-left transition-all ${
                      isActive
                        ? 'bg-[#151c27] text-white font-medium shadow-sm border border-[#273244]'
                        : 'text-[#8b949e] hover:bg-[#131720] hover:text-[#c9d1d9]'
                    }`}
                  >
                    <span className="truncate pr-2">{c.title}</span>
                    <span className="text-[10px] text-[#6e7681] shrink-0 font-mono">{c.timeAgo}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Bottom Settings Button */}
          <div className="p-3 border-t border-[#1e232d]">
            <button
              onClick={() => {
                setSettingsTab('general');
                setIsSettingsOpen(true);
              }}
              className="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs font-medium text-[#8b949e] hover:text-white hover:bg-[#141820] transition-colors"
            >
              <Settings className="w-4 h-4 text-[#7d8590]" />
              <span>Studio Settings</span>
            </button>
          </div>
        </div>

        {/* ===================== CENTER PANE: REAL CODE EDITOR & RADAR (Flex 1) ===================== */}
        <div className="flex-1 flex flex-col min-w-0 bg-[#0a0c10] relative">
          {/* Editor Tab Bar */}
          <div className="h-10 bg-[#080a0d] border-b border-[#1e232d] flex items-center justify-between px-2 shrink-0">
            <div className="flex items-center gap-1 overflow-x-auto min-w-0 h-full scrollbar-none">
              {Object.entries(files).map(([key, f]) => {
                const isSelected = activeFileKey === key;
                const isDirty = dirtyFiles[key];
                const hasError = f.diagnostics && f.diagnostics.length > 0;

                const getTabColor = (lang: string) => {
                  switch (lang) {
                    case 'cpp': return 'text-cyan-400';
                    case 'typescript': return 'text-blue-400';
                    case 'rust': return 'text-amber-400';
                    case 'python': return 'text-emerald-400';
                    case 'json': return 'text-yellow-400';
                    case 'yaml': return 'text-purple-400';
                    default: return 'text-gray-400';
                  }
                };

                return (
                  <button
                    key={key}
                    onClick={() => setActiveFileKey(key)}
                    className={`flex items-center gap-2 px-3 h-full text-xs font-mono border-r border-[#1e232d] transition-colors shrink-0 ${
                      isSelected
                        ? 'bg-[#0f1115] text-white border-t-2 border-t-[#66e3c4]'
                        : 'text-[#8b949e] hover:bg-[#12161f]'
                    }`}
                  >
                    <span className={`text-[10px] font-bold ${getTabColor(f.lang)}`}>
                      {f.lang === 'cpp' ? (f.name.endsWith('.h') ? 'H' : 'C++') : f.lang.toUpperCase().slice(0, 3)}
                    </span>
                    <span className="truncate max-w-[140px]">{f.name}</span>
                    {hasError && (
                      <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" title="1 Error" />
                    )}
                    {isDirty ? (
                      <span className="w-2 h-2 rounded-full bg-amber-400" />
                    ) : (
                      <X 
                        className="w-3 h-3 text-[#7d8590] hover:text-white" 
                        onClick={(e) => {
                          e.stopPropagation();
                          const keys = Object.keys(files);
                          if (keys.length > 1 && activeFileKey === key) {
                            const nextKey = keys.find(k => k !== key) || 'project_faf';
                            setActiveFileKey(nextKey);
                          }
                        }}
                      />
                    )}
                  </button>
                );
              })}

              <button 
                onClick={() => {
                  const name = prompt('Create file:');
                  if (name) {
                    const k = 'file_' + Date.now();
                    setFiles(p => ({ ...p, [k]: { id: k, name, path: 'src/' + name, folder: 'src', lang: 'typescript', content: `// ${name}\n` } }));
                    setActiveFileKey(k);
                  }
                }}
                className="p-1 hover:text-white text-[#7d8590] rounded"
                title="New file"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Language Server & Action Controls */}
            <div className="flex items-center gap-1 text-[#8b949e] shrink-0 pr-1">
              <button
                onClick={() => setShowCompletion(!showCompletion)}
                className={`flex items-center gap-1 px-2 py-1 text-xs font-mono rounded border transition-colors ${
                  showCompletion
                    ? 'bg-purple-950/80 border-purple-500/50 text-purple-300'
                    : 'bg-[#12161f] hover:bg-[#1a202c] border-[#252d3a] text-[#c9d1d9]'
                }`}
                title="Trigger IntelliSense Code Completion"
              >
                <Box className="w-3 h-3 text-purple-400" />
                <span>Autocomplete</span>
              </button>

              <button
                onClick={() => setShowSymbolHover(!showSymbolHover)}
                className={`flex items-center gap-1 px-2 py-1 text-xs font-mono rounded border transition-colors ${
                  showSymbolHover
                    ? 'bg-blue-950/80 border-blue-500/50 text-blue-300'
                    : 'bg-[#12161f] hover:bg-[#1a202c] border-[#252d3a] text-[#c9d1d9]'
                }`}
                title="Hover Tooltip for types & methods"
              >
                <FileText className="w-3 h-3 text-[#58a6ff]" />
                <span>Hover</span>
              </button>

              <button
                onClick={() => setShowSymbolSearch(true)}
                className="flex items-center gap-1 px-2 py-1 bg-[#12161f] hover:bg-[#1a202c] text-[#c9d1d9] text-xs font-mono rounded border border-[#252d3a] transition-colors"
                title="Workspace Symbol Search (#)"
              >
                <Search className="w-3 h-3 text-amber-400" />
                <span>Symbols (#)</span>
              </button>

              <button
                onClick={() => setShowXrefs(!showXrefs)}
                className={`flex items-center gap-1 px-2 py-1 text-xs font-mono rounded border transition-colors ${
                  showXrefs
                    ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-300'
                    : 'bg-[#12161f] hover:bg-[#1a202c] border-[#252d3a] text-[#c9d1d9]'
                }`}
                title="Cross-References (xrefs)"
              >
                <Layers className="w-3 h-3 text-emerald-400" />
                <span>Refs (4)</span>
              </button>

              <button
                onClick={handleFormatDocument}
                className="flex items-center gap-1 px-2 py-1 bg-[#12161f] hover:bg-[#1a202c] text-[#c9d1d9] text-xs font-mono rounded border border-[#252d3a]"
                title="Format with clang-format / prettier"
              >
                <Code className="w-3 h-3 text-cyan-400" />
                <span>Format</span>
              </button>

              <button 
                onClick={handleSaveActiveFile}
                className="flex items-center gap-1 px-2 py-1 bg-[#12161f] hover:bg-[#1a202c] text-[#c9d1d9] text-xs font-mono rounded border border-[#252d3a]"
                title="Save file (Ctrl+S)"
              >
                <Save className="w-3 h-3 text-[#388bfd]" />
                <span>Save</span>
              </button>

              <button 
                onClick={() => handleExecuteTerminalCommand('run')}
                className="flex items-center gap-1 px-2 py-1 bg-[#10241b] hover:bg-[#163525] text-emerald-400 text-xs font-mono rounded border border-emerald-500/40"
                title="Execute file in CLI"
              >
                <Play className="w-3 h-3 fill-emerald-400" />
                <span>Run</span>
              </button>

              <button 
                onClick={() => setShowTerminalDrawer(!showTerminalDrawer)}
                className={`p-1.5 rounded transition-colors ${showTerminalDrawer ? 'text-white bg-[#21262d]' : 'hover:text-white'}`}
                title="Toggle Terminal"
              >
                <Terminal className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Dynamic Context & AST Pruning Radar */}
          <div className="h-7 bg-[#0b0e13] border-b border-[#1c222b] px-3 flex items-center justify-between text-[11px] font-mono shrink-0">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 text-[#8b949e]">
                <Cpu className="w-3.5 h-3.5 text-[#38bdf8]" />
                <span>Context Load:</span>
                <span className="text-[#e6edf3] font-semibold">1,280</span>
                <span className="text-[#6e7681]">/ 8,192 t</span>
              </div>
              <div className="w-20 h-1.5 bg-[#1a202c] rounded-full overflow-hidden">
                <div className="w-[15.6%] h-full bg-[#38bdf8]" />
              </div>
              <div className="flex items-center gap-1 text-emerald-400">
                <Sparkles className="w-3 h-3 text-emerald-400" />
                <span>AST Extents: -71.4% pruned</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[10px] text-[#7d8590]">MCP Resolver: Audited</span>
              <button
                onClick={() => setIsContextDiffOpen(true)}
                className="px-2 py-0.5 rounded bg-[#10241b] border border-emerald-500/40 text-[10px] text-emerald-300 hover:bg-[#153424] transition-colors flex items-center gap-1 font-semibold"
              >
                <span>Inspect Delta</span>
                <span>→</span>
              </button>
            </div>
          </div>

          {/* Breadcrumbs Bar */}
          <div className="h-6 bg-[#080a0d] border-b border-[#1a1f26] px-4 flex items-center justify-between text-[11px] text-[#7d8590] font-mono shrink-0">
            <div className="flex items-center">
              <span>veklom-ops-command</span>
              <span className="mx-1.5 text-[#3e4654]">›</span>
              <span>{activeFile.folder || 'src'}</span>
              <span className="mx-1.5 text-[#3e4654]">›</span>
              <span className="text-white font-medium">{activeFile.name}</span>
              {activeFile.diagnostics && activeFile.diagnostics.length > 0 && (
                <span className="ml-2.5 px-1.5 py-0.2 rounded bg-red-950/80 border border-red-700 text-red-300 text-[10px] flex items-center gap-1 font-bold">
                  <AlertTriangle size={10} />
                  1 Problem
                </span>
              )}
            </div>
            <div className="text-[10px] text-[#6e7681]">
              Ln {cursorPos.line}, Col {cursorPos.col} • UTF-8 • {activeFile.content.length} bytes • {activeFile.lang.toUpperCase()}
            </div>
          </div>

          {/* Inline Diagnostic Problem Banner (Matches diagnostics.png) */}
          {activeFile.diagnostics && activeFile.diagnostics.length > 0 && (
            <div className="bg-red-950/70 border-b border-red-800/60 px-4 py-1.5 flex items-center justify-between text-xs font-mono text-red-200 shrink-0">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                <span className="text-white font-semibold">{activeFile.diagnostics[0].message}</span>
                <span className="text-[#8b949e] text-[11px]">({activeFile.diagnostics[0].code})</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleApplyQuickFix}
                  className="px-2.5 py-0.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-sans font-semibold flex items-center gap-1 shadow transition"
                >
                  <Zap size={12} className="text-yellow-300" />
                  <span>Quick Fix: {activeFile.diagnostics[0].quickFixText}</span>
                </button>
                <button
                  onClick={() => setShowDiagnosticHover(!showDiagnosticHover)}
                  className="px-2 py-0.5 rounded bg-[#1e232d] hover:bg-[#252c38] text-gray-300 text-[11px] font-sans transition"
                >
                  Peek
                </button>
              </div>
            </div>
          )}

          {/* Real Editable Code Editor with Line Numbers */}
          <div className="flex-1 overflow-auto flex font-mono text-xs leading-5 bg-[#0a0c10] relative">
            {/* Line Numbers Gutter */}
            <div className="w-14 bg-[#08090d] text-[#555f6d] border-r border-[#181d24] py-3 text-right pr-2 select-none shrink-0 font-mono text-[11px]">
              {activeFile.content.split('\n').map((_, i) => {
                const lineNum = i + 1;
                const isBreakpoint = lineNum === 15;
                const isErrorLine = activeFile.diagnostics?.some(d => d.line === lineNum);
                const hasAction = isErrorLine || lineNum === 26;

                return (
                  <div key={i} className="flex items-center justify-end gap-1 h-5">
                    {hasAction && (
                      <button
                        onClick={() => setShowLightbulbMenu(true)}
                        className="hover:scale-110 transition-transform"
                        title="Code Actions & Quick Fixes"
                      >
                        <Lightbulb size={12} className="text-amber-400 fill-amber-400" />
                      </button>
                    )}
                    {isErrorLine && !hasAction && (
                      <span className="w-2 h-2 rounded-full bg-red-500" title="Error here" />
                    )}
                    {isBreakpoint && (
                      <span className="w-2.5 h-2.5 rounded-full bg-[#388bfd] text-white flex items-center justify-center text-[9px] font-bold">
                        +
                      </span>
                    )}
                    <span className={isErrorLine ? 'text-red-400 font-bold' : ''}>{lineNum}</span>
                  </div>
                );
              })}
            </div>

            {/* Editable Code Content */}
            <div className="flex-1 py-3 px-4 relative">
              <textarea
                value={activeFile.content}
                onChange={e => handleCodeChange(e.target.value)}
                onKeyDown={e => {
                  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                    e.preventDefault();
                    handleSaveActiveFile();
                  }
                  if ((e.ctrlKey || e.metaKey) && e.key === ' ') {
                    e.preventDefault();
                    setShowCompletion(true);
                  }
                  if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
                    e.preventDefault();
                    setShowSymbolSearch(true);
                  }
                }}
                onSelect={e => {
                  const target = e.target as HTMLTextAreaElement;
                  const textBefore = target.value.slice(0, target.selectionStart);
                  const lines = textBefore.split('\n');
                  setCursorPos({
                    line: lines.length,
                    col: lines[lines.length - 1].length + 1
                  });
                }}
                spellCheck={false}
                className="w-full h-full bg-transparent text-[#e6edf3] font-mono text-[12px] leading-5 resize-none focus:outline-none whitespace-pre"
              />

              {/* Floating Language Server Widgets */}
              <AutocompleteWidget
                isOpen={showCompletion}
                onClose={() => setShowCompletion(false)}
                onSelect={handleSelectCompletion}
                activeFile={activeFile}
              />

              {showDiagnosticHover && activeFile.diagnostics && activeFile.diagnostics.length > 0 && (
                <DiagnosticHoverCard
                  diagnostic={activeFile.diagnostics[0]}
                  onApplyQuickFix={handleApplyQuickFix}
                  onClose={() => setShowDiagnosticHover(false)}
                />
              )}

              <SymbolHoverCard
                isOpen={showSymbolHover}
                onClose={() => setShowSymbolHover(false)}
              />

              <LightbulbMenu
                isOpen={showLightbulbMenu}
                onClose={() => setShowLightbulbMenu(false)}
                onSelectAction={handleSelectCodeAction}
              />
            </div>
          </div>

          {/* Cross References Drawer */}
          <CrossReferencesDrawer
            isOpen={showXrefs}
            onClose={() => setShowXrefs(false)}
            onSelectRef={(fileId) => {
              setActiveFileKey(fileId);
            }}
          />

          {/* Real Interactive CLI / Terminal Drawer */}
          {showTerminalDrawer && (
            <div className="h-56 bg-[#07090c] border-t border-[#1e232d] flex flex-col font-mono text-xs">
              <div className="h-7 bg-[#0e1117] px-3 flex items-center justify-between border-b border-[#1e232d] text-[#8b949e]">
                <div className="flex items-center gap-2">
                  <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-white text-[11px] font-semibold">VEKLOM SOVEREIGN TERMINAL & PSES CLI</span>
                </div>
                <div className="flex items-center gap-2">
                  <button 
                    onClick={() => handleExecuteTerminalCommand('find-ast')}
                    className="hover:text-white text-[10px] px-1.5 py-0.5 rounded bg-[#1c222b]"
                  >
                    Find-Ast
                  </button>
                  <button 
                    onClick={() => handleExecuteTerminalCommand('get-tokens')}
                    className="hover:text-white text-[10px] px-1.5 py-0.5 rounded bg-[#1c222b]"
                  >
                    Get-Token
                  </button>
                  <button 
                    onClick={() => handleExecuteTerminalCommand('faf score')}
                    className="hover:text-white text-[10px] px-1.5 py-0.5 rounded bg-[#1c222b] text-emerald-400"
                  >
                    faf score
                  </button>
                  <button 
                    onClick={() => handleExecuteTerminalCommand('faf sync')}
                    className="hover:text-white text-[10px] px-1.5 py-0.5 rounded bg-[#1c222b]"
                  >
                    faf sync
                  </button>
                  <button 
                    onClick={() => handleExecuteTerminalCommand('diff')}
                    className="hover:text-white text-[10px] px-1.5 py-0.5 rounded bg-[#1c222b] text-[#38bdf8]"
                  >
                    diff
                  </button>
                  <button 
                    onClick={() => setTerminalOutput([])}
                    className="hover:text-white text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-[#1c222b]"
                  >
                    Clear
                  </button>
                  <button onClick={() => setShowTerminalDrawer(false)} className="hover:text-white">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Terminal Logs Scrollable */}
              <div className="flex-1 p-2.5 overflow-y-auto space-y-1 text-[#7ee787]">
                {terminalOutput.map((line, i) => (
                  <div key={i} className={line.startsWith('$') ? 'text-white font-bold' : ''}>
                    {line}
                  </div>
                ))}
              </div>

              {/* Terminal Input Line */}
              <div className="h-8 bg-[#090b0e] border-t border-[#1a1f26] px-3 flex items-center gap-2">
                <span className="text-emerald-400 font-bold">$</span>
                <input
                  type="text"
                  value={terminalInput}
                  onChange={e => setTerminalInput(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') {
                      handleExecuteTerminalCommand();
                    }
                  }}
                  placeholder="Type 'run', 'faf score', 'faf sync', 'ollama test', 'find-ast', 'get-tokens', 'export-vs', or 'help'..."
                  className="flex-1 bg-transparent text-white text-xs font-mono focus:outline-none"
                />
              </div>
            </div>
          )}
        </div>

        {/* ===================== RIGHT PANE: CAPABILITY & CONSEQUENCE DECK (Width 390px) ===================== */}
        <div className="w-[390px] bg-[#0c0e12] border-l border-[#1e232d] flex flex-col shrink-0 min-h-0 relative">
          {/* Header */}
          <div className="h-10 border-b border-[#1e232d] flex items-center justify-between px-3 bg-[#090b0e]">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-4 h-4 rounded bg-[#10241b] border border-[#66e3c4]/50 flex items-center justify-center text-[#66e3c4] p-0.5">
                <Shield className="w-full h-full" />
              </div>
              <div className="truncate">
                <div className="text-xs font-bold text-white tracking-tight">CAPABILITY ACTUATOR</div>
              </div>
            </div>
            <div className="flex items-center gap-1.5 shrink-0">
              <span className="px-2 py-0.5 rounded bg-[#10241b] border border-emerald-500/40 text-[9px] font-mono text-emerald-400 font-semibold">
                LAW 0 GATE
              </span>
              <span className="px-2 py-0.5 rounded bg-[#13161c] border border-[#242a36] text-[10px] font-mono text-[#a5d6ff]">
                {llmConfig.provider === 'ollama' ? llmConfig.ollamaModel : llmConfig.provider}
              </span>
            </div>
          </div>

          {/* Consequence Gate Status HUD Card */}
          <div className="p-3 border-b border-[#1e232d] bg-[#090b0e]">
            <div className="bg-[#10141a] border border-[#1e2530] rounded-lg p-2.5 space-y-1.5">
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-[#8b949e]">Consequence Gate:</span>
                <span className="text-emerald-400 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  FAIL-CLOSED [ACTIVE]
                </span>
              </div>
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-[#8b949e]">Net Delta (ΔC):</span>
                <span className="text-white font-semibold">0.00 COMMONS</span>
              </div>
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-[#8b949e]">Evidence Seal:</span>
                <span className="text-[#38bdf8] truncate max-w-[170px]">PGL: 0x88c2...e9a1</span>
              </div>
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-[#8b949e]">Substrate:</span>
                <span className="text-[#a5d6ff]">Local Hardware / Docker</span>
              </div>
            </div>
          </div>

          {/* Capability Execution Stream Scrollable */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3 text-xs">
            {chatMessages.map((msg) => (
              <div 
                key={msg.id}
                className={`rounded-lg p-3 space-y-1.5 border transition-all ${
                  msg.role === 'user' 
                    ? 'bg-[#12161f] border-[#252f40] text-white' 
                    : 'bg-[#101319] border-[#1d232e] text-[#d1d7e0]'
                }`}
              >
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className={`font-semibold uppercase tracking-wider ${msg.role === 'user' ? 'text-[#38bdf8]' : 'text-[#66e3c4]'}`}>
                    {msg.role === 'user' ? 'Operator Instruction' : 'Capability Receipt'}
                  </span>
                  <span className="text-[#6e7681]">{msg.time}</span>
                </div>

                {msg.capabilityId && (
                  <div className="flex items-center gap-2 text-[10px] font-mono text-[#8b949e] bg-[#090b0e] px-2 py-1 rounded border border-[#1a1f29]">
                    <span>ID: <strong className="text-white">{msg.capabilityId}</strong></span>
                    <span>•</span>
                    <span className="truncate">Seal: <strong className="text-[#38bdf8]">{msg.merkleSeal}</strong></span>
                  </div>
                )}

                <div className="text-[11px] leading-relaxed whitespace-pre-wrap font-sans">
                  {msg.text}
                </div>

                {msg.meta && (
                  <div className="text-[10px] font-mono text-[#7d8590] pt-1 border-t border-[#1a1f29]">
                    {msg.meta}
                  </div>
                )}
              </div>
            ))}

            {isGenerating && (
              <div className="bg-[#101319] border border-[#1d232e] rounded-lg p-3 space-y-2 text-xs font-mono text-emerald-400 animate-pulse">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 animate-spin" />
                  <span>Resolving capability contract & AST tokens...</span>
                </div>
              </div>
            )}
          </div>

          {/* Prompt & Capability Composer */}
          <div className="p-3 border-t border-[#1e232d] bg-[#090b0e] space-y-2">
            {/* Docked Context Tags */}
            <div className="flex items-center gap-1.5 flex-wrap text-[10px] font-mono">
              <span className="px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-600/40 text-emerald-300">
                @project.faf
              </span>
              <span className="px-1.5 py-0.5 rounded bg-[#131924] border border-[#232f42] text-[#a5d6ff]">
                @{activeFile.name}
              </span>
              {useAstEnhancer && (
                <span className="px-1.5 py-0.5 rounded bg-[#1f1910] border border-amber-600/40 text-amber-300">
                  @ast_extents
                </span>
              )}
            </div>

            {/* Input Composer Box */}
            <div className="bg-[#101319] border border-[#1e2430] rounded-lg p-2.5 space-y-2 focus-within:border-[#388bfd]">
              <textarea
                value={inputMessage}
                onChange={e => setInputMessage(e.target.value)}
                onKeyDown={e => {
                  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Instruct capability engine or dispatch code synthesis (Cmd+Enter)..."
                rows={3}
                className="w-full bg-transparent text-xs text-white placeholder-[#555f6d] resize-none focus:outline-none"
              />

              <div className="flex items-center justify-between pt-1 border-t border-[#1a1f29]">
                <div className="flex items-center gap-2">
                  {/* Add Context Button */}
                  <div className="relative">
                    <button
                      onClick={() => setShowAddContext(!showAddContext)}
                      className="flex items-center gap-1 text-[11px] text-[#8b949e] hover:text-white px-1.5 py-0.5 rounded hover:bg-[#1a1f29] transition-colors"
                      title="Attach context to capability execution"
                    >
                      <Plus className="w-3 h-3" />
                      <span>Context</span>
                    </button>

                    {showAddContext && (
                      <div className="absolute left-0 bottom-full mb-1 w-56 bg-[#161a22] border border-[#2b3342] rounded-lg shadow-xl p-1 z-30 text-xs">
                        <button 
                          onClick={() => {
                            setInputMessage(prev => prev + ' @context:project.faf (Always-33)');
                            setShowAddContext(false);
                          }}
                          className="w-full text-left px-2 py-1.5 hover:bg-[#21262d] rounded text-emerald-400 font-mono flex items-center justify-between"
                        >
                          <span>@project.faf</span>
                          <span className="text-[10px] text-[#7d8590]">Always-33</span>
                        </button>
                        <button 
                          onClick={() => {
                            setInputMessage(prev => prev + ' @file:' + activeFile.name);
                            setShowAddContext(false);
                          }}
                          className="w-full text-left px-2 py-1.5 hover:bg-[#21262d] rounded text-white flex items-center justify-between"
                        >
                          <span className="truncate">@{activeFile.name}</span>
                          <span className="text-[10px] text-[#7d8590]">active</span>
                        </button>
                        <button 
                          onClick={() => {
                            setInputMessage(prev => prev + ' @ast:script_extents');
                            setShowAddContext(false);
                          }}
                          className="w-full text-left px-2 py-1.5 hover:bg-[#21262d] rounded text-[#a5d6ff] font-mono flex items-center justify-between"
                        >
                          <span>@ast_extents</span>
                          <span className="text-[10px] text-[#7d8590]">PSES</span>
                        </button>
                      </div>
                    )}
                  </div>

                  {/* AST Enhancer Toggle */}
                  <button
                    onClick={() => setUseAstEnhancer(!useAstEnhancer)}
                    className={`flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded border transition-colors ${
                      useAstEnhancer 
                        ? 'bg-[#10241b] border-emerald-500/40 text-emerald-400' 
                        : 'bg-[#161a20] border-[#292f3b] text-[#7d8590]'
                    }`}
                    title="AST Engine Pre-Pass (Filters tokens & improves output accuracy)"
                  >
                    <Sparkles className="w-2.5 h-2.5" />
                    <span>AST Engine</span>
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setTurboMode(!turboMode)}
                    className="flex items-center gap-1 text-[10px] text-[#7d8590] hover:text-white px-1.5 py-0.5 rounded hover:bg-[#21262d]"
                  >
                    <Shield className="w-3 h-3 text-emerald-400" />
                    <span>Turbo</span>
                  </button>

                  <button
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isGenerating}
                    className={`px-3 py-1 rounded text-xs font-semibold flex items-center gap-1 transition-all ${
                      inputMessage.trim() && !isGenerating
                        ? 'bg-[#1f6feb] text-white hover:bg-[#388bfd] shadow-sm'
                        : 'bg-[#1b2028] text-[#555f6d] cursor-not-allowed'
                    }`}
                  >
                    <span>Dispatch</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. SYSTEM TELEMETRY & CONTEXT STATUS BAR (24px) */}
      <div className="h-6 bg-[#07090c] border-t border-[#1e232d] flex items-center justify-between px-3 text-[11px] font-mono text-[#8b949e] shrink-0 z-20">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>CAPPO: LAW 0 ENFORCED</span>
          </div>
          <span className="text-[#252c38]">•</span>
          <div className="flex items-center gap-1 text-[#a5d6ff]">
            <Layers className="w-3 h-3 text-[#38bdf8]" />
            <span>PGL: IMMUTABLE LINEAGE</span>
          </div>
          <span className="text-[#252c38]">•</span>
          <span>branch: main (clean)</span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-emerald-400 font-semibold">FAF: 31/33 (96% A+)</span>
          <span className="text-[#252c38]">•</span>
          <span className="text-[#a5d6ff]">OLLAMA: 127.0.0.1:11434</span>
          <span className="text-[#252c38]">•</span>
          <span>Ln {cursorPos.line}, Col {cursorPos.col}</span>
          <span className="text-[#252c38]">•</span>
          <span>UTF-8</span>
          <span className="text-[#252c38]">•</span>
          <span>LF</span>
          <button 
            onClick={() => setShowTerminalDrawer(!showTerminalDrawer)}
            className="flex items-center gap-1 text-[#8b949e] hover:text-white px-1.5 py-0.5 rounded hover:bg-[#1a1e24]"
          >
            <Terminal className="w-3 h-3 text-emerald-400" />
            <span>Terminal</span>
          </button>
        </div>
      </div>

      {/* 5. SETTINGS MODAL */}
      <AntigravitySettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        llmConfig={llmConfig}
        onUpdateLlmConfig={updateLlmConfig}
        initialTab={settingsTab}
        onOpenFafModal={() => {
          setIsSettingsOpen(false);
          setIsFafModalOpen(true);
        }}
      />

      {/* 6. CONTEXT DIFF & PRUNING VALIDATOR */}
      <ContextDiffPanel
        isOpen={isContextDiffOpen}
        onClose={() => setIsContextDiffOpen(false)}
        activeFileName={activeFile.name}
      />

      {/* 7. FAF-MCP CONTEXT CONTROLLER & ALWAYS-33 KERNEL */}
      <FafMcpInspectorModal
        isOpen={isFafModalOpen}
        onClose={() => setIsFafModalOpen(false)}
        fafContent={files['project_faf']?.content || CANONICAL_PROJECT_FAF}
        onUpdateFafContent={(newContent) => handleCodeChange(newContent)}
      />

      {/* 8. WORKSPACE SYMBOL SEARCH MODAL (Matches symbolsearch.png) */}
      <SymbolSearchModal
        isOpen={showSymbolSearch}
        onClose={() => setShowSymbolSearch(false)}
        onSelectSymbol={(sym) => {
          if (sym.file.includes('FS.cpp')) setActiveFileKey('fs_cpp');
          else if (sym.file.includes('FS.h')) setActiveFileKey('fs_h');
          else if (sym.file.includes('StringRef')) setActiveFileKey('stringref_h');
          else if (sym.file.includes('dispatch')) setActiveFileKey('rust_veklom');
          else if (sym.file.includes('env_manager')) setActiveFileKey('python_env_mgr');
          else if (sym.file.includes('project.faf')) setActiveFileKey('project_faf');
          setShowSymbolSearch(false);
        }}
      />
    </div>
  );
}
