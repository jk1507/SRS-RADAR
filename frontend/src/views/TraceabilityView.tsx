import React from 'react';
import { ActiveTab } from '../types';
import { GitFork, ArrowRight, CheckCircle2, AlertTriangle, Layers, Search, Loader2, AlertCircle } from 'lucide-react';
import { api } from '../api/client';
import { useActiveProject, useAsync } from '../api/hooks';

interface TraceabilityViewProps {
  onNavigate: (tab: ActiveTab) => void;
}

export const TraceabilityView: React.FC<TraceabilityViewProps> = ({ onNavigate }) => {
  const { active, activeId } = useActiveProject();
  const matrix = useAsync(
    () => (activeId ? api.getTraceMatrix(activeId) : Promise.resolve(null)),
    [activeId],
  );

  if (matrix.loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] gap-3 text-on-surface-variant">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
        <span className="font-body-md text-body-md">Loading traceability matrix…</span>
      </div>
    );
  }
  if (matrix.error || !matrix.data) {
    return (
      <div className="m-6 p-5 rounded-xl bg-error-container/20 border border-error/40 flex flex-col gap-2">
        <div className="flex items-center gap-2 text-error font-semibold"><AlertCircle className="w-5 h-5" /> {matrix.error || 'No traceability data — analyze a project first.'}</div>
        <button onClick={matrix.reload} className="mt-2 self-start h-8 px-3 rounded-lg bg-primary-container text-on-primary-container font-label-md text-label-md">Retry</button>
      </div>
    );
  }

  const rows = matrix.data.rows;
  const totals = matrix.data.totals as Record<string, any>;

  return (
    <div className="px-4 sm:px-6 py-6 max-w-7xl mx-auto w-full flex flex-col gap-6 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-surface-container-high">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="font-label-caps text-label-caps uppercase text-tertiary font-bold">Coverage Rate: {totals.linked_pct ?? 0}%</span>
            <span className="w-1 h-1 rounded-full bg-outline" />
            <span className="font-code-sm text-code-sm text-outline">
              {totals.requirements ?? 0} Requirements · {totals.targets ?? 0} Imported Targets
            </span>
          </div>
          <h1 className="font-headline-lg text-2xl sm:text-3xl text-on-surface font-semibold tracking-tight">Traceability Matrix & Dependency Tree</h1>
          <p className="font-body-md text-body-md text-on-surface-variant">
            Verify end-to-end alignment for {active?.name || 'this project'} — {totals.fully_traced_pct ?? 0}% fully traced,
            {(Array.isArray(totals.gaps) ? totals.gaps.length : 0)} gaps need links
          </p>
        </div>
      </div>

      {/* Dependency Map Cards */}
      <div className="bg-surface-container-low border border-surface-container-high rounded-2xl p-6 shadow-md flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface flex items-center gap-2">
            <GitFork className="w-5 h-5 text-tertiary" /> Inter-Requirement Dependency Graph
          </h2>
          <span className="font-code-sm text-code-sm text-outline">{active?.name || '—'}</span>
        </div>

        <div className="flex flex-col gap-3 max-h-[560px] overflow-y-auto pr-1">
          {rows.length === 0 && (
            <p className="font-body-md text-body-md text-on-surface-variant py-6 text-center">
              No requirements extracted yet — run an analysis first.
            </p>
          )}
          {rows.map((row) => {
            const links = [
              ...row.arch_targets.map((t) => ({ ...t, kind: 'ARCH' })),
              ...row.test_targets.map((t) => ({ ...t, kind: 'TEST' })),
              ...row.compliance_targets.map((t) => ({ ...t, kind: 'COMP' })),
            ];
            return (
              <div key={row.req_id} className="p-4 rounded-xl bg-surface-container border border-surface-container-high flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-start gap-3 min-w-0">
                  <span className="font-code-md text-code-md font-bold px-2.5 py-1 rounded bg-surface-container-lowest text-primary shrink-0">
                    {row.req_id}
                  </span>
                  <div className="flex flex-col min-w-0">
                    <span className="font-body-md text-body-md font-semibold text-on-surface truncate">
                      {row.req_clause.slice(0, 110)}{row.req_clause.length > 110 ? '…' : ''}
                    </span>
                    <span className="font-code-sm text-code-sm text-outline mt-0.5">
                      {row.status === 'missing'
                        ? 'GAP — not linked to any target'
                        : `coverage ${row.coverage_percentage}% · ${row.status}`}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <span className="font-label-caps text-label-caps text-outline uppercase">Linked Targets:</span>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {links.length === 0 && (
                      <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-error-container/30 text-error font-semibold border border-error/30">
                        NO LINKS
                      </span>
                    )}
                    {links.map((link, idx) => (
                      <span
                        key={`${link.link_id}-${idx}`}
                        title={`${link.kind} · ${link.name} · ${link.status}${link.status === 'suggested' ? ` (AI ${Math.round(link.confidence * 100)}%)` : ''}`}
                        className={`font-code-sm text-code-sm px-2 py-0.5 rounded font-semibold border ${
                          link.status === 'confirmed'
                            ? 'bg-surface-container-highest text-tertiary border-tertiary/20'
                            : 'bg-surface-container-highest text-primary border-primary/30 border-dashed'
                        }`}
                      >
                        {link.code}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
