import React from 'react';
import { ActiveTab } from '../types';
import { api } from '../api/client';
import { useActiveProject, useAsync } from '../api/hooks';
import { BarChart3, Download, CheckCircle2, AlertTriangle, ShieldCheck, Loader2, AlertCircle, ExternalLink } from 'lucide-react';

interface ReportsViewProps {
  onNavigate: (tab: ActiveTab) => void;
}

export const ReportsView: React.FC<ReportsViewProps> = () => {
  const { active, activeId } = useActiveProject();
  const report = useAsync(
    () => (activeId ? api.getReport(activeId) : Promise.resolve(null)),
    [activeId],
  );
  const data = report.data;

  if (report.loading || (!activeId && !report.error)) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] gap-3 text-on-surface-variant">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
        <span className="font-body-md text-body-md">Loading audit report…</span>
      </div>
    );
  }
  if (report.error || !data) {
    return (
      <div className="m-6 p-5 rounded-xl bg-error-container/20 border border-error/40 flex flex-col gap-2">
        <div className="flex items-center gap-2 text-error font-semibold">
          <AlertCircle className="w-5 h-5" /> {report.error || 'No report data — analyze a project first.'}
        </div>
        <button onClick={report.reload} className="mt-2 self-start h-8 px-3 rounded-lg bg-primary-container text-on-primary-container font-label-md text-label-md">Retry</button>
      </div>
    );
  }

  const dims = data.score.dimensions || {};
  const conflicts = data.issues.conflicts?.length ?? 0;
  const trend = data.score.trend;

  return (
    <div className="px-4 sm:px-6 py-6 max-w-7xl mx-auto w-full flex flex-col gap-6 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-surface-container-high">
        <div className="flex flex-col gap-1">
          <h1 className="font-headline-lg text-2xl sm:text-3xl text-on-surface font-semibold tracking-tight">Specification Quality Audit Reports</h1>
          <p className="font-body-md text-body-md text-on-surface-variant">Export comprehensive INCOSE ISO/IEC/IEEE 29148 compliance reports</p>
        </div>
        <div className="flex items-center gap-2">
          <a
            href={api.getReportHtmlUrl(activeId!)}
            target="_blank"
            rel="noreferrer"
            className="px-4 py-2 rounded-lg bg-primary text-on-primary font-label-md text-label-md font-semibold flex items-center gap-2 hover:opacity-90 transition-opacity shadow-md"
          >
            <Download className="w-4 h-4" />
            <span>Open Executive Report (Print → PDF)</span>
          </a>
          <a
            href={api.getExportUrl(activeId!, 'issues', 'csv')}
            className="px-3 py-2 rounded-lg bg-surface-container border border-surface-container-high text-on-surface font-label-md text-label-md flex items-center gap-2 hover:border-outline transition-all"
          >
            <Download className="w-4 h-4" /> CSV
          </a>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-surface-container-low border border-surface-container-high flex flex-col gap-3">
          <span className="font-label-caps text-label-caps text-outline uppercase">Overall Quality Score</span>
          <span className="font-display text-4xl text-tertiary font-bold">{data.score.overall} / 100</span>
          <span className="font-body-sm text-body-sm text-on-surface-variant">
            {trend != null
              ? `${trend >= 0 ? '+' : ''}${trend} points compared to the previous revision`
              : 'First analysis — no previous revision to compare'}
          </span>
          <span className="font-code-sm text-code-sm text-outline">{data.project.name} · {data.project.version}</span>
        </div>

        <div className="p-6 rounded-2xl bg-surface-container-low border border-surface-container-high flex flex-col gap-3">
          <span className="font-label-caps text-label-caps text-outline uppercase">INCOSE Rule Compliance</span>
          <span className="font-display text-4xl text-primary font-bold">{data.compliance.incose_pct}%</span>
          <span className="font-body-sm text-body-sm text-on-surface-variant">
            {data.compliance.compliant_requirements} of {data.compliance.total_requirements} statements pass all rules
          </span>
        </div>

        <div className="p-6 rounded-2xl bg-surface-container-low border border-surface-container-high flex flex-col gap-3">
          <span className="font-label-caps text-label-caps text-outline uppercase">Critical Risk Factors</span>
          <span className="font-display text-4xl text-error font-bold">{data.issues.by_severity_open.critical || 0} Critical · {conflicts} Conflicts</span>
          <span className="font-body-sm text-body-sm text-on-surface-variant">
            {data.issues.open} open issues across {data.compliance.total_requirements} requirements · traceability {data.traceability.coverage_pct}%
          </span>
        </div>
      </div>

      {/* Dimension breakdown (real per-dimension means) */}
      <div className="p-6 rounded-2xl bg-surface-container-low border border-surface-container-high flex flex-col gap-4">
        <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary" /> Quality Dimensions
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(dims).map(([dim, value]) => (
            <div key={dim} className="p-4 rounded-xl bg-surface-container border border-surface-container-high flex flex-col gap-2">
              <span className="font-label-caps text-label-caps text-outline uppercase">{dim}</span>
              <div className="h-2 rounded-full bg-surface-container-highest overflow-hidden">
                <div
                  className="h-full bg-primary transition-all"
                  style={{ width: `${value ?? 0}%` }}
                />
              </div>
              <span className="font-code-md text-code-md font-bold text-on-surface">{value ?? '—'}</span>
            </div>
          ))}
        </div>
        <div className="flex flex-wrap gap-3 pt-2 border-t border-surface-container-high">
          <a href={api.getExportUrl(activeId!, 'requirements', 'json')} className="font-code-sm text-code-sm text-primary hover:underline flex items-center gap-1">
            <Download className="w-3.5 h-3.5" /> Export requirements (JSON)
          </a>
          <a href={api.getReportHtmlUrl(activeId!)} target="_blank" rel="noreferrer" className="font-code-sm text-code-sm text-primary hover:underline flex items-center gap-1">
            <ExternalLink className="w-3.5 h-3.5" /> Full audit report
          </a>
        </div>
      </div>
    </div>
  );
};
