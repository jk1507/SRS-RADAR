import React from 'react';
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
  ChevronRight
} from 'lucide-react';
import { mockProjects, mockLiveTelemetryLogs } from '../data/mockData';

interface DashboardViewProps {
  onNavigate: (tab: ActiveTab) => void;
  onOpenUpload: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate, onOpenUpload }) => {
  return (
    <div className="px-4 sm:px-6 py-6 max-w-7xl mx-auto w-full flex flex-col gap-8 animate-in fade-in duration-300">
      {/* Executive Greeting & Action Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-2 border-b border-surface-container-high/40">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="font-label-caps text-label-caps uppercase text-primary tracking-widest bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-md">
              SRS Verification Node
            </span>
            <span className="font-code-sm text-code-sm text-outline">Cluster US-East-1</span>
          </div>
          <h1 className="font-display text-2xl sm:text-3xl text-on-surface font-semibold tracking-tight mt-1">
            Good morning, Jack.
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
              <span className="font-display text-3xl text-on-surface font-semibold">3</span>
              <span className="font-label-md text-label-md text-on-surface-variant">Projects Enrolled</span>
            </div>
            <div className="mt-2 flex items-center gap-1.5 font-code-sm text-code-sm text-secondary-fixed">
              <span className="w-2 h-2 rounded-full bg-secondary animate-ping" />
              <span>1 pending live analysis</span>
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
              <span className="font-display text-3xl text-tertiary font-semibold">83.3</span>
              <span className="font-code-md text-code-md text-outline">/ 100</span>
            </div>
            <div className="mt-2 flex items-center gap-1 text-tertiary font-code-sm text-code-sm">
              <TrendingUp className="w-3.5 h-3.5" />
              <span className="font-semibold">+5.4%</span>
              <span className="text-on-surface-variant font-body-sm text-body-sm">vs last month</span>
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
              <span className="font-display text-3xl text-error font-semibold">18</span>
              <span className="font-label-md text-label-md text-on-surface-variant">Detected</span>
            </div>
            <div className="mt-2 flex items-center gap-2 font-code-sm text-code-sm">
              <span className="text-error bg-error-container/40 border border-error/30 px-1.5 py-0.5 rounded font-semibold">3 Crit</span>
              <span className="text-on-surface-variant bg-surface-container px-1.5 py-0.5 rounded">7 High</span>
              <span className="text-outline bg-surface-container px-1.5 py-0.5 rounded">8 Med</span>
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
              <span className="font-display text-3xl text-on-surface font-semibold">248</span>
              <span className="font-label-md text-label-md text-on-surface-variant">Statements</span>
            </div>
            <div className="mt-2 flex items-center gap-1.5 font-code-sm text-code-sm text-on-surface-variant">
              <Layers className="w-3.5 h-3.5 text-outline" />
              <span>Across 3 target domains</span>
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
            {mockProjects.map((proj) => (
              <div 
                key={proj.id}
                onClick={() => onNavigate(proj.id === 'proj-01' ? 'srs-progress' : 'requirements')}
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
                    </div>
                    <span className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">{proj.fileName} • {proj.domain}</span>
                  </div>
                </div>

                <div className="flex items-center gap-4 shrink-0 justify-between sm:justify-end border-t sm:border-t-0 pt-2 sm:pt-0 border-surface-container-high">
                  <div className="flex flex-col items-end">
                    <span className="font-label-caps text-label-caps text-outline uppercase">Quality Index</span>
                    <span className="font-code-md text-code-md font-bold text-tertiary">{proj.qualityScore}/100</span>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="font-label-caps text-label-caps text-outline uppercase">Issues</span>
                    <span className="font-code-md text-code-md font-bold text-error">{proj.openIssuesCount}</span>
                  </div>
                  <ArrowRight className="w-5 h-5 text-outline group-hover:text-primary group-hover:translate-x-1 transition-all" />
                </div>
              </div>
            ))}
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

          <div className="bg-surface-container-lowest border border-surface-container-high rounded-xl p-4 flex flex-col gap-2.5 font-code-sm text-code-sm overflow-hidden min-h-[260px]">
            {mockLiveTelemetryLogs.map((log, idx) => (
              <div key={idx} className="flex items-start gap-2 text-on-surface-variant leading-relaxed">
                <span className="text-outline shrink-0">[{new Date().toLocaleTimeString()}]</span>
                <span className={`
                  ${log.includes('CRITICAL') || log.includes('CONFLICT') ? 'text-error font-semibold' : ''}
                  ${log.includes('WARN') || log.includes('flagged') ? 'text-amber-300' : ''}
                  ${log.includes('DISCOVERY') || log.includes('AI') ? 'text-primary' : ''}
                  ${log.includes('verified') || log.includes('compliant') ? 'text-tertiary' : ''}
                `}>
                  {log}
                </span>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between text-outline font-code-sm text-code-sm pt-1">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-outline" /> Next sweep in 4m 12s
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
