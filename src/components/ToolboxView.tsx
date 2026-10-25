import React, { useState } from 'react';
import { Activity, ShieldAlert, CheckCircle, Clock, FileText, ChevronRight, AlertOctagon } from 'lucide-react';
import { ToolboxMeeting } from '../types';

interface ToolboxViewProps {
  missions: ToolboxMeeting[];
  onOpenReport: (title: string, data: unknown) => void;
}

export const ToolboxView: React.FC<ToolboxViewProps> = ({ missions, onOpenReport }) => {
  const [selectedMission, setSelectedMission] = useState<ToolboxMeeting>(missions[0]);

  return (
    <div className="space-y-6 pb-16">
      <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-2">
          <Activity className="w-5 h-5 text-[#66e3c4]" />
          <h2 className="text-lg font-bold text-[#eef3f8]">Toolbox Meetings & Missions Registry</h2>
        </div>
        <p className="text-xs text-[#8d9aaa] leading-relaxed max-w-3xl">
          Toolbox meetings establish interdepartmental scope, risk classifications, forbidden boundaries, and definitions of done before any operational drill or hardening procedure is executed.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Meeting List */}
        <div className="space-y-3">
          <h3 className="text-xs font-mono font-semibold uppercase text-[#8d9aaa] px-1">
            Registered Missions ({missions.length})
          </h3>
          <div className="space-y-2">
            {missions.map((m) => {
              const isSelected = selectedMission.mission_id === m.mission_id;
              return (
                <button
                  key={m.mission_id}
                  onClick={() => setSelectedMission(m)}
                  className={`w-full text-left p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-[#151c27] border-[#66e3c4] shadow-md'
                      : 'bg-[#121720]/80 border-[#26303d] hover:border-[#26303d]/80 hover:bg-[#17202c]/50'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="font-mono text-xs font-bold text-[#66e3c4]">{m.mission_id}</span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                        m.status === 'completed' || m.status === 'department_reports_received'
                          ? 'bg-[#10241b] text-[#66e3c4] border-[#66e3c4]/30'
                          : 'bg-[#2e2410] text-[#ffca6b] border-[#ffca6b]/30'
                      }`}
                    >
                      {m.status}
                    </span>
                  </div>
                  <h4 className="text-sm font-semibold text-[#eef3f8] line-clamp-1">{m.title}</h4>
                  <div className="flex items-center gap-2 text-[11px] font-mono text-[#8d9aaa] mt-2">
                    <span>Priority: {m.priority || m.risk_level || 'standard'}</span>
                    <span>·</span>
                    <span>Lead: {m.primary_department || 'command-desk'}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Mission Detail */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-sm space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#26303d]">
              <div>
                <span className="text-xs font-mono text-[#66e3c4] font-semibold">{selectedMission.mission_id}</span>
                <h3 className="text-xl font-bold text-[#eef3f8] mt-0.5">{selectedMission.title}</h3>
                {selectedMission.processed_at && (
                  <p className="text-[11px] font-mono text-[#8d9aaa] mt-1">
                    Processed at: {selectedMission.processed_at} by {selectedMission.processed_by || 'command-desk'}
                  </p>
                )}
              </div>
              <button
                onClick={() => onOpenReport(`${selectedMission.mission_id} JSON Spec`, selectedMission)}
                className="self-start sm:self-center px-3 py-1.5 rounded-lg bg-[#10151d] border border-[#26303d] hover:border-[#66e3c4] text-[#66e3c4] text-xs font-mono flex items-center gap-1.5 cursor-pointer transition-colors"
              >
                <FileText className="w-4 h-4" />
                Raw Spec →
              </button>
            </div>

            {/* Objective & Instructions */}
            <div>
              <h4 className="text-xs font-mono uppercase tracking-wider text-[#8d9aaa] mb-1.5">
                Primary Objective & Instructions
              </h4>
              <div className="p-3.5 rounded-lg bg-[#0e131b] border border-[#26303d] text-xs font-mono text-[#c8f6e9] leading-relaxed">
                {selectedMission.primary_objective ||
                  selectedMission.instructions ||
                  selectedMission.intent ||
                  'No specific objective description.'}
              </div>
            </div>

            {/* Scope & Impact Matrix */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 rounded-lg bg-[#0e131b] border border-[#26303d]">
                <span className="text-[10px] font-mono text-[#8d9aaa] block uppercase">Risk Tier</span>
                <strong className="text-xs font-mono text-[#ffca6b] uppercase">
                  {selectedMission.risk_level || selectedMission.priority || 'standard'}
                </strong>
              </div>
              <div className="p-3 rounded-lg bg-[#0e131b] border border-[#26303d]">
                <span className="text-[10px] font-mono text-[#8d9aaa] block uppercase">Prod Impact</span>
                <strong className={`text-xs font-mono ${selectedMission.production_impact ? 'text-[#ff8e8e]' : 'text-[#66e3c4]'}`}>
                  {selectedMission.production_impact ? 'YES (High Risk)' : 'NO (Governed)'}
                </strong>
              </div>
              <div className="p-3 rounded-lg bg-[#0e131b] border border-[#26303d]">
                <span className="text-[10px] font-mono text-[#8d9aaa] block uppercase">Approval Gate</span>
                <strong className="text-xs font-mono text-[#eef3f8]">
                  {selectedMission.approval_required ? 'Required (Veklom Gate)' : 'Standard'}
                </strong>
              </div>
              <div className="p-3 rounded-lg bg-[#0e131b] border border-[#26303d]">
                <span className="text-[10px] font-mono text-[#8d9aaa] block uppercase">Lead Dept</span>
                <strong className="text-xs font-mono text-[#66e3c4] truncate block">
                  {selectedMission.primary_department || 'command-desk'}
                </strong>
              </div>
            </div>

            {/* Forbidden Actions */}
            {selectedMission.forbidden_actions && selectedMission.forbidden_actions.length > 0 && (
              <div>
                <h4 className="text-xs font-mono uppercase tracking-wider text-[#ff8e8e] mb-2 flex items-center gap-1.5">
                  <AlertOctagon className="w-3.5 h-3.5" />
                  Strictly Forbidden Actions
                </h4>
                <div className="flex flex-wrap gap-2">
                  {selectedMission.forbidden_actions.map((act, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded bg-[#321816] border border-[#ff8e8e]/40 text-[#ff8e8e] font-mono text-xs"
                    >
                      ✕ {act}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Definition of Done */}
            {selectedMission.definition_of_done && (
              <div>
                <h4 className="text-xs font-mono uppercase tracking-wider text-[#66e3c4] mb-2 flex items-center gap-1.5">
                  <CheckCircle className="w-3.5 h-3.5" />
                  Definition of Done
                </h4>
                <ul className="space-y-1.5 bg-[#0e131b] p-3 rounded-lg border border-[#26303d] text-xs font-mono text-[#8d9aaa]">
                  {selectedMission.definition_of_done.map((item, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-[#66e3c4] font-bold">✓</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Objectives List if present */}
            {selectedMission.objectives && (
              <div>
                <h4 className="text-xs font-mono uppercase tracking-wider text-[#ffca6b] mb-2">
                  Specific Objectives
                </h4>
                <div className="space-y-2">
                  {selectedMission.objectives.map((obj) => (
                    <div
                      key={obj.id}
                      className="p-3 bg-[#0e131b] rounded-lg border border-[#26303d] text-xs font-mono flex items-start justify-between gap-3"
                    >
                      <div>
                        <span className="text-[#66e3c4] font-bold block mb-0.5">{obj.id}</span>
                        <p className="text-[#eef3f8]">{obj.description}</p>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-[#151c27] text-[#ffca6b] text-[11px] shrink-0 border border-[#26303d]">
                        @{obj.assignee}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Response Summary */}
            {selectedMission.response_summary && (
              <div className="p-3 bg-[#151c27] rounded-lg border border-[#66e3c4]/30 text-xs text-[#c8f6e9] font-mono">
                <strong className="text-[#66e3c4] block mb-1">Response Summary:</strong>
                {selectedMission.response_summary}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
