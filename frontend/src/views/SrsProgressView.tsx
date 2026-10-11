import React, { useState, useEffect } from 'react';
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
  Play
} from 'lucide-react';
import { mockLiveTelemetryLogs } from '../data/mockData';

interface SrsProgressViewProps {
  onNavigate: (tab: ActiveTab) => void;
}

export const SrsProgressView: React.FC<SrsProgressViewProps> = ({ onNavigate }) => {
  const [progress, setProgress] = useState(98);
  const [elapsed, setElapsed] = useState(52);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatSeconds = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `0${m}:${s < 10 ? '0' : ''}${s}s`;
  };

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
                <span className="font-headline-sm text-headline-sm text-on-surface font-semibold truncate">Smart-Hospital-SRS-v1.3.pdf</span>
                <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-surface-container text-on-surface-variant font-medium">2.4 MB</span>
              </div>
              <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-outline font-code-sm text-code-sm mt-0.5">
                <span>Parsed: <strong className="text-on-surface font-semibold">84 statements</strong></span>
                <span className="w-1 h-1 rounded-full bg-outline-variant" />
                <span>Context: <strong className="text-on-surface font-semibold">ISO/IEC/IEEE 29148</strong></span>
                <span className="w-1 h-1 rounded-full bg-outline-variant" />
                <span>Hash: <span className="font-label-caps text-label-caps text-primary">0x9E2F...C1A0</span></span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-6 self-start md:self-auto shrink-0 border-t md:border-t-0 pt-3 md:pt-0 border-surface-container-high">
            <div className="flex flex-col text-left md:text-right">
              <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider">Engine Mode</span>
              <span className="font-label-md text-label-md text-tertiary font-semibold flex items-center gap-1.5 justify-start md:justify-end">
                <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse" />
                Deep Semantics v2.4
              </span>
            </div>
            <div className="h-8 w-px bg-surface-container-high hidden sm:block" />
            <div className="flex flex-col text-left md:text-right">
              <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider">Privacy Ring</span>
              <span className="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1 justify-start md:justify-end">
                <Lock className="w-3.5 h-3.5 text-primary" />
                Zero-Retention Airgap
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
                  <span className="w-2 h-2 rounded-full bg-primary animate-ping" />
                  <span>Live Scan Running</span>
                </div>
                <span className="font-code-sm text-code-sm text-outline">Thread ID #8094</span>
                <span className="w-1 h-1 rounded-full bg-surface-container-highest" />
                <span className="font-code-sm text-code-sm text-tertiary font-semibold">Real-Time Ingestion</span>
              </div>

              <div className="flex flex-col gap-2">
                <h1 className="font-display text-2xl sm:text-3xl lg:text-4xl text-on-surface tracking-tight font-semibold">
                  Analyzing Smart Hospital SRS
                </h1>
                <p className="font-body-lg text-body-lg text-on-surface-variant max-w-xl">
                  We’re checking <span className="text-on-surface font-medium">84 requirement statements</span> for ambiguity, conflicts, testability, and traceability gaps across your clinical specification model.
                </p>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
                <div className="bg-surface-container border border-surface-container-high p-3.5 rounded-xl flex flex-col gap-1">
                  <span className="font-label-caps text-label-caps text-outline uppercase">Elapsed Time</span>
                  <span className="font-code-md text-code-md text-on-surface font-bold tracking-tight">{formatSeconds(elapsed)}</span>
                </div>
                <div className="bg-surface-container border border-surface-container-high p-3.5 rounded-xl flex flex-col gap-1">
                  <span className="font-label-caps text-label-caps text-outline uppercase">Est. Remaining</span>
                  <span className="font-code-md text-code-md text-primary font-bold tracking-tight">00:01s</span>
                </div>
                <div className="bg-surface-container border border-surface-container-high p-3.5 rounded-xl flex flex-col gap-1 col-span-2 sm:col-span-1">
                  <span className="font-label-caps text-label-caps text-outline uppercase">Speed</span>
                  <span className="font-code-md text-code-md text-tertiary font-bold tracking-tight">9.3 req/s</span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between text-outline">
                  <span className="font-label-caps text-label-caps uppercase tracking-wider">Pipeline Completion</span>
                  <span className="font-code-sm text-code-sm text-primary font-semibold">Stage 4 of 6</span>
                </div>
                <div className="w-full bg-surface-container h-2.5 rounded-full overflow-hidden flex gap-1 p-0.5 border border-surface-container-high">
                  <div className="h-full bg-tertiary rounded-full w-1/6 transition-all duration-500" />
                  <div className="h-full bg-tertiary rounded-full w-1/6 transition-all duration-500" />
                  <div className="h-full bg-tertiary rounded-full w-1/6 transition-all duration-500" />
                  <div className="h-full bg-primary rounded-full w-1/6 animate-pulse transition-all duration-500" />
                  <div className="h-full bg-surface-container-high rounded-full w-1/6" />
                  <div className="h-full bg-surface-container-high rounded-full w-1/6" />
                </div>
              </div>
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
                  <span className="font-code-sm text-code-sm text-tertiary mt-0.5 font-semibold">82 / 84 REQ</span>
                </div>
              </div>

              <div className="mt-4 flex items-center gap-2 px-4 py-1.5 rounded-full bg-surface-container-lowest border border-surface-container-high text-outline shadow-sm">
                <RotateCw className="w-4 h-4 text-primary animate-spin" />
                <span className="font-code-sm text-code-sm text-on-surface">Validating semantic matrix...</span>
              </div>
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
              <span className="font-code-sm text-code-sm text-outline">Stage 04: Active Execution</span>
            </div>

            <div className="flex flex-col gap-2.5">
              <div className="flex items-start justify-between p-3.5 rounded-xl bg-surface-container/60 border border-surface-container-high">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-tertiary-container/30 text-tertiary flex items-center justify-center shrink-0 mt-0.5 font-bold">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div className="flex flex-col">
                    <span className="font-body-md text-body-md font-medium text-on-surface">1. Reading document structure</span>
                    <span className="font-code-sm text-code-sm text-outline">84 requirements extracted, hierarchical schema formed</span>
                  </div>
                </div>
                <span className="font-code-sm text-code-sm px-2.5 py-0.5 rounded-full bg-tertiary-container/20 text-tertiary font-semibold shrink-0">Passed (0.4s)</span>
              </div>

              <div className="flex items-start justify-between p-3.5 rounded-xl bg-surface-container/60 border border-surface-container-high">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-tertiary-container/30 text-tertiary flex items-center justify-center shrink-0 mt-0.5 font-bold">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div className="flex flex-col">
                    <span className="font-body-md text-body-md font-medium text-on-surface">2. Semantic clarity & vague word scan</span>
                    <span className="font-code-sm text-code-sm text-outline">Scanned for subjective descriptors ('fast', 'user-friendly', 'easy')</span>
                  </div>
                </div>
                <span className="font-code-sm text-code-sm px-2.5 py-0.5 rounded-full bg-tertiary-container/20 text-tertiary font-semibold shrink-0">Passed (2.1s)</span>
              </div>

              <div className="flex items-start justify-between p-3.5 rounded-xl bg-surface-container/60 border border-surface-container-high">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-tertiary-container/30 text-tertiary flex items-center justify-center shrink-0 mt-0.5 font-bold">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div className="flex flex-col">
                    <span className="font-body-md text-body-md font-medium text-on-surface">3. Requirement conflict matrix cross-check</span>
                    <span className="font-code-sm text-code-sm text-outline">Cross-referencing 84 clauses for logical contradiction (REQ-031 ↔ REQ-042)</span>
                  </div>
                </div>
                <span className="font-code-sm text-code-sm px-2.5 py-0.5 rounded-full bg-error-container/20 text-error font-semibold shrink-0">3 Conflicts</span>
              </div>

              <div className="flex items-start justify-between p-3.5 rounded-xl bg-primary-container/10 border border-primary/30">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center shrink-0 mt-0.5 font-bold">
                    <RotateCw className="w-4 h-4 animate-spin text-primary" />
                  </div>
                  <div className="flex flex-col">
                    <span className="font-body-md text-body-md font-semibold text-primary">4. INCOSE testability & SLA verifier</span>
                    <span className="font-code-sm text-code-sm text-on-surface-variant">Synthesizing testable criteria for 18 flagged non-functional statements</span>
                  </div>
                </div>
                <span className="font-code-sm text-code-sm px-2.5 py-0.5 rounded-full bg-primary-container/30 text-primary font-semibold shrink-0 animate-pulse">Running</span>
              </div>
            </div>
          </div>

          {/* Right Column (5 cols): Live Ingestion Stream & Action CTA */}
          <div className="lg:col-span-5 bg-surface-container-low border border-surface-container-high rounded-xl p-6 shadow-md flex flex-col justify-between gap-6">
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h3 className="font-headline-sm text-headline-sm font-semibold text-on-surface">Scan Telemetry Stream</h3>
                <span className="font-code-sm text-code-sm text-tertiary flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse" /> Live Stream
                </span>
              </div>
              <div className="bg-surface-container-lowest border border-surface-container-high rounded-xl p-3.5 font-code-sm text-code-sm flex flex-col gap-2 max-h-52 overflow-y-auto">
                {mockLiveTelemetryLogs.map((log, index) => (
                  <div key={index} className="text-on-surface-variant leading-relaxed">
                    <span className="text-outline mr-2">{index + 1}.</span>
                    <span className={log.includes('CONFLICT') ? 'text-error font-semibold' : log.includes('flagged') ? 'text-amber-300' : ''}>
                      {log}
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
                <span>Inspect REQ-024 Canvas</span>
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
