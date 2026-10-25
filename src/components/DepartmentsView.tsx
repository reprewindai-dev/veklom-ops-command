import React, { useState } from 'react';
import { Layers, Shield, FileText, CheckCircle2, AlertTriangle, ArrowRight, Target, Users } from 'lucide-react';
import { Department } from '../types';

interface DepartmentsViewProps {
  departments: Department[];
  onOpenReport: (title: string, data: unknown) => void;
}

export const DepartmentsView: React.FC<DepartmentsViewProps> = ({ departments, onOpenReport }) => {
  const [activeDept, setActiveDept] = useState<Department>(departments[0]);

  return (
    <div className="space-y-6 pb-16">
      <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-2">
          <Layers className="w-5 h-5 text-[#66e3c4]" />
          <h2 className="text-lg font-bold text-[#eef3f8]">The 9 Autonomous DevOps Departments</h2>
        </div>
        <p className="text-xs text-[#8d9aaa] leading-relaxed max-w-3xl">
          Each department is an independent Poltergeist project equipped with dedicated watchers, runbooks, verification scripts, interdepartmental handoffs, and capability gates.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Navigation list */}
        <div className="space-y-2">
          {departments.map((dept) => {
            const isSelected = activeDept.team === dept.team;
            return (
              <button
                key={dept.team}
                onClick={() => setActiveDept(dept)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-[#151c27] border-[#66e3c4] shadow-md'
                    : 'bg-[#121720]/80 border-[#26303d] hover:border-[#26303d]/80 hover:bg-[#17202c]/50'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <h4 className="font-bold text-sm text-[#eef3f8]">{dept.name}</h4>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                      dept.latestReport?.status === 'aligned'
                        ? 'bg-[#10241b] text-[#66e3c4] border-[#66e3c4]/30'
                        : 'bg-[#2e2410] text-[#ffca6b] border-[#ffca6b]/30'
                    }`}
                  >
                    {dept.latestReport?.status || 'unverified'}
                  </span>
                </div>
                <div className="text-xs font-mono text-[#8d9aaa] mb-1">
                  targets: {dept.targetCount} · daemon: active
                </div>
                <p className="text-xs text-[#8d9aaa] line-clamp-1">{dept.mission}</p>
              </button>
            );
          })}
        </div>

        {/* Detailed Department View */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-[#121720]/90 border border-[#26303d] rounded-xl p-5 sm:p-6 shadow-sm space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#26303d]">
              <div>
                <span className="text-xs font-mono text-[#8d9aaa] uppercase tracking-wider block">
                  Department ID: <span className="text-[#66e3c4]">{activeDept.team}</span>
                </span>
                <h3 className="text-2xl font-bold text-[#eef3f8] mt-0.5">{activeDept.name}</h3>
                <p className="text-xs font-mono text-[#8d9aaa] mt-1 flex items-center gap-2">
                  <Users className="w-3.5 h-3.5 text-[#66e3c4]" />
                  Captain: <strong className="text-[#eef3f8]">{activeDept.captain || 'Assigned Agent'}</strong>
                </p>
              </div>

              <button
                onClick={() => onOpenReport(`${activeDept.name} Latest Report`, activeDept.latestReport || { status: 'awaiting_response' })}
                className="px-3.5 py-2 rounded-lg bg-[#10151d] border border-[#26303d] hover:border-[#66e3c4] text-[#66e3c4] text-xs font-mono flex items-center gap-2 cursor-pointer transition-colors"
              >
                <FileText className="w-4 h-4" />
                Inspect Latest JSONL →
              </button>
            </div>

            {/* Mission Statement */}
            <div>
              <h4 className="text-xs font-mono uppercase tracking-wider text-[#8d9aaa] mb-1">Mission Mandate</h4>
              <p className="p-3.5 bg-[#0e131b] rounded-lg border border-[#26303d] text-xs leading-relaxed text-[#eef3f8]">
                {activeDept.mission}
              </p>
            </div>

            {/* Poltergeist Target Watchers */}
            <div>
              <h4 className="text-xs font-mono uppercase tracking-wider text-[#66e3c4] mb-2 flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5" />
                Watched Repository Targets ({activeDept.targets?.length || activeDept.targetCount})
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {activeDept.targets?.map((target, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded bg-[#0e131b] border border-[#26303d] text-xs font-mono text-[#8d9aaa] flex items-center gap-2"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-[#66e3c4]"></span>
                    <span className="truncate">{target}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Latest Report Details */}
            {activeDept.latestReport && (
              <div className="space-y-4 pt-3 border-t border-[#26303d]/60">
                <h4 className="text-xs font-mono uppercase tracking-wider text-[#ffca6b]">
                  Current Alignment Drill ({activeDept.latestReport.mission_id})
                </h4>

                <div className="p-3.5 bg-[#0e131b] rounded-lg border border-[#26303d] text-xs font-mono text-[#c8f6e9] leading-relaxed">
                  <strong className="text-[#66e3c4] block mb-1">Mission Understanding:</strong>
                  {activeDept.latestReport.mission_understanding}
                </div>

                {/* Owned systems */}
                {activeDept.latestReport.owned_systems && (
                  <div>
                    <span className="text-[11px] font-mono text-[#8d9aaa] uppercase block mb-1">Owned Systems:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {activeDept.latestReport.owned_systems.map((s, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded bg-[#151c27] border border-[#26303d] text-xs font-mono text-[#eef3f8]"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Risks */}
                {activeDept.latestReport.risks && (
                  <div>
                    <span className="text-[11px] font-mono text-[#ffca6b] uppercase block mb-1">Identified Risks:</span>
                    <ul className="space-y-1 bg-[#0e131b] p-3 rounded-lg border border-[#26303d] text-xs font-mono text-[#8d9aaa]">
                      {activeDept.latestReport.risks.map((r, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <AlertTriangle className="w-3.5 h-3.5 text-[#ffca6b] shrink-0 mt-0.5" />
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Forbidden actions */}
                {activeDept.latestReport.forbidden_actions && (
                  <div>
                    <span className="text-[11px] font-mono text-[#ff8e8e] uppercase block mb-1">Forbidden Actions:</span>
                    <div className="flex flex-wrap gap-2">
                      {activeDept.latestReport.forbidden_actions.map((act, i) => (
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

                {/* Handoff & Admission */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                  <div className="p-3 bg-[#0e131b] rounded-lg border border-[#26303d]">
                    <span className="text-[10px] font-mono text-[#8d9aaa] uppercase block">Handoff Target</span>
                    <strong className="text-xs font-mono text-[#66e3c4]">
                      {activeDept.latestReport.handoff_to || 'command-desk'}
                    </strong>
                  </div>
                  <div className="p-3 bg-[#0e131b] rounded-lg border border-[#26303d]">
                    <span className="text-[10px] font-mono text-[#8d9aaa] uppercase block">cAPI Admission</span>
                    <strong className="text-xs font-mono text-[#eef3f8]">
                      {activeDept.latestReport.capi_admission?.capability || 'governed-mesh'} (
                      {activeDept.latestReport.capi_admission?.status || 'active'})
                    </strong>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
