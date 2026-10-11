import React, { useEffect, useState } from 'react';
import { ActiveTab } from '../types';
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  BarChart3,
  Upload,
  Plus,
  ArrowRight,
  TrendingUp,
  Activity,
  Radio,
  Clock,
  Layers,
  ChevronRight,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { api } from '../api/client';
import { useAsync, toProjectItem, formatLogEvent } from '../api/hooks';

interface DashboardViewProps {
  onNavigate: (tab: ActiveTab) => void;
  onOpenUpload: () => void;
}

const greeting = () => {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
};

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate, onOpenUpload }) => {
  const summary = useAsync(() => api.getDashboardSummary(), []);
  const me = useAsync(() => api.getMe(), []);
  const [tick, setTick] = useState(0);

  // refresh the ingestion stream periodically (SSE feeds the live screens)
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 8000);
    return () => clearInterval(id);
  }, []);
  useEffect(() => {
    if (tick > 0) summary.reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick]);

  const s = summary.data;
  const sev = s?.open_issues_by_severity || {};

  if (summary.loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] gap-3 text-on-surface-variant">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
        <span className="font-body-md text-body-md">Loading dashboard…</span>
      </div>
    );
  }
  if (summary.error) {
    return (
      <div className="m-6 p-5 rounded-xl bg-error-container/20 border border-error/40 flex flex-col gap-2">
        <div className="flex items-center gap-2 text-error font-headline-sm text-headline-sm font-semibold">
          <AlertCircle className="w-5 h-5" /> Backend unavailable
        </div>
        <p className="font-body-md text-body-md text-on-surface-variant">{summary.error}</p>
        <p className="font-body-sm text-body-sm text-outline">
          Start the API (uvicorn app.main:app) and sign in with the seeded demo user, then retry.
        </p>
        <button onClick={summary.reload}
          className="mt-2 self-start h-8 px-3 rounded-lg bg-primary-container text-on-primary-container font-label-md text-label-md">
          Retry
        </button>
      </div>
    );
  }

  const projects = s?.projects || [];
  const logs = (s?.recent_events || []).slice(-50).reverse();

  return (
    <div className="px-4 sm:px-6 py-6 max-w-7xl mx-auto w-full flex flex-col gap-8 animate-in fade-in duration-300">
      {/* Executive Greeting & Action Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-2 border-b border-surface-container-high/40">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="font-label-caps text-label-caps uppercase text-primary tracking-widest bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-md">
              SRS Verification Node
            </span>
            <span className="font-code-sm text-code-sm text-outline">
              {s?.domains_count ?? 0} domains · {s?.total_requirements_count ?? 0} statements
            </span>
          </div>
          <h1 className="font-display text-2xl sm:text-3xl text-on-surface font-semibold tracking-tight mt-1">
            {greeting()}, {me.data?.name || 'Analyst'}.
          </h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            Let’s make your requirements clearer, more testable, and reliable.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onOpenUpload}
            className="h-9 px-3.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface font-label-md text-label-md flex items-center gap-2 transition-all border border-surface-container-high shadow-sm"
          >
            <Upload className="w-4 h-4 text-on-surface-variant" />
            <span>Quick Upload SRS</span>
          </button>
          <button
            onClick={onOpenUpload}
            className="h-9 px-4 rounded-lg bg-primary-container text-on-primary-container font-label-md text-label-md font-semibold flex items-center gap-1.5 hover:opacity-90 active:scale-95 transition-all shadow-md"
          >
            <Plus className="w-4 h-4" />
            <span>New Project</span>
          </button>
        </div>
      </div>

      {/* Metric Overview: High Density Bento Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Active Specifications */}
        <div
          onClick={() => onNavigate('projects')}
          className="p-5 rounded-xl bg-surface-container-low border border-surface-container-high shadow-sm flex flex-col justify-between group hover:bg-surface-container hover:border-outline transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between text-on-surface-variant">
            <span className="font-label-caps text-label-caps uppercase tracking-wider text-outline font-semibold">Active Specifications</span>
            <FileText className="w-5 h-5 text-secondary" />
          </div>
          <div className="mt-4 flex flex-col">
            <div className="flex items-baseline gap-2">
              <span className="font-display text-3xl text-on-surface font-semibold">{s?.active_projects_count ?? 0}</span>
              <span className="font-label-md text-label-md text-on-surface-variant">Projects Enrolled</span>
            </div>
            <div className="mt-2 flex items-center gap-1.5 font-code-sm text-code-sm text-secondary-fixed">
              <span className={`w-2 h-2 rounded-full bg-secondary ${(s?.analyzing_projects_count ?? 0) > 0 ? 'animate-ping' : ''}`} />
              <span>{s?.analyzing_projects_count ?? 0} pending live analysis</span>
            </div>
          </div>
        </div>

        {/* Metric 2: Quality Index */}
        <div
          onClick={() => onNavigate('reports')}
          className="p-5 rounded-xl bg-surface-container-low border border-surface-container-high shadow-sm flex flex-col justify-between group hover:bg-surface-container hover:border-outline transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between text-on-surface-variant">
            <span className="font-label-caps text-label-caps uppercase tracking-wider text-outline font-semibold">Quality Index</span>
            <CheckCircle2 className="w-5 h-5 text-tertiary" />
          </div>
          <div className="mt-4 flex flex-col">
            <div className="flex items-baseline gap-2">
              <span className="font-display text-3xl text-tertiary font-semibold">{s?.overall_quality_score ?? 0}</span>
              <span className="font-code-md text-code-md text-outline">/ 100</span>
            </div>
            <div className={`mt-2 flex items-center gap-1 font-code-sm text-code-sm ${(s?.quality_trend_percentage ?? 0) >= 0 ? 'text-tertiary' : 'text-error'}`}>
              {(s?.quality_trend_percentage ?? 0) >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <Activity className="w-3.5 h-3.5" />}
              <span className="font-semibold">
                {s?.quality_trend_percentage != null && s.quality_trend_percentage !== 0
                  ? `${s.quality_trend_percentage > 0 ? '+' : ''}${s.quality_trend_percentage}`
                  : '—'}
              </span>
              <span className="text-on-surface-variant font-body-sm text-body-sm">vs last run</span>
            </div>
          </div>
        </div>

        {/* Metric 3: Open Ambiguities & Conflicts */}
        <div
          onClick={() => onNavigate('issues')}
          className="p-5 rounded-xl bg-surface-container-low border border-surface-container-high shadow-sm flex flex-col justify-between group hover:bg-surface-container hover:border-outline transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between text-on-surface-variant">
            <span className="font-label-caps text-label-caps uppercase tracking-wider text-outline font-semibold">Open Ambiguities</span>
            <AlertTriangle className="w-5 h-5 text-error" />
          </div>
          <div className="mt-4 flex flex-col">
            <div className="flex items-baseline gap-2">
              <span className="font-display text-3xl text-error font-semibold">{s?.open_issues_count ?? 0}</span>
              <span className="font-label-md text-label-md text-on-surface-variant">Detected</span>
            </div>
            <div className="mt-2 flex items-center gap-2 font-code-sm text-code-sm">
              <span className="text-error bg-error-container/40 border border-error/30 px-1.5 py-0.5 rounded font-semibold">{sev.critical ?? 0} Crit</span>
              <span className="text-on-surface-variant bg-surface-container px-1.5 py-0.5 rounded">{sev.high ?? 0} High</span>
              <span className="text-outline bg-surface-container px-1.5 py-0.5 rounded">{sev.medium ?? 0} Med</span>
            </div>
          </div>
        </div>

        {/* Metric 4: Parsed Requirements */}
        <div
          onClick={() => onNavigate('requirements')}
          className="p-5 rounded-xl bg-surface-container-low border border-surface-container-high shadow-sm flex flex-col justify-between group hover:bg-surface-container hover:border-outline transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between text-on-surface-variant">
            <span className="font-label-caps text-label-caps uppercase tracking-wider text-outline font-semibold">Parsed Requirements</span>
            <BarChart3 className="w-5 h-5 text-primary" />
          </div>
          <div className="mt-4 flex flex-col">
            <div className="flex items-baseline gap-2">
              <span className="font-display text-3xl text-on-surface font-semibold">{s?.total_requirements_count ?? 0}</span>
              <span className="font-label-md text-label-md text-on-surface-variant">Statements</span>
            </div>
            <div className="mt-2 flex items-center gap-1.5 font-code-sm text-code-sm text-on-surface-variant">
              <Layers className="w-3.5 h-3.5 text-outline" />
              <span>Across {s?.domains_count ?? 0} target domains</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Enrolled Projects & Live Telemetry Sweep Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (7 cols): Active Specifications Table */}
        <div className="lg:col-span-7 bg-surface-container-low border border-surface-container-high rounded-xl p-5 shadow-md flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary" />
              <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Enrolled Specifications</h2>
            </div>
            <button
              onClick={() => onNavigate('projects')}
              className="font-code-sm text-code-sm text-primary hover:underline flex items-center gap-1"
            >
              View All Specs <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex flex-col gap-3">
            {projects.length === 0 && (
              <div className="p-6 rounded-xl border border-dashed border-surface-container-high text-center flex flex-col gap-2">
                <p className="font-body-md text-body-md text-on-surface-variant">No specifications enrolled yet.</p>
                <button onClick={onOpenUpload}
                  className="self-center h-8 px-3 rounded-lg bg-primary-container text-on-primary-container font-label-md text-label-md">
                  Upload your first SRS
                </button>
              </div>
            )}
            {projects.map((proj) => {
              const item = toProjectItem(proj);
              return (
                <div
                  key={proj.id}
                  onClick={() => onNavigate(proj.status === 'analyzing' ? 'srs-progress' : 'requirements')}
                  className="p-4 rounded-xl bg-surface-container border border-surface-container-high hover:border-primary/50 transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center text-primary shrink-0 mt-0.5 group-hover:bg-primary-container/20 transition-colors">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold group-hover:text-primary transition-colors">{proj.name}</h3>
                        <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-surface-container-highest text-outline">{proj.version}</span>
                        {proj.status === 'analyzing' && (
                          <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-primary/15 text-primary border border-primary/30">ANALYZING</span>
                        )}
                      </div>
                      <span className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
                        {item.fileName} • {proj.domain}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0 justify-between sm:justify-end border-t sm:border-t-0 pt-2 sm:pt-0 border-surface-container-high">
                    <div className="flex flex-col items-end">
                      <span className="font-label-caps text-label-caps text-outline uppercase">Quality Index</span>
                      <span className="font-code-md text-code-md font-bold text-tertiary">{proj.quality_score}/100</span>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="font-label-caps text-label-caps text-outline uppercase">Issues</span>
                      <span className="font-code-md text-code-md font-bold text-error">{proj.open_ambiguities_count}</span>
                    </div>
                    <ArrowRight className="w-5 h-5 text-outline group-hover:text-primary group-hover:translate-x-1 transition-all" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column (5 cols): Live Telemetry Stream */}
        <div className="lg:col-span-5 bg-surface-container-low border border-surface-container-high rounded-xl p-5 shadow-md flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Radio className="w-5 h-5 text-tertiary animate-pulse" />
              <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Radar Ingestion Stream</h2>
            </div>
            <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-tertiary-container/20 text-tertiary font-semibold">
              GUARD ACTIVE
            </span>
          </div>

          <div className="bg-surface-container-lowest border border-surface-container-high rounded-xl p-4 flex flex-col gap-2.5 font-code-sm text-code-sm overflow-hidden min-h-[260px] max-h-[360px] overflow-y-auto">
            {logs.length === 0 && (
              <span className="text-outline">Waiting for analysis events…</span>
            )}
            {logs.map((log, idx) => (
              <div key={`${log.run_id}-${idx}`} className="flex items-start gap-2 text-on-surface-variant leading-relaxed">
                <span className="text-outline shrink-0">
                  [{log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '--:--:--'}]
                </span>
                <span
                  className={
                    log.tag?.includes('CONFLICT') || log.tag === 'ERROR'
                      ? 'text-error font-semibold'
                      : log.tag?.includes('WARN')
                        ? 'text-amber-300'
                        : log.tag?.includes('RECOMMENDATION') || log.tag?.includes('DISCOVERY')
                          ? 'text-primary'
                          : log.tag?.includes('COMPLETE') || log.tag?.includes('TRACE')
                            ? 'text-tertiary'
                            : ''
                  }
                >
                  {`[${log.tag}] ${log.message}`}
                </span>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between text-outline font-code-sm text-code-sm pt-1">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-outline" /> Live · refreshes every 8s
            </span>
            <button
              onClick={() => onNavigate('srs-progress')}
              className="text-primary hover:underline font-medium flex items-center gap-1"
            >
              Open Live Pipeline <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
