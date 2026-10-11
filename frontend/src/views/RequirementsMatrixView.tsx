import React, { useEffect, useMemo, useState } from 'react';
import { ActiveTab, RequirementItem } from '../types';
import {
  Search,
  Filter,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Check,
  SlidersHorizontal,
  GitFork,
  Plus,
  Edit3,
  Copy,
  RefreshCw,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { api, RecommendationData, RequirementData } from '../api/client';
import { useActiveProject, useAsync, toRequirementItem } from '../api/hooks';

interface RequirementsMatrixViewProps {
  onNavigate: (tab: ActiveTab) => void;
  selectedReqId?: string;
  onSelectReq: (id: string) => void;
}

export const RequirementsMatrixView: React.FC<RequirementsMatrixViewProps> = ({
  onNavigate,
  selectedReqId,
  onSelectReq,
}) => {
  const { active, activeId } = useActiveProject();
  const reqsApi = useAsync(
    () => (activeId
      ? api.getRequirements({ project_id: activeId, page_size: 200 })
      : Promise.resolve([])),
    [activeId],
  );

  const [rawReqs, setRawReqs] = useState<RequirementData[]>([]);
  const [activeReqId, setActiveReqId] = useState<string | undefined>(selectedReqId);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'functional' | 'non-functional'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'review' | 'verified'>('all');
  const [appliedFixes, setAppliedFixes] = useState<Record<string, boolean>>({});
  const [customCriteriaInput, setCustomCriteriaInput] = useState('');
  const [rec, setRec] = useState<RecommendationData | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const mapped = reqsApi.data || [];
    setRawReqs(mapped);
    if (mapped.length > 0 && (!activeReqId || !mapped.some((r) => r.req_id_str === activeReqId))) {
      setActiveReqId(mapped[0].req_id_str);
      onSelectReq(mapped[0].req_id_str);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reqsApi.data]);

  const reqs = useMemo(() => rawReqs.map(toRequirementItem), [rawReqs]);
  const currentRaw = rawReqs.find((r) => r.req_id_str === activeReqId) || rawReqs[0];

  // pending AI rewrite for the selected requirement
  useEffect(() => {
    setRec(null);
    if (!currentRaw) return;
    api.getRecommendationsForReq(currentRaw.id)
      .then((list) => {
        const pending = list.find(
          (r) => r.status === 'pending' || r.status === 'needs_human_input');
        if (pending) setRec(pending);
      })
      .catch(() => undefined);
  }, [currentRaw?.id]);

  const currentReq = currentRaw
    ? {
        ...toRequirementItem(currentRaw),
        suggestedRewrite: rec?.proposed_text || undefined,
      }
    : (undefined as unknown as RequirementItem);

  // acceptance criteria derived from extracted normalized constraints
  const acceptanceCriteria: string[] = currentRaw
    ? (currentRaw.constraints_json || []).map((c: any) =>
        `${c.attribute} ${c.operator} ${Array.isArray(c.value) ? c.value.join(' – ') : c.value}${c.unit ? ' ' + c.unit : ''}`)
    : [];
  const missingInfo: string[] = currentRaw?.missing_information_json || [];

  const handleApplyFix = async (reqId: string) => {
    if (!rec?.proposed_text) return;
    setBusy(true);
    try {
      await api.acceptRecommendation(rec.id);
      setAppliedFixes((prev) => ({ ...prev, [reqId]: true }));
      setRec(null);
      await reqsApi.reload();
    } catch (err) {
      alert(`Apply failed: ${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleAddCriteria = () => {
    // local-only note: acceptance criteria editing lands in a future
    // milestone (criteria are derived from extracted constraints today)
    setCustomCriteriaInput('');
  };

  const filteredReqs = reqs.filter((r) => {
    const matchesSearch =
      r.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.originalText.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || r.type === filterType;
    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'review' && r.status !== 'Verified') ||
      (statusFilter === 'verified' && r.status === 'Verified');
    return matchesSearch && matchesType && matchesStatus;
  });

  if (reqsApi.loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] gap-3 text-on-surface-variant">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
        <span className="font-body-md text-body-md">Loading requirements…</span>
      </div>
    );
  }
  if (reqsApi.error) {
    return (
      <div className="m-6 p-5 rounded-xl bg-error-container/20 border border-error/40 flex flex-col gap-2">
        <div className="flex items-center gap-2 text-error font-semibold"><AlertCircle className="w-5 h-5" /> {reqsApi.error}</div>
        <button onClick={reqsApi.reload} className="mt-2 self-start h-8 px-3 rounded-lg bg-primary-container text-on-primary-container font-label-md text-label-md">Retry</button>
      </div>
    );
  }
  if (!currentReq || !currentRaw) {
    return (
      <div className="px-6 py-10 max-w-7xl mx-auto w-full flex flex-col gap-3 items-center text-center">
        <AlertCircle className="w-8 h-8 text-outline" />
        <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">No requirements yet</h2>
        <p className="font-body-md text-body-md text-on-surface-variant">
          {active ? `“${active.name}” has not been analyzed. Run an analysis to extract requirements.`
                  : 'Create a project and upload an SRS document to get started.'}
        </p>
        {activeId && (
          <button
            onClick={() => api.analyzeProject(activeId)
              .then(() => onNavigate('srs-progress'))
              .catch((err) => alert(err.message))}
            className="mt-2 h-9 px-4 rounded-lg bg-primary text-on-primary font-label-md text-label-md font-semibold"
          >
            Run Analysis
          </button>
        )}
      </div>
    );
  }


  return (
    <div className="flex flex-col w-full min-h-[calc(100vh-3.5rem)] animate-in fade-in duration-300">
      {/* Top Banner Control Bar */}
      <div className="px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-surface-container-lowest border-b border-surface-container-high">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-primary-container animate-pulse" />
            <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight font-semibold">Requirements Matrix</h1>
          </div>
          <span className="px-2.5 py-0.5 rounded bg-surface-container text-outline font-code-sm text-code-sm">
            {reqs.length} TOTAL ENROLLED
          </span>
          <span className="px-2.5 py-0.5 rounded bg-surface-container-high text-primary font-code-sm text-code-sm flex items-center gap-1.5 border border-primary/20">
            <Sparkles className="w-3.5 h-3.5 text-primary" /> SpecSentinel AI Sync
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center bg-surface-container-low px-3 py-1.5 rounded-lg border border-surface-container-high gap-2">
            <SlidersHorizontal className="w-4 h-4 text-outline" />
            <span className="font-label-md text-label-md text-on-surface-variant">Lint Mode: Strict INCOSE</span>
          </div>
          <button
            onClick={() => {
              if (!activeId) return;
              api.analyzeProject(activeId)
                .then(() => onNavigate('srs-progress'))
                .catch((err) => alert(err.message));
            }}
            className="bg-primary text-on-primary font-label-md text-label-md px-3.5 py-1.5 rounded-lg flex items-center gap-2 hover:opacity-90 transition-opacity shadow-sm font-semibold"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Re-analyze Spec</span>
          </button>
        </div>
      </div>

      {/* Split Workspace Layout */}
      <div className="flex flex-col xl:flex-row w-full gap-6 p-6 flex-1">
        {/* LEFT PANEL: Table & Filters (54%) */}
        <div className="flex flex-col xl:w-[54%] w-full bg-surface-container-low border border-surface-container-high rounded-2xl shadow-md p-4">
          {/* Filter Toolbar */}
          <div className="flex flex-col gap-3 pb-3 border-b border-surface-container-high">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="relative flex-1 w-full">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-outline" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search requirements, RFC keywords, or IDs (e.g. REQ-024)..."
                  className="w-full bg-surface-container-lowest border border-surface-container-high text-on-surface placeholder-outline font-body-sm text-body-sm pl-9 pr-4 py-2 rounded-lg focus:outline-none focus:border-primary"
                />
              </div>

              <div className="flex items-center gap-1 bg-surface-container p-1 rounded-lg border border-surface-container-high w-full sm:w-auto">
                <button
                  onClick={() => setStatusFilter('all')}
                  className={`px-2.5 py-1 rounded-md text-label-md font-label-md transition-all ${statusFilter === 'all' ? 'bg-surface-container-highest text-on-surface font-semibold shadow-sm' : 'text-on-surface-variant hover:text-on-surface'}`}
                >
                  All <span className="font-code-sm text-code-sm text-outline">{reqs.length}</span>
                </button>
                <button
                  onClick={() => setStatusFilter('review')}
                  className={`px-2.5 py-1 rounded-md text-label-md font-label-md transition-all ${statusFilter === 'review' ? 'bg-error-container/40 text-error font-semibold shadow-sm' : 'text-on-surface-variant hover:text-on-surface'}`}
                >
                  Needs Review <span className="px-1.5 rounded bg-error-container text-error font-code-sm text-[10px]">
                    {reqs.filter((r) => r.status !== 'Verified').length}
                  </span>
                </button>
                <button
                  onClick={() => setStatusFilter('verified')}
                  className={`px-2.5 py-1 rounded-md text-label-md font-label-md transition-all ${statusFilter === 'verified' ? 'bg-tertiary-container/20 text-tertiary font-semibold shadow-sm' : 'text-on-surface-variant hover:text-on-surface'}`}
                >
                  Verified <span className="font-code-sm text-code-sm text-tertiary">
                    {reqs.filter((r) => r.status === 'Verified').length}
                  </span>
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-outline px-1">
              <div className="flex items-center gap-2">
                <span className="font-label-caps text-label-caps uppercase text-outline">Filter Class:</span>
                <button
                  onClick={() => setFilterType(filterType === 'functional' ? 'all' : 'functional')}
                  className={`px-2 py-0.5 rounded font-code-sm text-code-sm transition-colors ${filterType === 'functional' ? 'bg-primary text-on-primary font-semibold' : 'bg-surface-container text-primary hover:bg-surface-container-high'}`}
                >
                  Functional ({reqs.filter((r) => r.type === 'functional').length})
                </button>
                <button
                  onClick={() => setFilterType(filterType === 'non-functional' ? 'all' : 'non-functional')}
                  className={`px-2 py-0.5 rounded font-code-sm text-code-sm transition-colors ${filterType === 'non-functional' ? 'bg-primary text-on-primary font-semibold' : 'bg-surface-container text-on-surface hover:bg-surface-container-high'}`}
                >
                  Non-Functional ({reqs.filter((r) => r.type === 'non-functional').length})
                </button>
              </div>
              <span className="font-code-sm text-code-sm text-outline hidden sm:inline">Sorted by Ambiguity Score ↓</span>
            </div>
          </div>

          {/* Feed List */}
          <div className="flex flex-col gap-2 mt-3 overflow-y-auto max-h-[calc(100vh-18rem)] pr-1">
            {filteredReqs.map((req) => {
              const isSelected = req.id === activeReqId;
              const isClean = req.status === 'Verified';
              return (
                <div
                  key={req.id}
                  onClick={() => {
                    setActiveReqId(req.id);
                    onSelectReq(req.id);
                  }}
                  className={`
                    p-3.5 rounded-xl cursor-pointer transition-all relative overflow-hidden border
                    ${isSelected 
                      ? 'bg-surface-container-highest border-primary shadow-md' 
                      : 'bg-surface-container border-surface-container-high hover:bg-surface-container-high hover:border-outline'
                    }
                  `}
                >
                  {isSelected && <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-primary" />}

                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className={`font-code-md text-code-md font-bold px-2 py-0.5 rounded ${isSelected ? 'bg-primary/20 text-primary' : 'bg-surface-container-lowest text-on-surface'}`}>
                        {req.id}
                      </span>
                      <span className="font-label-caps text-label-caps uppercase px-2 py-0.5 rounded bg-surface-container-low text-outline">
                        {req.category}
                      </span>
                      {req.issues.length > 0 && (
                        <span className="flex items-center gap-1 font-label-caps text-label-caps px-2 py-0.5 rounded bg-error-container text-error font-semibold">
                          <AlertTriangle className="w-3 h-3" /> {req.issues.length} ISSUES
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="flex flex-col items-end">
                        <span className="font-label-caps text-label-caps text-outline uppercase">Clarity Index</span>
                        <span className={`font-code-md text-code-md font-bold ${req.ambiguityScore < 60 ? 'text-error' : 'text-tertiary'}`}>
                          {req.ambiguityScore} <span className="text-outline text-code-sm">/ 100</span>
                        </span>
                      </div>
                      <span className={`px-2 py-0.5 rounded font-label-md text-label-md font-medium ${isClean ? 'bg-tertiary-container/20 text-tertiary' : 'bg-surface-container text-primary'}`}>
                        {req.status}
                      </span>
                    </div>
                  </div>

                  <p className="font-body-md text-body-md text-on-surface mt-2.5 font-medium line-clamp-2">
                    "{req.originalText}"
                  </p>

                  <div className="mt-3 flex items-center justify-between text-outline text-code-sm">
                    <div className="flex items-center gap-3">
                      {req.issues[0] && (
                        <span className="flex items-center gap-1 text-error font-medium">
                          <span className="w-1.5 h-1.5 rounded-full bg-error" /> {req.issues[0].type}
                        </span>
                      )}
                      <span className="text-outline">{req.section}</span>
                    </div>
                    {isSelected && (
                      <span className="font-code-sm text-code-sm text-primary flex items-center gap-1 font-semibold">
                        Selected Canvas <ArrowRight className="w-3.5 h-3.5" />
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* RIGHT PANEL: INSPECTION CANVAS (46%) */}
        <div className="flex flex-col xl:w-[46%] w-full bg-surface-container-low border border-surface-container-high rounded-2xl shadow-md p-6 gap-6">
          {/* Header of Canvas */}
          <div className="flex flex-col gap-2 border-b border-surface-container-high pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-code-md text-code-md font-bold px-2.5 py-1 rounded bg-primary-container/20 text-primary border border-primary/30">
                  {currentReq.id} Inspection
                </span>
                <span className="font-code-sm text-code-sm text-outline">{currentReq.section}</span>
              </div>
              <span className="font-label-caps text-label-caps text-outline uppercase">{currentReq.author} • {currentReq.lastUpdated}</span>
            </div>

            <h2 className="font-headline-md text-headline-md font-semibold text-on-surface mt-1">{currentReq.title}</h2>

            {/* Ambiguity Heatmap Bar */}
            <div className="flex flex-col gap-1 mt-2">
              <div className="flex items-center justify-between text-code-sm font-code-sm">
                <span className="text-outline">Semantic Quality Index</span>
                <span className={`font-bold ${currentReq.ambiguityScore < 60 ? 'text-error' : 'text-tertiary'}`}>
                  {currentReq.ambiguityScore}/100 ({currentReq.ambiguityScore >= 80 ? 'Crisp Specification' : 'Ambiguous Clauses Detected'})
                </span>
              </div>
              <div className="w-full bg-surface-container h-2 rounded-full overflow-hidden flex">
                <div className={`h-full ${currentReq.ambiguityScore < 60 ? 'bg-error' : 'bg-tertiary'} rounded-full transition-all duration-500`} style={{ width: `${currentReq.ambiguityScore}%` }} />
              </div>
            </div>
          </div>

          {/* Original Statement Box */}
          <div className="flex flex-col gap-2">
            <span className="font-label-caps text-label-caps uppercase text-outline">Current Requirement Clause</span>
            <div className="p-4 rounded-xl bg-surface-container-lowest border border-surface-container-high text-on-surface font-body-lg text-body-lg leading-relaxed relative">
              "{currentReq.originalText}"
            </div>
          </div>

          {/* Detected Lint Issues */}
          {currentReq.issues.length > 0 && (
            <div className="flex flex-col gap-2">
              <span className="font-label-caps text-label-caps uppercase text-error font-semibold flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> Syntactic & Semantic Rule Violations ({currentReq.issues.length})
              </span>
              <div className="flex flex-col gap-2">
                {currentReq.issues.map((iss) => (
                  <div key={iss.id} className="p-3 rounded-xl bg-error-container/20 border border-error/30 flex items-start justify-between">
                    <div className="flex flex-col">
                      <span className="font-code-sm text-code-sm font-bold text-error">{iss.type}</span>
                      <span className="font-body-sm text-body-sm text-on-surface mt-0.5">{iss.description}</span>
                    </div>
                    <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-error-container text-error font-semibold uppercase">{iss.severity}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SpecSentinel AI Testable Rewrite Callout */}
          {currentReq.suggestedRewrite && (
            <div className="flex flex-col gap-3 p-4 rounded-xl bg-primary-container/10 border border-primary/30 relative">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-primary font-semibold font-label-md text-label-md">
                  <Sparkles className="w-4 h-4 text-primary" />
                  <span>SpecSentinel AI Testable Rewrite Suggestion</span>
                </div>
                <span className="font-code-sm text-code-sm px-2 py-0.5 rounded bg-tertiary-container/20 text-tertiary font-semibold">
                  {rec ? `${rec.predicted_score_delta >= 0 ? '+' : ''}${rec.predicted_score_delta} score delta (recomputed)` : 'recomputed delta'}
                </span>
              </div>

              <p className="font-body-md text-body-md text-on-surface font-medium leading-relaxed bg-surface-container-lowest/80 p-3 rounded-lg border border-surface-container-high">
                "{currentReq.suggestedRewrite}"
              </p>

              <div className="flex items-center justify-between pt-1">
                <span className="font-code-sm text-code-sm text-outline">
                  {missingInfo.length > 0
                    ? `Missing: ${missingInfo.join(', ')}`
                    : 'All required fields present'}
                </span>
                <button
                  onClick={() => handleApplyFix(currentReq.id)}
                  disabled={busy || appliedFixes[currentReq.id]}
                  className={`
                    px-4 py-1.5 rounded-lg text-label-md font-semibold flex items-center gap-2 transition-all shadow-sm
                    ${appliedFixes[currentReq.id]
                      ? 'bg-tertiary-container/30 text-tertiary cursor-default'
                      : 'bg-primary text-on-primary hover:opacity-90 active:scale-95'}
                    ${busy ? 'opacity-60 cursor-wait' : ''}
                  `}
                >
                  <Check className="w-4 h-4" />
                  <span>
                    {appliedFixes[currentReq.id] ? 'Fix Applied'
                      : busy ? 'Applying…' : 'Apply Fix (Tab)'}
                  </span>
                </button>
              </div>
            </div>
          )}

          {/* Acceptance Criteria Builder */}
          <div className="flex flex-col gap-3 pt-2 border-t border-surface-container-high">
            <span className="font-label-caps text-label-caps uppercase text-outline">Verifiable Acceptance Criteria</span>
            <div className="flex flex-col gap-2">
              {acceptanceCriteria.length === 0 && missingInfo.length === 0 && (
                <span className="font-body-sm text-body-sm text-outline">
                  No extracted constraints — add criteria below or re-run analysis.
                </span>
              )}
              {acceptanceCriteria.map((crit, idx) => (
                <div key={idx} className="flex items-center gap-2.5 font-body-sm text-body-sm text-on-surface bg-surface-container p-2.5 rounded-lg border border-surface-container-high">
                  <CheckCircle2 className="w-4 h-4 text-tertiary shrink-0" />
                  <span>{crit}</span>
                </div>
              ))}
              {missingInfo.map((crit, idx) => (
                <div key={`m-${idx}`} className="flex items-center gap-2.5 font-body-sm text-body-sm text-amber-300 bg-error-container/10 p-2.5 rounded-lg border border-amber-400/30">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>Missing: {crit}</span>
                </div>
              ))}
            </div>

            {/* Add Custom Criterion Input */}
            <div className="flex items-center gap-2 mt-1">
              <input
                type="text"
                value={customCriteriaInput}
                onChange={(e) => setCustomCriteriaInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddCriteria()}
                placeholder="Add testable acceptance criteria (e.g. Render latency <= 200ms)..."
                className="flex-1 bg-surface-container-lowest border border-surface-container-high text-on-surface font-body-sm text-body-sm px-3 py-1.5 rounded-lg focus:outline-none focus:border-primary"
              />
              <button
                onClick={handleAddCriteria}
                className="px-3 py-1.5 rounded-lg bg-surface-container-high text-on-surface hover:bg-surface-bright font-label-md text-label-md font-semibold transition-colors"
              >
                Add
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
