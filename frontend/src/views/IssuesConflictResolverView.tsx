import React, { useState } from 'react';
import { ActiveTab, IssueItem } from '../types';
import { 
  Bug, 
  AlertTriangle, 
  CheckCircle2, 
  Download, 
  ArrowRight, 
  Sparkles, 
  Check, 
  ShieldAlert, 
  HelpCircle,
  Clock,
  Layers
} from 'lucide-react';
import { mockIssues } from '../data/mockData';

interface IssuesConflictResolverViewProps {
  onNavigate: (tab: ActiveTab) => void;
  selectedIssueId?: string;
}

export const IssuesConflictResolverView: React.FC<IssuesConflictResolverViewProps> = ({
  onNavigate,
  selectedIssueId = 'ISS-001',
}) => {
  const [issues, setIssues] = useState<IssueItem[]>(mockIssues);
  const [activeIssueId, setActiveIssueId] = useState<string>(selectedIssueId);
  const [filterType, setFilterType] = useState<'all' | 'conflicts' | 'ambiguity' | 'acceptance'>('all');
  const [resolvedIssues, setResolvedIssues] = useState<Record<string, boolean>>({});

  const currentIssue = issues.find((i) => i.id === activeIssueId) || issues[0];

  const handleResolveIssue = (issueId: string) => {
    setIssues((prev) =>
      prev.map((i) => (i.id === issueId ? { ...i, status: 'Resolved' } : i))
    );
    setResolvedIssues((prev) => ({ ...prev, [issueId]: true }));
  };

  const filteredIssues = issues.filter((i) => {
    if (filterType === 'conflicts') return i.type.includes('CONFLICT');
    if (filterType === 'ambiguity') return i.type.includes('AMBIGUOUS');
    if (filterType === 'acceptance') return i.type.includes('ACCEPTANCE');
    return true;
  });

  return (
    <div className="flex flex-col w-full min-h-[calc(100vh-3.5rem)] px-4 sm:px-6 py-6 gap-6 animate-in fade-in duration-300">
      {/* Top Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="font-label-caps text-label-caps uppercase text-primary font-bold tracking-wider">Semantic Analysis Engine</span>
            <span className="w-1 h-1 rounded-full bg-outline" />
            <span className="font-code-sm text-code-sm text-tertiary flex items-center gap-1 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-ping" /> Live Scan Synchronized
            </span>
          </div>
          <h1 className="font-headline-lg text-2xl sm:text-3xl text-on-surface tracking-tight font-semibold">Issues & Conflict Resolution</h1>
          <p className="font-body-md text-body-md text-on-surface-variant">
            {issues.length} total issues detected across Smart Hospital Management (SRS v1.3)
          </p>
        </div>

        {/* Severity Metrics Bar & PDF Export */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-error-container/80 text-error border border-error/30 shadow-sm">
            <ShieldAlert className="w-4 h-4" />
            <span className="font-code-md text-code-md font-bold">3</span>
            <span className="font-label-md text-label-md">Critical</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-container-high border border-surface-container-highest text-on-surface-variant shadow-sm">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span className="font-code-md text-code-md font-bold text-on-surface">7</span>
            <span className="font-label-md text-label-md">High</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-container-high border border-surface-container-highest text-on-surface-variant shadow-sm">
            <span className="w-2 h-2 rounded-full bg-secondary" />
            <span className="font-code-md text-code-md font-bold text-on-surface">8</span>
            <span className="font-label-md text-label-md">Medium</span>
          </div>
          <button 
            onClick={() => alert('Generating formal PDF SRS Audit Report for Smart Hospital Management...')}
            className="ml-2 flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-surface-container-highest hover:bg-surface-bright text-on-surface font-label-md text-label-md font-semibold transition-colors shadow-sm border border-surface-container-high"
          >
            <Download className="w-4 h-4" />
            <span>Export Audit (PDF)</span>
          </button>
        </div>
      </div>

      {/* Category Pills */}
      <div className="flex items-center gap-2 p-1.5 bg-surface-container-lowest rounded-xl overflow-x-auto border border-surface-container-high shadow-sm">
        <button
          onClick={() => setFilterType('all')}
          className={`px-3.5 py-1.5 rounded-lg font-label-md text-label-md transition-all flex items-center gap-2 ${filterType === 'all' ? 'bg-surface-container text-on-surface font-semibold shadow-sm' : 'text-on-surface-variant hover:text-on-surface'}`}
        >
          <span>All Issues</span>
          <span className="font-code-sm text-code-sm px-1.5 py-0.2 rounded-full bg-surface-container-highest text-on-surface-variant">{issues.length}</span>
        </button>
        <button
          onClick={() => setFilterType('conflicts')}
          className={`px-3.5 py-1.5 rounded-lg font-label-md text-label-md transition-all flex items-center gap-2 ${filterType === 'conflicts' ? 'bg-error-container/30 text-error font-semibold shadow-sm' : 'text-on-surface-variant hover:text-on-surface'}`}
        >
          <span>Requirement Conflicts</span>
          <span className="font-code-sm text-code-sm px-1.5 py-0.2 rounded-full bg-error-container text-error">3</span>
        </button>
        <button
          onClick={() => setFilterType('ambiguity')}
          className={`px-3.5 py-1.5 rounded-lg font-label-md text-label-md transition-all flex items-center gap-2 ${filterType === 'ambiguity' ? 'bg-surface-container text-on-surface font-semibold shadow-sm' : 'text-on-surface-variant hover:text-on-surface'}`}
        >
          <span>Ambiguity</span>
          <span className="font-code-sm text-code-sm px-1.5 py-0.2 rounded-full bg-surface-container-high text-on-surface-variant">7</span>
        </button>
        <button
          onClick={() => setFilterType('acceptance')}
          className={`px-3.5 py-1.5 rounded-lg font-label-md text-label-md transition-all flex items-center gap-2 ${filterType === 'acceptance' ? 'bg-surface-container text-on-surface font-semibold shadow-sm' : 'text-on-surface-variant hover:text-on-surface'}`}
        >
          <span>Missing Acceptance</span>
          <span className="font-code-sm text-code-sm px-1.5 py-0.2 rounded-full bg-surface-container-high text-on-surface-variant">5</span>
        </button>
      </div>

      {/* Main Grid Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Navigator Panel (4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-3">
          <div className="flex items-center justify-between px-1">
            <span className="font-label-caps text-label-caps uppercase text-outline">Issue Navigator ({filteredIssues.length})</span>
            <span className="font-code-sm text-code-sm text-outline">Sorted by Severity</span>
          </div>

          <div className="flex flex-col gap-2.5">
            {filteredIssues.map((issue) => {
              const isSelected = issue.id === activeIssueId;
              const isResolved = issue.status === 'Resolved';
              return (
                <div
                  key={issue.id}
                  onClick={() => setActiveIssueId(issue.id)}
                  className={`
                    p-4 rounded-xl cursor-pointer transition-all border relative
                    ${isSelected 
                      ? 'bg-surface-container-high border-primary text-on-surface shadow-md' 
                      : 'bg-surface-container border-surface-container-high hover:bg-surface-container-high text-on-surface-variant'
                    }
                  `}
                >
                  {isSelected && <div className="absolute left-0 top-3 bottom-3 w-1 bg-primary rounded-r" />}

                  <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <span className={`font-code-sm text-code-sm px-2 py-0.5 rounded font-semibold flex items-center gap-1 ${issue.severity === 'critical' ? 'bg-error-container text-error' : 'bg-surface-container-highest text-amber-300'}`}>
                        <ShieldAlert className="w-3 h-3" /> {issue.type}
                      </span>
                      <span className="font-code-sm text-code-sm text-outline">{issue.section}</span>
                    </div>

                    <div className="flex items-center justify-between gap-2 mt-0.5">
                      <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold tracking-tight">{issue.title}</h3>
                      <ArrowRight className={`w-4 h-4 ${isSelected ? 'text-primary' : 'text-outline'}`} />
                    </div>

                    <p className="font-body-sm text-body-sm text-on-surface-variant line-clamp-2">{issue.summary}</p>

                    <div className="flex items-center justify-between pt-1 border-t border-surface-container-high/40">
                      <span className="font-code-sm text-code-sm text-outline">{issue.section}</span>
                      <span className={`font-label-caps text-label-caps uppercase font-bold ${isResolved ? 'text-tertiary' : 'text-primary'}`}>
                        {issue.status}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Conflict Resolution Canvas (8 cols) */}
        <div className="lg:col-span-8 bg-surface-container-low border border-surface-container-high rounded-2xl p-6 shadow-md flex flex-col gap-6">
          {/* Header of Active Issue */}
          <div className="flex flex-col gap-2 border-b border-surface-container-high pb-4">
            <div className="flex items-center justify-between">
              <span className="font-code-sm text-code-sm px-2.5 py-1 rounded bg-error-container/30 border border-error/40 text-error font-bold uppercase flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" /> {currentIssue.type}
              </span>
              <span className="font-code-sm text-code-sm text-outline">{currentIssue.section}</span>
            </div>

            <h2 className="font-headline-lg text-2xl text-on-surface font-semibold mt-1">{currentIssue.title}</h2>
            <p className="font-body-md text-body-md text-on-surface-variant">{currentIssue.summary}</p>
          </div>

          {/* Side-by-Side Contradictory Requirements Inspector */}
          {currentIssue.details ? (
            <div className="flex flex-col gap-4">
              <span className="font-label-caps text-label-caps uppercase text-outline">Side-by-Side Clause Comparison</span>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Requirement A */}
                <div className="p-4 rounded-xl bg-surface-container-lowest border border-error/40 flex flex-col gap-2 relative">
                  <div className="flex items-center justify-between border-b border-surface-container-high pb-2">
                    <span className="font-code-md text-code-md font-bold text-error px-2 py-0.5 rounded bg-error-container/30">
                      {currentIssue.details.reqA.id}
                    </span>
                    <span className="font-code-sm text-code-sm text-outline">{currentIssue.details.reqA.section}</span>
                  </div>
                  <p className="font-body-md text-body-md text-on-surface mt-1 leading-relaxed">
                    "{currentIssue.details.reqA.text}"
                  </p>
                </div>

                {/* Requirement B */}
                {currentIssue.details.reqB && (
                  <div className="p-4 rounded-xl bg-surface-container-lowest border border-error/40 flex flex-col gap-2 relative">
                    <div className="flex items-center justify-between border-b border-surface-container-high pb-2">
                      <span className="font-code-md text-code-md font-bold text-error px-2 py-0.5 rounded bg-error-container/30">
                        {currentIssue.details.reqB.id}
                      </span>
                      <span className="font-code-sm text-code-sm text-outline">{currentIssue.details.reqB.section}</span>
                    </div>
                    <p className="font-body-md text-body-md text-on-surface mt-1 leading-relaxed">
                      "{currentIssue.details.reqB.text}"
                    </p>
                  </div>
                )}
              </div>

              {/* Root Cause Analysis */}
              <div className="p-4 rounded-xl bg-surface-container border border-surface-container-high flex flex-col gap-1.5">
                <span className="font-label-caps text-label-caps uppercase text-amber-300 font-semibold">Root Cause Diagnostics</span>
                <p className="font-body-sm text-body-sm text-on-surface">{currentIssue.details.rootCause}</p>
              </div>

              {/* AI Recommended Harmonization Solution */}
              <div className="p-5 rounded-xl bg-primary-container/10 border border-primary/30 flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-primary font-semibold font-label-md text-label-md">
                    <Sparkles className="w-4 h-4" />
                    <span>SpecSentinel AI Harmonization Strategy</span>
                  </div>
                  <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-tertiary-container/20 text-tertiary font-semibold">
                    Role-Based Partitioning
                  </span>
                </div>

                <p className="font-body-md text-body-md text-on-surface font-medium leading-relaxed bg-surface-container-lowest/90 p-3.5 rounded-lg border border-surface-container-high">
                  {currentIssue.details.recommendedResolution}
                </p>

                <div className="flex items-center justify-end pt-2">
                  <button
                    onClick={() => handleResolveIssue(currentIssue.id)}
                    disabled={resolvedIssues[currentIssue.id]}
                    className={`
                      px-5 py-2 rounded-lg font-label-md text-label-md font-semibold flex items-center gap-2 transition-all shadow-md
                      ${resolvedIssues[currentIssue.id]
                        ? 'bg-tertiary-container/30 text-tertiary cursor-default'
                        : 'bg-primary text-on-primary hover:opacity-90 active:scale-95'
                      }
                    `}
                  >
                    <Check className="w-4 h-4" />
                    <span>{resolvedIssues[currentIssue.id] ? 'Harmonized & Resolved' : 'Apply Harmonized Resolution'}</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-xl bg-surface-container border border-surface-container-high text-center flex flex-col items-center justify-center gap-3">
              <Bug className="w-10 h-10 text-outline" />
              <p className="font-body-lg text-body-lg text-on-surface font-medium">Select an issue from the left navigator to inspect details.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
