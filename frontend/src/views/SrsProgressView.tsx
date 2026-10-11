import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ActiveTab } from '../types';
import {
  FileText,
  CheckCircle2,
  RotateCw,
  Lock,
  Clock,
  Activity,
  ArrowRight,
  Sparkles,
  AlertTriangle,
  Play,
  Loader2,
  AlertCircle,
  ShieldCheck,
  XCircle,
} from 'lucide-react';
import { AnalysisRunData, api } from '../api/client';
import { useActiveProject, useAsync } from '../api/hooks';

interface SrsProgressViewProps {
  onNavigate: (tab: ActiveTab) => void;
}

const STAGES = [
  'Reading document structure',
  'Semantic clarity & vague-term scan',
  'Requirement conflict matrix',
  'Testability & SLA verification',
  'Traceability analysis',
  'Final scoring & recommendations',
];

const STAGE_RESULTS: { [k: number]: string } = {
  0: 'requirements extracted, hierarchical schema formed',
  1: 'vague-term scan + INCOSE rule lint applied',
  2: 'interval + Z3 constraint cross-check complete',
  3: 'testable rewrites synthesized for flagged statements',
  4: 'coverage vs imported architecture/test targets',
  5: 'deterministic 7-dimension score computed',
};

interface LiveEvent {
  stage: number;
  stage_index: number;
  processed: number;
  total: number;
  percentage: number;
  tag: string;
  message: string;
  req_code?: string;
  status?: string;
}

