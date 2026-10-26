import React, { useState, useEffect } from 'react';
import {
  X,
  ChevronRight,
  ArrowLeft,
  Search,
  Plus,
  Settings,
  Folder,
  History,
  FileCode,
  Check,
  Globe,
  Terminal,
  Shield,
  Layers,
  Sparkles,
  Play,
  RotateCw,
  ExternalLink,
  ChevronDown,
  Trash2,
  Edit2,
  Cpu,
  Key,
  Server,
  Download,
  Copy
} from 'lucide-react';
import { testOllamaConnection, LlmConfig, DEFAULT_LLM_CONFIG, POPULAR_OLLAMA_MODELS } from '../../services/localLlmService';

interface AntigravitySettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  llmConfig: LlmConfig;
  onUpdateLlmConfig: (config: LlmConfig) => void;
  initialTab?: 'general' | 'cli_project' | 'network_permissions' | 'tool_permissions' | 'models' | 'visual_studio' | 'faf_mcp';
  onOpenFafModal?: () => void;
}

export function AntigravitySettingsModal({
  isOpen,
  onClose,
  llmConfig,
  onUpdateLlmConfig,
  initialTab = 'general',
  onOpenFafModal
}: AntigravitySettingsModalProps) {
  const [activeMenu, setActiveMenu] = useState<'general' | 'application' | 'appearance' | 'notifications' | 'models' | 'cli_project' | 'conversations' | 'visual_studio' | 'faf_mcp'>(initialTab as any);
  const [subView, setSubView] = useState<'none' | 'network_permissions' | 'tool_permissions' | 'file_access'>('none');
  const [queuedMessages, setQueuedMessages] = useState<'queue' | 'send_immediately'>('queue');
  const [securityPreset, setSecurityPreset] = useState<'turbo' | 'strict' | 'relaxed'>('turbo');
  const [planReviewPolicy, setPlanReviewPolicy] = useState<'always_proceed' | 'ask_first'>('always_proceed');

  // Ollama Connection State
  const [testingOllama, setTestingOllama] = useState(false);
  const [ollamaStatus, setOllamaStatus] = useState<{ connected: boolean; message: string; availableModels: string[] } | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);
  const [copiedVsCode, setCopiedVsCode] = useState(false);

  // Network permissions list
  const [networkUrls, setNetworkUrls] = useState<{ url: string; permission: string }[]>([
    { url: '127.0.0.1:11434 (Ollama)', permission: 'Allow' },
    { url: '127.0.0.1', permission: 'Allow' },
    { url: 'civictrust.us', permission: 'Allow' },
    { url: 'claude.ai', permission: 'Allow' },
    { url: 'docs.anchorbrowser.io', permission: 'Allow' },
    { url: 'github.com', permission: 'Allow' },
    { url: 'trust3.ai', permission: 'Allow' },
    { url: 'veklom.com', permission: 'Allow' },
    { url: 'wix.com', permission: 'Allow' },
  ]);

  const [newUrlInput, setNewUrlInput] = useState('');
  const [showAddUrl, setShowAddUrl] = useState(false);

  if (!isOpen) return null;

  const handleTestOllama = async () => {
    setTestingOllama(true);
    setOllamaStatus(null);
    const res = await testOllamaConnection(llmConfig.ollamaUrl);
    setTestingOllama(false);
    if (res.connected) {
      setOllamaStatus({
        connected: true,
        message: `Successfully connected to Ollama daemon! Found ${res.models.length} model(s).`,
        availableModels: res.models
      });
      if (res.models.length > 0 && !res.models.includes(llmConfig.ollamaModel)) {
        onUpdateLlmConfig({ ...llmConfig, ollamaModel: res.models[0] });
      }
    } else {
      setOllamaStatus({
        connected: false,
        message: res.error || 'Failed to reach Ollama daemon.',
        availableModels: POPULAR_OLLAMA_MODELS
      });
    }
  };

  const handleAddUrl = () => {
    if (newUrlInput.trim()) {
      setNetworkUrls(prev => [...prev, { url: newUrlInput.trim(), permission: 'Allow' }]);
      setNewUrlInput('');
      setShowAddUrl(false);
    }
  };

  const handleRemoveUrl = (index: number) => {
    setNetworkUrls(prev => prev.filter((_, i) => i !== index));
  };

  const handleCopyVsCodeConfig = () => {
    const launchConfig = {
      version: '0.2.0',
      configurations: [
        {
          name: 'PowerShell: Launch Current File (PSES)',
          type: 'PowerShell',
          request: 'launch',
          script: '${file}',
          cwd: '${workspaceFolder}'
        },
        {
          name: 'Local Ollama: Optimize Output Engine',
          type: 'node',
          request: 'launch',
          program: '${workspaceFolder}/scripts/runLocalLlmPipeline.mjs'
        }
      ]
    };
    navigator.clipboard.writeText(JSON.stringify(launchConfig, null, 2));
    setCopiedVsCode(true);
    setTimeout(() => setCopiedVsCode(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 font-sans text-sm animate-fadeIn">
      <div 
        className="w-full max-w-[900px] h-[640px] bg-[#16181d] border border-[#262a33] rounded-2xl shadow-2xl flex overflow-hidden text-[#e6edf3]"
        onClick={e => e.stopPropagation()}
      >
        {/* Left Modal Sidebar */}
        <div className="w-[220px] border-r border-[#242831] bg-[#121418] p-3 flex flex-col justify-between shrink-0">
          <div className="space-y-4">
            <div>
              <div className="text-[11px] font-semibold text-[#7d8590] uppercase tracking-wider px-2 mb-1">Settings</div>
              <nav className="space-y-0.5">
                <button
                  onClick={() => { setActiveMenu('general'); setSubView('none'); }}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    activeMenu === 'general' && subView === 'none'
                      ? 'bg-[#262c36] text-white shadow-sm'
                      : 'text-[#8b949e] hover:bg-[#1a1e24] hover:text-[#c9d1d9]'
                  }`}
                >
                  General
                </button>
                <button
                  onClick={() => { setActiveMenu('models'); setSubView('none'); }}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center justify-between ${
                    activeMenu === 'models' ? 'bg-[#262c36] text-white' : 'text-[#8b949e] hover:bg-[#1a1e24] hover:text-[#c9d1d9]'
                  }`}
                >
                  <span>Models & Ollama</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                </button>
                <button
                  onClick={() => { setActiveMenu('visual_studio'); setSubView('none'); }}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    activeMenu === 'visual_studio' ? 'bg-[#262c36] text-white' : 'text-[#8b949e] hover:bg-[#1a1e24] hover:text-[#c9d1d9]'
                  }`}
                >
                  Visual Studio 2026
                </button>
                <button
                  onClick={() => { setActiveMenu('faf_mcp'); setSubView('none'); }}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center justify-between ${
                    activeMenu === 'faf_mcp' ? 'bg-[#262c36] text-white' : 'text-[#8b949e] hover:bg-[#1a1e24] hover:text-[#c9d1d9]'
                  }`}
                >
                  <span>FAF MCP & Context</span>
                  <span className="text-[10px] font-mono text-emerald-400">96%</span>
                </button>
                <button
                  onClick={() => { setActiveMenu('application'); setSubView('none'); }}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    activeMenu === 'application' ? 'bg-[#262c36] text-white' : 'text-[#8b949e] hover:bg-[#1a1e24] hover:text-[#c9d1d9]'
                  }`}
                >
                  Application
                </button>
                <button
                  onClick={() => { setActiveMenu('appearance'); setSubView('none'); }}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    activeMenu === 'appearance' ? 'bg-[#262c36] text-white' : 'text-[#8b949e] hover:bg-[#1a1e24] hover:text-[#c9d1d9]'
                  }`}
                >
                  Appearance
                </button>
                <button
                  onClick={() => { setActiveMenu('notifications'); setSubView('none'); }}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    activeMenu === 'notifications' ? 'bg-[#262c36] text-white' : 'text-[#8b949e] hover:bg-[#1a1e24] hover:text-[#c9d1d9]'
                  }`}
                >
                  Notifications
                </button>
              </nav>
            </div>

            <div>
              <div className="text-[11px] font-semibold text-[#7d8590] uppercase tracking-wider px-2 mb-1">Projects</div>
              <button
                onClick={() => { setActiveMenu('cli_project'); setSubView('none'); }}
                className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  activeMenu === 'cli_project' && subView === 'none'
                    ? 'bg-[#262c36] text-white shadow-sm'
                    : 'text-[#8b949e] hover:bg-[#1a1e24] hover:text-[#c9d1d9]'
                }`}
              >
                CLI Project
              </button>
            </div>

            <div>
              <div className="text-[11px] font-semibold text-[#7d8590] uppercase tracking-wider px-2 mb-1">Not in Project</div>
              <button
                onClick={() => { setActiveMenu('conversations'); setSubView('none'); }}
                className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  activeMenu === 'conversations' ? 'bg-[#262c36] text-white' : 'text-[#8b949e] hover:bg-[#1a1e24] hover:text-[#c9d1d9]'
                }`}
              >
                Conversations
              </button>
            </div>
          </div>

          <div className="pt-3 border-t border-[#242831] space-y-2">
            <button className="w-full text-left px-2 text-xs text-[#8b949e] hover:text-white transition-colors">
              Shortcuts
            </button>
            <button className="w-full text-left px-2 text-xs text-[#8b949e] hover:text-white transition-colors">
              Provide Feedback
            </button>
            <div className="flex items-center gap-2.5 px-2 pt-2">
              <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-purple-500 via-pink-500 to-amber-400 p-[1px]">
                <div className="w-full h-full rounded-full bg-[#1e2229] flex items-center justify-center text-[10px] font-bold text-white">
                  PF
                </div>
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-xs font-medium text-white truncate">Plugged Finds</div>
                <div className="text-[10px] text-[#7d8590] truncate">pluggedfinds41@gmail.com</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Modal Body */}
        <div className="flex-1 flex flex-col min-w-0 bg-[#16181d] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-[#242831]">
            {subView !== 'none' ? (
              <button
                onClick={() => setSubView('none')}
                className="flex items-center gap-1.5 text-xs text-[#8b949e] hover:text-white transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Back
              </button>
            ) : (
              <div className="text-base font-semibold text-white">
                {activeMenu === 'general' && 'General'}
                {activeMenu === 'models' && 'Models, Ollama & BYOK'}
                {activeMenu === 'visual_studio' && 'Visual Studio 2026 & Editor Services'}
                {activeMenu === 'cli_project' && 'CLI Project'}
                {activeMenu === 'application' && 'Application Settings'}
                {activeMenu === 'appearance' && 'Appearance'}
                {activeMenu === 'notifications' && 'Notification Preferences'}
                {activeMenu === 'conversations' && 'Conversations'}
              </div>
            )}
            <button
              onClick={onClose}
              className="text-[#8b949e] hover:text-white p-1 rounded-md hover:bg-[#232730] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="p-6 space-y-6">
            {/* TAB: Models & Ollama (Real Functioning Engine) */}
            {activeMenu === 'models' && subView === 'none' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-white">Models & Inference Engine</h3>
                  <p className="text-xs text-[#8b949e] mt-0.5">
                    Configure local Ollama, BYOK (Bring Your Own Key), and the output-enhancing AST compiler.
                  </p>
                </div>

                {/* Provider Selection */}
                <div className="bg-[#1b1f26] border border-[#292f3b] rounded-xl p-4 space-y-4">
                  <div>
                    <label className="text-xs font-semibold text-white block mb-1">Active AI Provider</label>
                    <div className="grid grid-cols-2 gap-2">
                      {[
                        { id: 'ollama', label: 'Local Ollama (Offline)', icon: Server },
                        { id: 'custom_endpoint', label: 'Custom HTTP Endpoint', icon: Globe },
                        { id: 'byok_gemini', label: 'BYOK: Google Gemini', icon: Cpu },
                        { id: 'byok_openai', label: 'BYOK: OpenAI / Compatible', icon: Key },
                      ].map((item) => (
                        <button
                          key={item.id}
                          onClick={() => onUpdateLlmConfig({ ...llmConfig, provider: item.id as any })}
                          className={`flex items-center gap-2.5 p-2.5 rounded-lg border text-left text-xs transition-colors ${
                            llmConfig.provider === item.id
                              ? 'bg-[#242b36] border-[#388bfd] text-white font-medium'
                              : 'bg-[#121418] border-[#292f3b] text-[#8b949e] hover:text-white'
                          }`}
                        >
                          <item.icon className="w-4 h-4 text-[#388bfd]" />
                          <span>{item.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Ollama URL & Test Connection */}
                  {llmConfig.provider === 'ollama' && (
                    <div className="space-y-3 pt-2 border-t border-[#292f3b]">
                      <div className="flex items-center justify-between">
                        <label className="text-xs font-semibold text-white">Local Ollama Endpoint</label>
                        <button
                          onClick={handleTestOllama}
                          disabled={testingOllama}
                          className="px-2.5 py-1 bg-[#262c36] hover:bg-[#323946] text-white text-xs font-medium rounded-md border border-[#363f4f] transition-colors flex items-center gap-1.5"
                        >
                          <RotateCw className={`w-3 h-3 ${testingOllama ? 'animate-spin' : ''}`} />
                          <span>{testingOllama ? 'Pinging...' : 'Test Local Connection'}</span>
                        </button>
                      </div>

                      <input
                        type="text"
                        value={llmConfig.ollamaUrl}
                        onChange={e => onUpdateLlmConfig({ ...llmConfig, ollamaUrl: e.target.value })}
                        placeholder="http://localhost:11434"
                        className="w-full bg-[#121418] border border-[#343b49] rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-[#4f8ff7]"
                      />

                      {ollamaStatus && (
                        <div className={`p-2.5 rounded-lg text-xs font-mono border ${
                          ollamaStatus.connected 
                            ? 'bg-[#0f241a] border-emerald-500/40 text-emerald-400' 
                            : 'bg-[#291717] border-red-500/40 text-red-300'
                        }`}>
                          {ollamaStatus.message}
                        </div>
                      )}

                      {/* Model Picker */}
                      <div>
                        <label className="text-xs font-semibold text-white block mb-1">Target Model</label>
                        <select
                          value={llmConfig.ollamaModel}
                          onChange={e => onUpdateLlmConfig({ ...llmConfig, ollamaModel: e.target.value })}
                          className="w-full bg-[#121418] border border-[#343b49] rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-[#4f8ff7]"
                        >
                          {(ollamaStatus?.availableModels || POPULAR_OLLAMA_MODELS).map(m => (
                            <option key={m} value={m}>{m}</option>
                          ))}
                        </select>
                        <div className="text-[11px] text-[#7d8590] mt-1">
                          Tip: Install any model locally in your terminal via <code className="text-[#a5d6ff]">ollama pull qwen2.5-coder</code> or <code className="text-[#a5d6ff]">ollama pull codellama</code>.
                        </div>
                      </div>
                    </div>
                  )}

                  {/* BYOK API Key Input */}
                  {llmConfig.provider !== 'ollama' && (
                    <div className="space-y-3 pt-2 border-t border-[#292f3b]">
                      {llmConfig.provider === 'custom_endpoint' && (
                        <div>
                          <label className="text-xs font-semibold text-white block mb-1">Custom Endpoint URL</label>
                          <input
                            type="text"
                            value={llmConfig.customEndpointUrl || ''}
                            onChange={e => onUpdateLlmConfig({ ...llmConfig, customEndpointUrl: e.target.value })}
                            placeholder="https://api.openai.com/v1/chat/completions"
                            className="w-full bg-[#121418] border border-[#343b49] rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-[#4f8ff7]"
                          />
                        </div>
                      )}

                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <label className="text-xs font-semibold text-white">API Key (BYOK - Stored in browser)</label>
                          <button
                            onClick={() => setShowApiKey(!showApiKey)}
                            className="text-[11px] text-[#7d8590] hover:text-white"
                          >
                            {showApiKey ? 'Hide' : 'Show'}
                          </button>
                        </div>
                        <input
                          type={showApiKey ? 'text' : 'password'}
                          value={llmConfig.apiKey}
                          onChange={e => onUpdateLlmConfig({ ...llmConfig, apiKey: e.target.value })}
                          placeholder="sk-..."
                          className="w-full bg-[#121418] border border-[#343b49] rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-[#4f8ff7]"
                        />
                      </div>
                    </div>
                  )}

                  {/* Output Improvement Engine Note */}
                  <div className="bg-[#121418] p-3 rounded-lg border border-[#2b3342] flex items-start gap-3">
                    <Sparkles className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <div className="text-xs">
                      <div className="font-semibold text-white">Complementary Output Enhancement Engine</div>
                      <div className="text-[#8b949e] text-[11px] mt-0.5 leading-relaxed">
                        Instead of replacing your existing IDE, this engine pre-processes code using AST script extents and token filtering before sending to your local Ollama or IDE, boosting code accuracy by ~4.2× with minimal context bloat.
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB: Visual Studio 2026 & PowerShell Integration */}
            {activeMenu === 'visual_studio' && subView === 'none' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-white">Visual Studio 2026 & Editor Services</h3>
                  <p className="text-xs text-[#8b949e] mt-0.5">
                    100% interoperability with Visual Studio, VS Code, and PowerShell Editor Services v2025.4.0.
                  </p>
                </div>

                <div className="bg-[#1b1f26] border border-[#292f3b] rounded-xl p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-xs font-semibold text-white">PowerShell Editor Services (PSES) Protocol</div>
                      <div className="text-[11px] text-[#8b949e]">Supports Find-Ast, Get-Token, and Set-ScriptExtent commands.</div>
                    </div>
                    <span className="px-2 py-0.5 bg-[#12281a] border border-emerald-500/40 text-emerald-400 text-[10px] font-mono rounded">
                      v2025.4.0 Compatible
                    </span>
                  </div>

                  <div className="pt-3 border-t border-[#292f3b]">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-white">Visual Studio 2026 launch.json snippet</span>
                      <button
                        onClick={handleCopyVsCodeConfig}
                        className="px-2.5 py-1 bg-[#262c36] hover:bg-[#323946] text-white text-xs font-medium rounded-md border border-[#363f4f] transition-colors flex items-center gap-1.5"
                      >
                        {copiedVsCode ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        <span>{copiedVsCode ? 'Copied!' : 'Copy launch.json'}</span>
                      </button>
                    </div>

                    <pre className="bg-[#121418] p-3 rounded-lg border border-[#2d3545] text-[11px] font-mono text-[#a5d6ff] overflow-x-auto">
{`{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "PowerShell: Launch Current File",
      "type": "PowerShell",
      "request": "launch",
      "script": "\${file}",
      "cwd": "\${workspaceFolder}"
    },
    {
      "name": "Local Ollama: Enhanced AST Execution",
      "type": "node",
      "request": "launch",
      "program": "\${workspaceFolder}/scripts/demo.ts"
    }
  ]
}`}
                    </pre>
                  </div>
                </div>
              </div>
            )}

            {/* TAB: FAF-MCP & Always-33 AI-Readiness */}
            {activeMenu === 'faf_mcp' && subView === 'none' && (
              <div className="space-y-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                      <span>FAF-MCP & Context Kernel</span>
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-mono">
                        96% A+ (31/33 Slots)
                      </span>
                    </h3>
                    <p className="text-xs text-[#8b949e] mt-0.5">
                      IANA registered standard <code className="text-[#a5d6ff]">application/vnd.faf+yaml</code> & Wolfe-Jam/faf-mcp Model Context Protocol server.
                    </p>
                  </div>
                  {onOpenFafModal && (
                    <button
                      onClick={onOpenFafModal}
                      className="px-3 py-1.5 bg-[#4f8ff7] hover:bg-[#3b82f6] text-white text-xs font-medium rounded-lg shadow-sm transition-colors flex items-center gap-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Launch Inspector</span>
                    </button>
                  )}
                </div>

                <div className="bg-[#1b1f26] border border-[#292f3b] rounded-xl p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-xs font-semibold text-white">Active Context Manifest</div>
                      <div className="text-[11px] text-[#8b949e] font-mono mt-0.5">./project.faf (Always-33 Standard)</div>
                    </div>
                    <span className="px-2 py-0.5 bg-[#12281a] border border-emerald-500/40 text-emerald-400 text-[10px] font-mono rounded">
                      Audited & Active
                    </span>
                  </div>

                  <div className="pt-3 border-t border-[#292f3b] grid grid-cols-2 gap-3 text-xs">
                    <div className="bg-[#121418] p-3 rounded-lg border border-[#262c36]">
                      <div className="text-[10px] font-semibold text-[#8b949e] uppercase tracking-wider mb-1">MCP Stdio Server</div>
                      <div className="font-mono text-[11px] text-[#a5d6ff]">npx @faf-mcp/server</div>
                      <div className="text-[10px] text-emerald-400 mt-1 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        <span>Ready • 6 Core Tools Registered</span>
                      </div>
                    </div>

                    <div className="bg-[#121418] p-3 rounded-lg border border-[#262c36]">
                      <div className="text-[10px] font-semibold text-[#8b949e] uppercase tracking-wider mb-1">Downstream Sync</div>
                      <div className="font-mono text-[11px] text-[#e6edf3]">Cursor, Windsurf, Claude, VS 2026</div>
                      <div className="text-[10px] text-[#8b949e] mt-1">Single-source-of-truth export</div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-[#292f3b]">
                    <div className="text-xs font-semibold text-white mb-2">FAF Context Capabilities</div>
                    <div className="grid grid-cols-3 gap-2 text-[11px]">
                      <div className="p-2.5 rounded-lg bg-[#14171d] border border-[#262c36]">
                        <div className="text-white font-medium">faf_eval</div>
                        <div className="text-[#8b949e] text-[10px] mt-0.5">Audits project against 33 essential slots</div>
                      </div>
                      <div className="p-2.5 rounded-lg bg-[#14171d] border border-[#262c36]">
                        <div className="text-white font-medium">faf_diff</div>
                        <div className="text-[#8b949e] text-[10px] mt-0.5">Detects AST context drift & pruning delta</div>
                      </div>
                      <div className="p-2.5 rounded-lg bg-[#14171d] border border-[#262c36]">
                        <div className="text-white font-medium">faf_sync</div>
                        <div className="text-[#8b949e] text-[10px] mt-0.5">Compiles .cursorrules & launch.json</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* SUB-VIEW: Network Permissions */}
            {subView === 'network_permissions' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">Network Permissions</h3>
                  <p className="text-xs text-[#8b949e] mt-1">Configure allowed and denied URLs or domains for agent web access.</p>
                </div>

                <div className="bg-[#1b1f26] border border-[#292f3b] rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-xs font-semibold text-white">Read URLs</div>
                      <div className="text-[11px] text-[#8b949e]">Allow/deny agent read access to specific URLs or domains.</div>
                    </div>
                    <button
                      onClick={() => setShowAddUrl(!showAddUrl)}
                      className="px-3 py-1 bg-[#262c36] hover:bg-[#323946] text-white text-xs font-medium rounded-lg border border-[#363f4f] transition-colors"
                    >
                      Add
                    </button>
                  </div>

                  {showAddUrl && (
                    <div className="flex items-center gap-2 pt-2 border-t border-[#292f3b]">
                      <input
                        type="text"
                        placeholder="e.g. 127.0.0.1:11434"
                        value={newUrlInput}
                        onChange={e => setNewUrlInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleAddUrl()}
                        className="flex-1 bg-[#121418] border border-[#343b49] rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[#4f8ff7]"
                        autoFocus
                      />
                      <button
                        onClick={handleAddUrl}
                        className="px-3 py-1.5 bg-[#2563eb] text-white text-xs font-medium rounded-lg hover:bg-[#1d4ed8]"
                      >
                        Save
                      </button>
                    </div>
                  )}

                  <div className="space-y-2 pt-2">
                    {networkUrls.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between bg-[#13161c] border border-[#272d38] px-3 py-2 rounded-lg text-xs">
                        <div className="flex items-center gap-3">
                          <span className="px-2 py-0.5 bg-[#1e2430] border border-[#343c4d] text-emerald-400 font-mono text-[11px] rounded">
                            {item.permission}
                          </span>
                          <span className="font-mono text-[#e6edf3]">{item.url}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleRemoveUrl(idx)}
                            className="text-[#7d8590] hover:text-red-400 p-1"
                            title="Remove permission"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* SUB-VIEW: Tool Permissions */}
            {subView === 'tool_permissions' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">Tool Permissions</h3>
                  <p className="text-xs text-[#8b949e] mt-1">Modify permissions for file, terminal, and MCP tools.</p>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between bg-[#1b1f26] border border-[#292f3b] rounded-xl p-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-white">File Access Rules</span>
                        <span className="px-1.5 py-0.2 bg-[#2d3340] text-[#a5d6ff] text-[10px] rounded font-mono">233</span>
                      </div>
                      <div className="text-[11px] text-[#8b949e] mt-0.5">Configure allowed and denied paths for file reads and writes.</div>
                    </div>
                    <button className="px-3 py-1.5 bg-[#262c36] hover:bg-[#323946] text-white text-xs font-medium rounded-lg border border-[#363f4f]">
                      Open
                    </button>
                  </div>

                  <div className="flex items-center justify-between bg-[#1b1f26] border border-[#292f3b] rounded-xl p-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-white">Terminal Commands</span>
                        <span className="px-1.5 py-0.2 bg-[#2d3340] text-[#a5d6ff] text-[10px] rounded font-mono">155</span>
                      </div>
                      <div className="text-[11px] text-[#8b949e] mt-0.5">Configure allowed terminal commands.</div>
                    </div>
                    <button className="px-3 py-1.5 bg-[#262c36] hover:bg-[#323946] text-white text-xs font-medium rounded-lg border border-[#363f4f]">
                      Open
                    </button>
                  </div>

                  <div className="flex items-center justify-between bg-[#1b1f26] border border-[#292f3b] rounded-xl p-4">
                    <div>
                      <div className="text-xs font-semibold text-white">MCP Tools</div>
                      <div className="text-[11px] text-[#8b949e] mt-0.5">Configure external tools via Model Context Protocol.</div>
                    </div>
                    <button className="px-3 py-1.5 bg-[#262c36] hover:bg-[#323946] text-white text-xs font-medium rounded-lg border border-[#363f4f]">
                      Open
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* TAB: General */}
            {activeMenu === 'general' && subView === 'none' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-white">General</h3>
                  <p className="text-xs text-[#8b949e] mt-0.5">Configure agent execution, queued message delivery, and permissions.</p>
                </div>

                {/* Execution Section */}
                <div className="space-y-3">
                  <div className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider">Execution</div>
                  <div className="bg-[#1b1f26] border border-[#292f3b] rounded-xl p-4 flex items-center justify-between">
                    <div>
                      <div className="text-xs font-semibold text-white">Queued Messages</div>
                      <div className="text-[11px] text-[#8b949e] mt-0.5">Configure when follow-up messages are sent. Keyboard shortcuts ⓘ</div>
                    </div>
                    <div className="flex bg-[#121418] p-1 rounded-lg border border-[#292f3b]">
                      <button
                        onClick={() => setQueuedMessages('queue')}
                        className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                          queuedMessages === 'queue' ? 'bg-[#2b313d] text-white shadow-sm' : 'text-[#8b949e] hover:text-white'
                        }`}
                      >
                        Queue
                      </button>
                      <button
                        onClick={() => setQueuedMessages('send_immediately')}
                        className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                          queuedMessages === 'send_immediately' ? 'bg-[#2b313d] text-white shadow-sm' : 'text-[#8b949e] hover:text-white'
                        }`}
                      >
                        Send Immediately
                      </button>
                    </div>
                  </div>
                </div>

                {/* Global Permissions */}
                <div className="space-y-3">
                  <div className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider">Global Permissions</div>
                  <div className="bg-[#1b1f26] border border-[#292f3b] rounded-xl p-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-xs font-semibold text-white">Security Preset</div>
                        <div className="text-[11px] text-[#8b949e] mt-0.5">Controls the actions the agent can take. Learn more about Turbo mode ⓘ</div>
                      </div>
                      <div className="relative">
                        <select
                          value={securityPreset}
                          onChange={e => setSecurityPreset(e.target.value as any)}
                          className="bg-[#121418] border border-[#292f3b] text-white text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-[#4f8ff7] appearance-none pr-8 cursor-pointer"
                        >
                          <option value="turbo">Turbo Mode</option>
                          <option value="strict">Strict Audit</option>
                          <option value="relaxed">Relaxed</option>
                        </select>
                        <ChevronDown className="w-3.5 h-3.5 text-[#8b949e] absolute right-2.5 top-2.5 pointer-events-none" />
                      </div>
                    </div>

                    <div className="pt-3 border-t border-[#292f3b] flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-white">Tool Permissions</span>
                          <span className="px-1.5 py-0.2 bg-[#2d3340] text-[#a5d6ff] text-[10px] rounded font-mono">388</span>
                        </div>
                        <div className="text-[11px] text-[#8b949e] mt-0.5">Modify permissions for file, terminal, and MCP tools.</div>
                      </div>
                      <button
                        onClick={() => setSubView('tool_permissions')}
                        className="px-3 py-1.5 bg-[#262c36] hover:bg-[#323946] text-white text-xs font-medium rounded-lg border border-[#363f4f]"
                      >
                        Open
                      </button>
                    </div>
                  </div>
                </div>

                {/* Agent Behavior */}
                <div className="space-y-3">
                  <div className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider">Agent Behavior</div>
                  <div className="bg-[#1b1f26] border border-[#292f3b] rounded-xl p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-xs font-semibold text-white">Plan Review Policy</div>
                        <div className="text-[11px] text-[#8b949e] mt-0.5">Whether the agent asks you to review its documents.</div>
                      </div>
                      <div className="relative">
                        <select
                          value={planReviewPolicy}
                          onChange={e => setPlanReviewPolicy(e.target.value as any)}
                          className="bg-[#121418] border border-[#292f3b] text-white text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-[#4f8ff7] appearance-none pr-8 cursor-pointer"
                        >
                          <option value="always_proceed">Always Proceed</option>
                          <option value="ask_first">Ask First</option>
                        </select>
                        <ChevronDown className="w-3.5 h-3.5 text-[#8b949e] absolute right-2.5 top-2.5 pointer-events-none" />
                      </div>
                    </div>
                    <div className="text-[11px] text-[#7d8590] pt-1">
                      Type <code className="px-1.5 py-0.5 bg-[#121418] text-[#a5d6ff] rounded font-mono">/</code> and select <code className="px-1.5 py-0.5 bg-[#121418] text-[#a5d6ff] rounded font-mono">plan</code> to have the agent generate a plan.
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB: CLI Project */}
            {activeMenu === 'cli_project' && subView === 'none' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-white">CLI Project</h3>
                  <p className="text-xs text-[#8b949e] mt-0.5">Project-specific configuration, sandboxing rules, and local overrides.</p>
                </div>

                <div className="space-y-3">
                  <div className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider">
                    Local Permissions <span className="text-[11px] lowercase text-[#7d8590] font-normal">• Also includes Global Permissions</span>
                  </div>
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between bg-[#1b1f26] border border-[#292f3b] rounded-xl p-3.5">
                      <div>
                        <div className="text-xs font-semibold text-white">File Access Rules</div>
                        <div className="text-[11px] text-[#8b949e]">Configure allowed and denied paths for file reads and writes.</div>
                      </div>
                      <button 
                        onClick={() => setSubView('tool_permissions')}
                        className="px-3 py-1 bg-[#262c36] hover:bg-[#323946] text-white text-xs font-medium rounded-lg border border-[#363f4f]"
                      >
                        Open
                      </button>
                    </div>

                    <div className="flex items-center justify-between bg-[#1b1f26] border border-[#292f3b] rounded-xl p-3.5">
                      <div>
                        <div className="text-xs font-semibold text-white">Network Access Rules</div>
                        <div className="text-[11px] text-[#8b949e]">Configure allowed and denied URLs for reading.</div>
                      </div>
                      <button
                        onClick={() => setSubView('network_permissions')}
                        className="px-3 py-1 bg-[#262c36] hover:bg-[#323946] text-white text-xs font-medium rounded-lg border border-[#363f4f]"
                      >
                        Open
                      </button>
                    </div>

                    <div className="flex items-center justify-between bg-[#1b1f26] border border-[#292f3b] rounded-xl p-3.5">
                      <div>
                        <div className="text-xs font-semibold text-white">Terminal Commands</div>
                        <div className="text-[11px] text-[#8b949e]">Configure allowed terminal commands.</div>
                      </div>
                      <button 
                        onClick={() => setSubView('tool_permissions')}
                        className="px-3 py-1 bg-[#262c36] hover:bg-[#323946] text-white text-xs font-medium rounded-lg border border-[#363f4f]"
                      >
                        Open
                      </button>
                    </div>

                    <div className="flex items-center justify-between bg-[#1b1f26] border border-[#292f3b] rounded-xl p-3.5">
                      <div>
                        <div className="text-xs font-semibold text-white">MCP Tools</div>
                        <div className="text-[11px] text-[#8b949e]">Configure external tools via Model Context Protocol.</div>
                      </div>
                      <button 
                        onClick={() => setSubView('tool_permissions')}
                        className="px-3 py-1 bg-[#262c36] hover:bg-[#323946] text-white text-xs font-medium rounded-lg border border-[#363f4f]"
                      >
                        Open
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
