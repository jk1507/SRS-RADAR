import React from 'react';
import { ActiveTab } from '../types';
import { BarChart3, Download, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';

interface ReportsViewProps {
  onNavigate: (tab: ActiveTab) => void;
}

export const ReportsView: React.FC<ReportsViewProps> = () => {
  return (
    <div className="px-4 sm:px-6 py-6 max-w-7xl mx-auto w-full flex flex-col gap-6 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-surface-container-high">
        <div className="flex flex-col gap-1">
          <h1 className="font-headline-lg text-2xl sm:text-3xl text-on-surface font-semibold tracking-tight">Specification Quality Audit Reports</h1>
          <p className="font-body-md text-body-md text-on-surface-variant">Export comprehensive INCOSE ISO/IEC/IEEE 29148 compliance reports</p>
        </div>
        <button
          onClick={() => alert('Exporting full executive PDF report...')}
          className="px-4 py-2 rounded-lg bg-primary text-on-primary font-label-md text-label-md font-semibold flex items-center gap-2 hover:opacity-90 transition-opacity shadow-md self-start sm:self-auto"
        >
          <Download className="w-4 h-4" />
          <span>Download Executive PDF</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-surface-container-low border border-surface-container-high flex flex-col gap-3">
          <span className="font-label-caps text-label-caps text-outline uppercase">Overall Quality Score</span>
          <span className="font-display text-4xl text-tertiary font-bold">83.3 / 100</span>
          <span className="font-body-sm text-body-sm text-on-surface-variant">+5.4% improvement compared to last specification revision</span>
        </div>

        <div className="p-6 rounded-2xl bg-surface-container-low border border-surface-container-high flex flex-col gap-3">
          <span className="font-label-caps text-label-caps text-outline uppercase">INCOSE Rule Compliance</span>
          <span className="font-display text-4xl text-primary font-bold">91.2%</span>
          <span className="font-body-sm text-body-sm text-on-surface-variant">78 of 84 statements adhere to imperative 'shall' criteria</span>
        </div>

        <div className="p-6 rounded-2xl bg-surface-container-low border border-surface-container-high flex flex-col gap-3">
          <span className="font-label-caps text-label-caps text-outline uppercase">Critical Risk Factors</span>
          <span className="font-display text-4xl text-error font-bold">3 Conflicts</span>
          <span className="font-body-sm text-body-sm text-on-surface-variant">Contradictions identified in security auto-lock and replication SLA</span>
        </div>
      </div>
    </div>
  );
};
