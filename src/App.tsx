import React, { useState, useEffect } from 'react';
import { Header, NavTab } from './components/Header';
import { CockpitView } from './components/CockpitView';
import { CompilersView } from './components/CompilersView';
import { GovernanceView } from './components/GovernanceView';
import { HardwareLedgerView } from './components/HardwareLedgerView';
import { ToolboxView } from './components/ToolboxView';
import { DepartmentsView } from './components/DepartmentsView';
import { GateApproverView } from './components/GateApproverView';
import { ContinuumView } from './components/ContinuumView';
import { ReportModal } from './components/ReportModal';
import {
  initialCoreBackend4,
  initialCapabilities,
  initialSecurityPosture,
  initialDepartments,
  initialToolboxMeetings,
  initialContinuumManifest,
  sampleInboxMessages,
} from './data/initialData';
import { CommandMessage, GateApprovalRequest, ToolboxMeeting } from './types';

export function App() {
  const [activeTab, setActiveTab] = useState<NavTab>('cockpit');
  const [activeMission, setActiveMission] = useState<ToolboxMeeting>(initialToolboxMeetings[0]);

  // Messages with local storage persistence
  const [messages, setMessages] = useState<CommandMessage[]>(() => {
    try {
      const stored = localStorage.getItem('veklom_inbox_messages');
      return stored ? JSON.parse(stored) : sampleInboxMessages;
    } catch {
      return sampleInboxMessages;
    }
  });

  // Pending gate approval request
  const [pendingGateRequest, setPendingGateRequest] = useState<GateApprovalRequest | null>(null);

  // Report Modal state
  const [modalTitle, setModalTitle] = useState<string>('');
  const [modalData, setModalData] = useState<unknown>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  // Listen to hash changes if someone navigates with `#gate`, `#compilers`, etc.
  useEffect(() => {
    const handleHash = () => {
      const hash = window.location.hash;
      if (hash.startsWith('#r=')) {
        setActiveTab('gate');
      } else if (hash === '#gate') {
        setActiveTab('gate');
      } else if (hash === '#compilers') {
        setActiveTab('compilers');
      } else if (hash === '#governance') {
        setActiveTab('governance');
      } else if (hash === '#hardware_ledger') {
        setActiveTab('hardware_ledger');
      } else if (hash === '#toolbox') {
        setActiveTab('toolbox');
      } else if (hash === '#departments') {
        setActiveTab('departments');
      } else if (hash === '#continuum') {
        setActiveTab('continuum');
      }
    };
    handleHash();
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);

  const handleSendMessage = (text: string, risk: 'low' | 'medium' | 'high' | 'critical', requiresApproval: boolean) => {
    const newMsg: CommandMessage = {
      id: 'cmd-' + Math.random().toString(36).substring(2, 8),
      createdAt: new Date().toISOString(),
      from: 'founder-operator',
      to: 'command-desk',
      text,
      risk,
      requiresApproval,
      status: 'queued',
    };

    const updated = [newMsg, ...messages];
    setMessages(updated);
    try {
      localStorage.setItem('veklom_inbox_messages', JSON.stringify(updated));
    } catch {
      // storage unavailable
    }
  };

  const handleInitiateGateApproval = (req: GateApprovalRequest) => {
    setPendingGateRequest(req);
    setActiveTab('gate');
  };

  const handleApprovalSuccess = (requestId: string, token: string) => {
    setMessages((prev) => {
      const updated = prev.map((msg) =>
        msg.id === requestId
          ? { ...msg, status: 'approved' as const, token }
          : msg
      );
      try {
        localStorage.setItem('veklom_inbox_messages', JSON.stringify(updated));
      } catch {
        // ignore
      }
      return updated;
    });
  };

  const handleOpenReport = (title: string, data: unknown) => {
    setModalTitle(title);
    setModalData(data);
    setIsModalOpen(true);
  };

  const queuedCount = messages.filter((m) => m.status === 'queued').length;

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0e13]">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        version="0.2.0"
        branch="main"
        commit="a8f3b92"
        isDirty={false}
        queuedCount={queuedCount}
      />

      <main id="main" className="flex-1 max-w-[1450px] w-full mx-auto px-4 sm:px-7 pt-6">
        {activeTab === 'cockpit' && (
          <CockpitView
            branch="main"
            commit="a8f3b92"
            isDirty={false}
            activeMission={activeMission}
            allMissions={initialToolboxMeetings}
            onSelectMission={setActiveMission}
            coreBackend4={initialCoreBackend4}
            capabilities={initialCapabilities}
            security={initialSecurityPosture}
            departments={initialDepartments}
            messages={messages}
            onSendMessage={handleSendMessage}
            onOpenReport={handleOpenReport}
            onInitiateGateApproval={handleInitiateGateApproval}
          />
        )}

        {activeTab === 'compilers' && (
          <CompilersView />
        )}

        {activeTab === 'governance' && (
          <GovernanceView />
        )}

        {activeTab === 'hardware_ledger' && (
          <HardwareLedgerView />
        )}

        {activeTab === 'toolbox' && (
          <ToolboxView
            missions={initialToolboxMeetings}
            onOpenReport={handleOpenReport}
          />
        )}

        {activeTab === 'departments' && (
          <DepartmentsView
            departments={initialDepartments}
            onOpenReport={handleOpenReport}
          />
        )}

        {activeTab === 'gate' && (
          <GateApproverView
            pendingRequest={pendingGateRequest}
            onClearPendingRequest={() => setPendingGateRequest(null)}
            onApprovalSuccess={handleApprovalSuccess}
          />
        )}

        {activeTab === 'continuum' && (
          <ContinuumView
            manifest={initialContinuumManifest}
            onOpenReport={handleOpenReport}
          />
        )}
      </main>

      <footer className="border-t border-[#26303d] py-4 px-7 bg-[#0b0e13] text-xs font-mono text-[#8d9aaa] flex flex-col sm:flex-row items-center justify-between gap-2 mt-auto">
        <div>
          Veklom Ops Command · Poltergeist DevOps & Capability OS Control Plane
        </div>
        <div className="flex items-center gap-4">
          <span className="text-[#66e3c4]">Sole Consequence Authority: CAPPO</span>
          <span>·</span>
          <span>Evidence: GnomLedger / PGL</span>
        </div>
      </footer>

      <ReportModal
        title={modalTitle}
        data={modalData}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
}

export default App;
