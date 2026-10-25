import { Shield, Cpu, Activity, FileText, KeyRound, Layers, AlertTriangle, Radio } from 'lucide-react';

export type NavTab =
  | 'cockpit'
  | 'compilers'
  | 'governance'
  | 'hardware_ledger'
  | 'toolbox'
  | 'departments'
  | 'gate'
  | 'continuum';

interface HeaderProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  version: string;
  branch: string;
  commit: string;
  isDirty: boolean;
  queuedCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  version,
  branch,
  commit,
  isDirty,
  queuedCount,
}) => {
  return (
    <header className="border-b border-[#26303d] bg-[#0b0e13]/90 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-[1450px] mx-auto px-4 sm:px-7 py-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#11151d] border border-[#26303d] flex items-center justify-center p-1.5 shadow-sm">
              <svg viewBox="0 0 32 32" className="w-full h-full" fill="none">
                <rect width="32" height="32" rx="8" fill="#11151d" />
                <path d="M9 9h4v14H9zM19 9h4v14h-4z" fill="#66e3c4" />
                <path d="M13 15h6v2h-6z" fill="#66e3c4" opacity="0.6" />
              </svg>
            </div>
            <div>
              <div className="text-[10px] font-bold tracking-[0.18em] uppercase text-[#66e3c4]">
                Private founder control desk · governed cockpit
              </div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#eef3f8] flex items-center gap-2">
                Veklom Ops Command
                <span className="text-xs font-mono font-normal text-[#8d9aaa] bg-[#121720] px-2 py-0.5 rounded border border-[#26303d]">
                  v{version}
                </span>
                <span className="text-[10px] font-mono font-bold text-[#66e3c4] bg-[#10241b] px-2 py-0.5 rounded border border-[#66e3c4]/30">
                  mini : sovereign
                </span>
              </h1>
            </div>
          </div>

          {/* Repo Truth Metadata Pills */}
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
            <span className="px-2.5 py-1 rounded-full bg-[#10151d] border border-[#26303d] text-[#8d9aaa] flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#66e3c4]"></span>
              {branch} @ <span className="text-[#eef3f8]">{commit}</span>
            </span>
            <span
              className={`px-2.5 py-1 rounded-full border ${
                isDirty
                  ? 'bg-[#2e2410] border-[#ffca6b]/40 text-[#ffca6b]'
                  : 'bg-[#10151d] border-[#26303d] text-[#66e3c4]'
              } flex items-center gap-1.5`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isDirty ? 'bg-[#ffca6b]' : 'bg-[#66e3c4]'
                }`}
              ></span>
              {isDirty ? 'uncommitted changes' : 'source clean'}
            </span>
            <span className="px-2.5 py-1 rounded-full bg-[#10151d] border border-[#26303d] text-[#8d9aaa]">
              Hardware: <strong className="text-[#eef3f8]">owned-docker</strong>
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 sm:gap-2 mt-4 -mb-3 overflow-x-auto pb-2 scrollbar-none border-t border-[#26303d]/40 pt-2 text-xs sm:text-sm font-medium">
          <button
            onClick={() => setActiveTab('cockpit')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-2 transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'cockpit'
                ? 'bg-[#121720] text-[#66e3c4] border border-[#26303d] shadow-sm'
                : 'text-[#8d9aaa] hover:text-[#eef3f8] hover:bg-[#121720]/50'
            }`}
          >
            <Cpu className="w-4 h-4" />
            <span>Ops Cockpit</span>
            {queuedCount > 0 && (
              <span className="bg-[#ffca6b]/20 text-[#ffca6b] text-[10px] px-1.5 py-0.2 rounded-full border border-[#ffca6b]/30">
                {queuedCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('compilers')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-2 transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'compilers'
                ? 'bg-[#121720] text-[#66e3c4] border border-[#26303d] shadow-sm'
                : 'text-[#8d9aaa] hover:text-[#eef3f8] hover:bg-[#121720]/50'
            }`}
          >
            <FileText className="w-4 h-4 text-[#66e3c4]" />
            <span>Compilers (Mini & HRM)</span>
          </button>

          <button
            onClick={() => setActiveTab('governance')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-2 transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'governance'
                ? 'bg-[#121720] text-[#66e3c4] border border-[#26303d] shadow-sm'
                : 'text-[#8d9aaa] hover:text-[#eef3f8] hover:bg-[#121720]/50'
            }`}
          >
            <Shield className="w-4 h-4 text-[#ffca6b]" />
            <span>MCP Governance & Tiers</span>
          </button>

          <button
            onClick={() => setActiveTab('hardware_ledger')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-2 transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'hardware_ledger'
                ? 'bg-[#121720] text-[#66e3c4] border border-[#26303d] shadow-sm'
                : 'text-[#8d9aaa] hover:text-[#eef3f8] hover:bg-[#121720]/50'
            }`}
          >
            <Radio className="w-4 h-4 text-[#66e3c4]" />
            <span>BLADE-HSM & vChip</span>
          </button>

          <button
            onClick={() => setActiveTab('toolbox')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-2 transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'toolbox'
                ? 'bg-[#121720] text-[#66e3c4] border border-[#26303d] shadow-sm'
                : 'text-[#8d9aaa] hover:text-[#eef3f8] hover:bg-[#121720]/50'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Toolbox Meetings</span>
          </button>

          <button
            onClick={() => setActiveTab('departments')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-2 transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'departments'
                ? 'bg-[#121720] text-[#66e3c4] border border-[#26303d] shadow-sm'
                : 'text-[#8d9aaa] hover:text-[#eef3f8] hover:bg-[#121720]/50'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>9 Departments</span>
          </button>

          <button
            onClick={() => setActiveTab('gate')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-2 transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'gate'
                ? 'bg-[#121720] text-[#66e3c4] border border-[#26303d] shadow-sm'
                : 'text-[#8d9aaa] hover:text-[#eef3f8] hover:bg-[#121720]/50'
            }`}
          >
            <KeyRound className="w-4 h-4" />
            <span>Veklom Gate Approver</span>
          </button>

          <button
            onClick={() => setActiveTab('continuum')}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-2 transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'continuum'
                ? 'bg-[#121720] text-[#66e3c4] border border-[#26303d] shadow-sm'
                : 'text-[#8d9aaa] hover:text-[#eef3f8] hover:bg-[#121720]/50'
            }`}
          >
            <Shield className="w-4 h-4" />
            <span>Continuum & Lock</span>
          </button>
        </nav>
      </div>
    </header>
  );
};