export const SrsProgressView: React.FC<SrsProgressViewProps> = ({ onNavigate }) => {
  const { active, activeId, reload: reloadProjects } = useActiveProject();
  const runs = useAsync(
    () => (activeId ? api.getRuns(activeId) : Promise.resolve([])),
    [activeId],
  );

  const [runId, setRunId] = useState<string | null>(null);
  const [run, setRun] = useState<AnalysisRunData | null>(null);
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const logRef = useRef<HTMLDivElement | null>(null);

  // pick: active run from summary, else newest run of the active project
  useEffect(() => {
    if (!runs.data || runs.data.length === 0) {
      setRunId(null);
      return;
    }
    const activeRun = runs.data.find((r) => r.status === 'pending' || r.status === 'in_progress');
    const next = (activeRun || runs.data[0]).id;
    setRunId((prev) => prev || next);
  }, [runs.data]);

  // load run detail whenever runId changes
  useEffect(() => {
    if (!runId) return;
    setEvents([]);
    setError(null);
    api.getRun(runId).then(setRun).catch((e) => setError(e.message));
  }, [runId]);

  // subscribe to SSE for live progress
  useEffect(() => {
    if (!runId) return;
    const source = new EventSource(api.getRunEventsUrl(runId));
    source.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data) as LiveEvent & { status?: string; scores?: any };
        setEvents((prev) => [...prev.slice(-200), data]);
        setRun((prev) => (prev ? {
          ...prev,
          progress_percentage: data.percentage ?? prev.progress_percentage,
          processed_requirements: data.processed ?? prev.processed_requirements,
          total_requirements: data.total || prev.total_requirements,
          stage_index: data.stage_index ?? prev.stage_index,
          current_stage: `Stage ${(data.stage_index ?? 0) + 1} of 6: ${STAGES[data.stage_index ?? 0]}`,
          eta_seconds: (data as any).eta_seconds ?? prev.eta_seconds,
          throughput_req_per_sec: (data as any).throughput ?? prev.throughput_req_per_sec,
          status: data.status || prev.status,
        } : prev));
        if (data.status === 'completed' || data.status === 'failed') {
          source.close();
          api.getRun(runId).then(setRun).catch(() => undefined);
          runs.reload();
          reloadProjects();
        }
      } catch {
        /* ignore malformed frames */
      }
    };
    source.onerror = () => {
      /* EventSource auto-reconnects with Last-Event-ID */
    };
    return () => source.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId]);

  // fallback polling while running (covers missed events)
  useEffect(() => {
    if (!runId || !run) return;
    if (run.status !== 'pending' && run.status !== 'in_progress') return;
    const id = setInterval(() => {
      api.getRunStatus(runId).then((s) => {
        setRun((prev) => (prev ? {
          ...prev,
          status: s.status,
          progress_percentage: s.percentage,
          processed_requirements: s.processed,
          total_requirements: s.total,
          eta_seconds: s.eta_seconds,
          error: s.error,
        } : prev));
        if (s.status === 'completed' || s.status === 'failed') {
          api.getRun(runId).then(setRun).catch(() => undefined);
          runs.reload();
        }
      }).catch(() => undefined);
    }, 3000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId, run?.status]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [events.length]);

  const progress = Math.round(run?.progress_percentage ?? 0);
  const stageIndex = run?.stage_index ?? 0;
  const isRunning = run?.status === 'pending' || run?.status === 'in_progress';

  const logLines = useMemo(() => {
    const fromRun = (run?.logs || []).map((l) => ({
      text: `[${l.tag || l.level}] ${l.message}`, level: l.level,
    }));
    const live = events.map((e) => ({
      text: `[${e.tag}] ${e.message}`,
      level: e.tag === 'ERROR' ? 'ERROR' : e.tag.endsWith('WARN') ? 'WARN' : 'INFO',
    }));
    return [...fromRun, ...live].slice(-120);
  }, [run?.logs, events]);

  const formatSeconds = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}s`;
  };

  const handleCancel = async () => {
    if (!runId) return;
    setBusy(true);
    try { await api.cancelRun(runId); await api.getRun(runId).then(setRun); }
    catch (e) { alert((e as Error).message); }
    finally { setBusy(false); }
  };

  const handleRetry = async () => {
    if (!runId) return;
    setBusy(true);
    try {
      const res = await api.retryRun(runId) as { data?: { run_id?: string } };
      setRunId(res?.data?.run_id || runId);
      runs.reload();
    } catch (e) { alert((e as Error).message); }
    finally { setBusy(false); }
  };

  if (runs.loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] gap-3 text-on-surface-variant">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
        <span className="font-body-md text-body-md">Loading analysis runs…</span>
      </div>
    );
  }

  if (!run || (!runId && runs.data?.length === 0)) {
    return (
      <div className="px-6 py-10 max-w-3xl mx-auto w-full flex flex-col gap-3 items-center text-center">
        <AlertCircle className="w-8 h-8 text-outline" />
        <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">No analysis yet</h2>
        <p className="font-body-md text-body-md text-on-surface-variant">
          {active ? `Upload or analyze a document for “${active.name}” to watch the live pipeline.`
                  : 'Create a project and upload an SRS first.'}
        </p>
        {activeId && (
          <button
            onClick={() => api.analyzeProject(activeId)
              .then((res) => { setRunId(res.id); runs.reload(); })
              .catch((e) => alert(e.message))}
            className="mt-2 h-9 px-4 rounded-lg bg-primary text-on-primary font-label-md text-label-md font-semibold flex items-center gap-2"
          >
            <Play className="w-4 h-4" /> Start Analysis
          </button>
        )}
      </div>
    );
  }

  const sha = (run.document_sha256 || '').slice(0, 6);
  const sizeMb = (run.document_size_bytes / (1024 * 1024)).toFixed(1);

  return (
    <div className="relative w-full overflow-hidden px-4 sm:px-8 py-8 min-h-[calc(100vh-3.5rem)] flex flex-col justify-between animate-in fade-in duration-300">
      {/* Background Ambient Glows */}
      <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[720px] h-[380px] bg-primary/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute top-1/3 -right-24 w-[420px] h-[420px] bg-secondary-container/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 left-12 w-[360px] h-[360px] bg-tertiary-container/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="relative z-10 w-full max-w-5xl mx-auto flex flex-col gap-8">
        {/* Document Header Card */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-surface-container-lowest/80 backdrop-blur-md px-6 py-4 rounded-xl border border-surface-container-high shadow-lg">
          <div className="flex items-center gap-4 min-w-0">
            <div className="w-10 h-10 rounded-lg bg-surface-container-high border border-surface-container-highest flex items-center justify-center text-primary shadow-sm shrink-0">
              <FileText className="w-5 h-5 text-primary" />
            </div>
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-headline-sm text-headline-sm text-on-surface font-semibold truncate">
                  {run.document_filename || '—'}
                </span>
                <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-surface-container text-on-surface-variant font-medium">
                  {sizeMb} MB
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-outline font-code-sm text-code-sm mt-0.5">
                <span>Parsed: <strong className="text-on-surface font-semibold">{run.total_requirements} statements</strong></span>
                <span className="w-1 h-1 rounded-full bg-outline-variant" />
                <span>Context: <strong className="text-on-surface font-semibold">{run.context_standard}</strong></span>
                <span className="w-1 h-1 rounded-full bg-outline-variant" />
                <span>Hash: <span className="font-label-caps text-label-caps text-primary">0x{(run.document_sha256 || '').slice(0, 4).toUpperCase()}…{(run.document_sha256 || '').slice(-4).toUpperCase()}</span></span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-6 self-start md:self-auto shrink-0 border-t md:border-t-0 pt-3 md:pt-0 border-surface-container-high">
            <div className="flex flex-col text-left md:text-right">
              <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider">Engine Mode</span>
              <span className="font-label-md text-label-md text-tertiary font-semibold flex items-center gap-1.5 justify-start md:justify-end">
                <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-tertiary animate-pulse' : 'bg-outline'}`} />
                {run.analysis_mode} · {run.llm_status}
              </span>
            </div>
            <div className="h-8 w-px bg-surface-container-high hidden sm:block" />
            <div className="flex flex-col text-left md:text-right">
              <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider">Privacy Ring</span>
              <span className="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1 justify-start md:justify-end"
                    title={active?.retention_mode === 'zero_retention'
                      ? 'Original file deleted after parsing; only extracted text, findings and SHA-256 stored. Text is sent to the configured LLM provider.'
                      : 'Standard retention: encrypted storage of the original document alongside extracted findings. Text is sent to the configured LLM provider.'}>
                <Lock className="w-3.5 h-3.5 text-primary" />
                {active?.retention_mode === 'zero_retention' ? 'Zero-Retention Mode' : 'Standard Retention'}
              </span>
            </div>
          </div>
        </div>

        {/* Live Scan Hero Panel */}
        <div className="bg-surface-container-low border border-surface-container-high rounded-2xl p-6 sm:p-10 shadow-xl relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-tertiary/5 pointer-events-none" />

          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* Left Info Column */}
            <div className="lg:col-span-7 flex flex-col gap-6">
              <div className="flex flex-wrap items-center gap-3">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-container/20 border border-primary/30 text-primary font-label-caps text-label-caps uppercase tracking-wider">
                  <span className={`w-2 h-2 rounded-full bg-primary ${isRunning ? 'animate-ping' : ''}`} />
                  <span>
                    {run.status === 'completed' ? 'Analysis Complete'
                      : run.status === 'failed' ? 'Analysis Failed'
                        : run.status === 'cancelled' ? 'Run Cancelled'
                          : 'Live Scan Running'}
                  </span>
                </div>
                <span className="font-code-sm text-code-sm text-outline">Run #{(run.id || '').slice(0, 8)}</span>
                <span className="w-1 h-1 rounded-full bg-surface-container-highest" />
                <span className="font-code-sm text-code-sm text-tertiary font-semibold">
                  {run.lint_mode} lint · Real-Time Ingestion
                </span>
              </div>

              <div className="flex flex-col gap-2">
                <h1 className="font-display text-2xl sm:text-3xl lg:text-4xl text-on-surface tracking-tight font-semibold">
                  Analyzing {active?.name || run.document_filename}
                </h1>
                <p className="font-body-lg text-body-lg text-on-surface-variant max-w-xl">
                  We’re checking <span className="text-on-surface font-medium">{run.total_requirements || '…'} requirement statements</span> for ambiguity, conflicts, testability, and traceability gaps.
                </p>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
                <div className="bg-surface-container border border-surface-container-high p-3.5 rounded-xl flex flex-col gap-1">
                  <span className="font-label-caps text-label-caps text-outline uppercase">Elapsed Time</span>
                  <span className="font-code-md text-code-md text-on-surface font-bold tracking-tight">{formatSeconds(run.elapsed_seconds)}</span>
                </div>
                <div className="bg-surface-container border border-surface-container-high p-3.5 rounded-xl flex flex-col gap-1">
                  <span className="font-label-caps text-label-caps text-outline uppercase">Est. Remaining</span>
                  <span className="font-code-md text-code-md text-primary font-bold tracking-tight">
                    {run.eta_seconds > 0 ? formatSeconds(run.eta_seconds) : '—'}
                  </span>
                </div>
                <div className="bg-surface-container border border-surface-container-high p-3.5 rounded-xl flex flex-col gap-1 col-span-2 sm:col-span-1">
                  <span className="font-label-caps text-label-caps text-outline uppercase">Speed</span>
                  <span className="font-code-md text-code-md text-tertiary font-bold tracking-tight">
                    {run.throughput_req_per_sec.toFixed(1)} req/s
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between text-outline">
                  <span className="font-label-caps text-label-caps uppercase tracking-wider">Pipeline Completion</span>
                  <span className="font-code-sm text-code-sm text-primary font-semibold">Stage {stageIndex + 1} of 6</span>
                </div>
                <div className="w-full bg-surface-container h-2.5 rounded-full overflow-hidden flex gap-1 p-0.5 border border-surface-container-high">
                  {[0, 1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className={`h-full rounded-full w-1/6 transition-all duration-500 ${
                      i < stageIndex ? 'bg-tertiary'
                        : i === stageIndex && isRunning ? 'bg-primary animate-pulse'
                          : i <= stageIndex ? 'bg-tertiary' : 'bg-surface-container-high'}`} />
                  ))}
                </div>
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-error-container/20 border border-error/40 text-error font-body-sm text-body-sm">
                  {error}
                </div>
              )}
            </div>

            {/* Right Gauge Column */}
            <div className="lg:col-span-5 flex flex-col items-center justify-center p-6 bg-surface-container/60 border border-surface-container-high rounded-2xl relative">
              <div className="relative w-52 h-52 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
                  <circle className="text-surface-container-high" cx="80" cy="80" fill="transparent" r="68" stroke="currentColor" strokeWidth="8" />
                  <circle className="text-primary transition-all duration-700" cx="80" cy="80" fill="transparent" r="68" stroke="currentColor" strokeDasharray="427.25" strokeDashoffset={427.25 * (1 - progress / 100)} strokeLinecap="round" strokeWidth="8" />
                  <circle className="text-tertiary/40" cx="80" cy="80" fill="transparent" r="54" stroke="currentColor" strokeDasharray="339.29" strokeDashoffset="100" strokeLinecap="round" strokeWidth="2" />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="font-display text-4xl sm:text-5xl leading-none text-on-surface font-extrabold tracking-tight">
                    {progress}<span className="text-primary text-2xl">%</span>
                  </span>
                  <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider mt-1">Processed</span>
                  <span className="font-code-sm text-code-sm text-tertiary mt-0.5 font-semibold">
                    {run.processed_requirements} / {run.total_requirements || '—'} REQ
                  </span>
                </div>
              </div>

              <div className="mt-4 flex items-center gap-2 px-4 py-1.5 rounded-full bg-surface-container-lowest border border-surface-container-high text-outline shadow-sm">
                {isRunning ? <RotateCw className="w-4 h-4 text-primary animate-spin" />
                  : run.status === 'completed' ? <ShieldCheck className="w-4 h-4 text-tertiary" />
                    : <XCircle className="w-4 h-4 text-error" />}
                <span className="font-code-sm text-code-sm text-on-surface">
                  {run.status === 'completed' ? `Done — score ${run.scores_json?.project_score ?? '—'}`
                    : run.status === 'failed' ? `Failed: ${run.error || 'unknown error'}`
                      : run.current_stage}
                </span>
              </div>

              {(isRunning || run.status === 'failed' || run.status === 'cancelled') && (
                <div className="mt-4 flex items-center gap-2">
                  {isRunning && (
                    <button onClick={handleCancel} disabled={busy}
                      className="px-4 py-1.5 rounded-lg bg-error-container/20 border border-error/40 text-error font-label-md text-label-md font-semibold hover:bg-error-container/40 transition-colors">
                      Cancel run
                    </button>
                  )}
                  {(run.status === 'failed' || run.status === 'cancelled') && (
                    <button onClick={handleRetry} disabled={busy}
                      className="px-4 py-1.5 rounded-lg bg-primary text-on-primary font-label-md text-label-md font-semibold hover:opacity-90 transition-opacity flex items-center gap-1.5">
                      <RotateCw className="w-3.5 h-3.5" /> Retry failed
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Pipeline Stages & Live Telemetry Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column (7 cols): Pipeline Execution Steps */}
          <div className="lg:col-span-7 bg-surface-container-low border border-surface-container-high rounded-xl p-6 shadow-md flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="font-headline-sm text-headline-sm font-semibold text-on-surface flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" />
                Scan Pipeline Sequence
              </h2>
              <span className="font-code-sm text-code-sm text-outline">
                Stage {String(stageIndex + 1).padStart(2, '0')}: {isRunning ? 'Active Execution' : run.status}
              </span>
            </div>

            <div className="flex flex-col gap-2.5 max-h-[420px] overflow-y-auto pr-1">
              {STAGES.map((label, i) => {
                const state = i < stageIndex || (!isRunning && run.status === 'completed')
                  ? 'passed'
                  : i === stageIndex && isRunning ? 'running'
                    : run.status === 'failed' && i === stageIndex ? 'failed' : 'pending';
                return (
                  <div key={i}
                    className={`flex items-start justify-between p-3.5 rounded-xl border ${
                      state === 'running' ? 'bg-primary-container/10 border-primary/30'
                        : 'bg-surface-container/60 border-surface-container-high'}`}>
                    <div className="flex items-start gap-3">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5 font-bold ${
                        state === 'passed' ? 'bg-tertiary-container/30 text-tertiary'
                          : state === 'running' ? 'bg-primary/20 text-primary'
                            : state === 'failed' ? 'bg-error-container/40 text-error'
                              : 'bg-surface-container-high text-outline'}`}>
                        {state === 'passed' ? <CheckCircle2 className="w-4 h-4" />
                          : state === 'running' ? <RotateCw className="w-4 h-4 animate-spin" />
                            : state === 'failed' ? <AlertTriangle className="w-4 h-4" />
                              : <Clock className="w-4 h-4" />}
                      </div>
                      <div className="flex flex-col">
                        <span className={`font-body-md text-body-md font-medium ${
                          state === 'running' ? 'text-primary font-semibold' : 'text-on-surface'}`}>
                          {i + 1}. {label}
                        </span>
                        <span className="font-code-sm text-code-sm text-outline">
                          {i <= stageIndex ? STAGE_RESULTS[i] : 'pending'}
                        </span>
                      </div>
                    </div>
                    <span className={`font-code-sm text-code-sm px-2.5 py-0.5 rounded-full font-semibold shrink-0 ${
                      state === 'passed' ? 'bg-tertiary-container/20 text-tertiary'
                        : state === 'running' ? 'bg-primary-container/30 text-primary animate-pulse'
                          : state === 'failed' ? 'bg-error-container/30 text-error'
                            : 'bg-surface-container-high text-outline'}`}>
                      {state === 'passed' ? 'Passed'
                        : state === 'running' ? 'Running'
                          : state === 'failed' ? 'Failed' : 'Queued'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column (5 cols): Live Ingestion Stream & Action CTA */}
          <div className="lg:col-span-5 bg-surface-container-low border border-surface-container-high rounded-xl p-6 shadow-md flex flex-col justify-between gap-6">
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h3 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Scan Telemetry Stream</h3>
                <span className="font-code-sm text-code-sm text-tertiary flex items-center gap-1">
                  <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-tertiary animate-pulse' : 'bg-outline'}`} />
                  {isRunning ? 'Live Stream' : 'Idle'}
                </span>
              </div>
              <div ref={logRef}
                className="bg-surface-container-lowest border border-surface-container-high rounded-xl p-3.5 font-code-sm text-code-sm flex flex-col gap-2 max-h-52 overflow-y-auto">
                {logLines.length === 0 && <span className="text-outline">Waiting for events…</span>}
                {logLines.map((log, index) => (
                  <div key={index} className="text-on-surface-variant leading-relaxed">
                    <span className="text-outline mr-2">{index + 1}.</span>
                    <span className={log.text.includes('CONFLICT') || log.level === 'ERROR' ? 'text-error font-semibold'
                      : log.level === 'WARN' || log.text.includes('WARN') ? 'text-amber-300'
                        : log.text.includes('COMPLETE') || log.text.includes('TRACE') ? 'text-tertiary' : ''}>
                      {log.text}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Action Navigation CTAs */}
            <div className="flex flex-col sm:flex-row items-center gap-3 border-t border-surface-container-high pt-4">
              <button
                onClick={() => onNavigate('requirements')}
                className="w-full sm:w-1/2 py-2.5 px-4 rounded-xl bg-primary text-on-primary font-label-md text-label-md font-semibold hover:opacity-90 transition-opacity flex items-center justify-center gap-2 shadow-md"
              >
                <span>Inspect Requirements Canvas</span>
                <ArrowRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => onNavigate('issues')}
                className="w-full sm:w-1/2 py-2.5 px-4 rounded-xl bg-surface-container hover:bg-surface-container-high text-on-surface font-label-md text-label-md font-semibold transition-colors border border-surface-container-high flex items-center justify-center gap-2"
              >
                <AlertTriangle className="w-4 h-4 text-error" />
                <span>Resolve Conflicts</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
