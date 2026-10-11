import React from 'react';
import { ActiveTab } from '../types';
import { GitFork, ArrowRight, CheckCircle2, AlertTriangle, Layers, Search } from 'lucide-react';
import { mockRequirements } from '../data/mockData';

interface TraceabilityViewProps {
  onNavigate: (tab: ActiveTab) => void;
}

export const TraceabilityView: React.FC<TraceabilityViewProps> = ({ onNavigate }) => {
  return (
    <div className="px-4 sm:px-6 py-6 max-w-7xl mx-auto w-full flex flex-col gap-6 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-surface-container-high">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="font-label-caps text-label-caps uppercase text-tertiary font-bold">Coverage Rate: 82%</span>
            <span className="w-1 h-1 rounded-full bg-outline" />
            <span className="font-code-sm text-code-sm text-outline">68 Mapped Nodes</span>
          </div>
          <h1 className="font-headline-lg text-2xl sm:text-3xl text-on-surface font-semibold tracking-tight">Traceability Matrix & Dependency Tree</h1>
          <p className="font-body-md text-body-md text-on-surface-variant">Verify end-to-end alignment between system requirements, architecture specs, and verification tests</p>
        </div>
      </div>

      {/* Dependency Map Cards */}
      <div className="bg-surface-container-low border border-surface-container-high rounded-2xl p-6 shadow-md flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface flex items-center gap-2">
            <GitFork className="w-5 h-5 text-tertiary" /> Inter-Requirement Dependency Graph
          </h2>
          <span className="font-code-sm text-code-sm text-outline">Smart Hospital SRS v1.3</span>
        </div>

        <div className="flex flex-col gap-3">
          {mockRequirements.map((req) => (
            <div key={req.id} className="p-4 rounded-xl bg-surface-container border border-surface-container-high flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-3">
                <span className="font-code-md text-code-md font-bold px-2.5 py-1 rounded bg-surface-container-lowest text-primary">
                  {req.id}
                </span>
                <div className="flex flex-col">
                  <span className="font-body-md text-body-md font-semibold text-on-surface">{req.title}</span>
                  <span className="font-code-sm text-code-sm text-outline mt-0.5">{req.originalText}</span>
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <span className="font-label-caps text-label-caps text-outline uppercase">Linked Targets:</span>
                <div className="flex items-center gap-1.5 flex-wrap">
                  {req.traceabilityLinks?.map((link, idx) => (
                    <span key={idx} className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-surface-container-highest text-tertiary font-semibold border border-tertiary/20">
                      {link}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
