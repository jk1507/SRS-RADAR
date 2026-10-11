import { useCallback, useEffect, useRef, useState } from 'react';
import {
  api, ensureAuth, IssueData, ProjectData, RequirementData, StreamEvent,
} from './client';
import { IssueItem, ProjectItem, RequirementItem } from '../types';

/** Fetch-on-mount hook with loading / error / reload states (PRD 9). */
export function useAsync<T>(fn: () => Promise<T>, deps: any[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const seq = useRef(0);

  const reload = useCallback(() => {
    const id = ++seq.current;
    setLoading(true);
    setError(null);
    ensureAuth()
      .then(fn)
      .then((res) => {
        if (seq.current === id) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (seq.current === id) {
          setError(err.message || 'Request failed');
          setLoading(false);
        }
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    reload();
  }, [reload]);

  return { data, loading, error, reload };
}

/** Active project resolution: URL-less app state shared via localStorage. */
const ACTIVE_PROJECT_KEY = 'rr_active_project_id';

export function getActiveProjectId(): string | null {
  return localStorage.getItem(ACTIVE_PROJECT_KEY);
}

export function setActiveProjectId(id: string) {
  localStorage.setItem(ACTIVE_PROJECT_KEY, id);
}

/** Loads projects and resolves the active one (first by default). */
export function useActiveProject() {
  const { data: projects, loading, error, reload } = useAsync(() => api.getProjects(), []);
  const [activeId, setActiveId] = useState<string | null>(getActiveProjectId());

  useEffect(() => {
    if (!projects || projects.length === 0) return;
    const exists = activeId && projects.some((p) => p.id === activeId);
    const next = exists ? activeId : projects[0].id;
    if (next !== activeId) {
      setActiveId(next);
      setActiveProjectId(next);
    }
  }, [projects, activeId]);

  const active = projects?.find((p) => p.id === activeId) || null;

  return {
    projects: projects || [],
    active,
    activeId: active?.id || null,
    setActive: (id: string) => {
      setActiveId(id);
      setActiveProjectId(id);
    },
    loading,
    error,
    reload,
  };
}

// ----------------------------------------------------------------- adapters
function relativeTime(iso?: string | null): string {
  if (!iso) return 'never';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return 'never';
  const diff = Math.max(0, Date.now() - then) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)} mins ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
  return `${Math.floor(diff / 86400)} days ago`;
}

export function toProjectItem(p: ProjectData, openIssues?: number): ProjectItem {
  return {
    id: p.id,
    name: p.name,
    fileName: p.document_filename || 'No document uploaded',
    version: p.version,
    requirementsCount: p.parsed_requirements_count,
    qualityScore: p.quality_score,
    openIssuesCount: openIssues ?? p.open_ambiguities_count,
    status: p.status === 'analyzing' ? 'Analyzing'
      : p.status === 'analyzed' ? 'Completed' : 'Draft',
    lastScan: relativeTime(p.last_analyzed_at),
    domain: p.domain,
  };
}

const SEVERITY_MAP: Record<string, 'critical' | 'high' | 'medium'> = {
  critical: 'critical', high: 'high', medium: 'medium', low: 'medium',
};

export function toRequirementItem(r: RequirementData): RequirementItem {
  const conflicts = (r.rule_violations || []).filter((v) => v.rule_id === 'RQ-CONS-001');
  const status: RequirementItem['status'] =
    conflicts.length > 0 ? 'Conflict'
      : r.status === 'verified' ? 'Verified' : 'Needs Review';
  return {
    id: r.req_id_str,
    title: r.source_heading || r.category,
    category: r.category,
    type: r.type.toLowerCase().includes('non') ? 'non-functional' : 'functional',
    status,
    ambiguityScore: Math.round(r.clarity_score),
    originalText: r.clause_text,
    issues: (r.rule_violations || []).map((v) => ({
      id: `${r.req_id_str}-${v.rule_id}`,
      type: v.type,
      description: v.description,
      severity: SEVERITY_MAP[v.severity.toLowerCase()] || 'medium',
    })),
    section: r.source_section
      ? `Section ${r.source_section}${r.source_page ? ` · p.${r.source_page}` : ''}`
      : '—',
    author: 'Extracted from SRS',
    lastUpdated: relativeTime(r.updated_at),
  };
}

export function toIssueItem(i: IssueData): IssueItem {
  const sev = SEVERITY_MAP[i.severity.toLowerCase()] || 'medium';
  const typeLabel =
    i.issue_type === 'conflict' ? 'REQUIREMENT CONFLICT'
      : i.issue_type === 'ambiguity' ? 'AMBIGUOUS WORDING'
        : i.issue_type === 'missing_acceptance' ? 'MISSING ACCEPTANCE'
          : i.issue_type === 'traceability_gap' ? 'TRACEABILITY GAP'
            : i.issue_type === 'scope_note' ? 'SCOPE MISMATCH'
              : i.category.toUpperCase();
  const evidence = i.evidence_json || {};
  const reqA = evidence.req_a || {};
  const reqB = evidence.req_b || {};
  return {
    id: i.id,
    reqIds: i.affected_req_ids || [],
    type: `${sev.toUpperCase()} · ${typeLabel}` as IssueItem['type'],
    title: i.title,
    summary: i.root_cause || i.title,
    section: reqA.section ? `Section ${reqA.section}` : i.category,
    severity: sev,
    status: i.status === 'open' ? 'Active' : i.status === 'resolved' ? 'Resolved' : 'Under Review',
    details: (reqA.quote || reqA.text) ? {
      reqA: { id: reqA.code || (i.affected_req_ids || [])[0] || '',
              text: reqA.quote || reqA.text || '',
              section: reqA.section ? `Sec ${reqA.section}` : '—' },
      reqB: reqB.quote || reqB.text ? {
        id: reqB.code || (i.affected_req_ids || [])[1] || '',
        text: reqB.quote || reqB.text || '',
        section: reqB.section ? `Sec ${reqB.section}` : '—',
      } : undefined,
      rootCause: i.root_cause || '—',
      recommendedResolution: i.ai_recommendation || '—',
    } : undefined,
  };
}

export function formatLogEvent(e: StreamEvent): string {
  const ts = e.timestamp ? new Date(e.timestamp).toTimeString().slice(0, 8) : '';
  return `${ts ? `[${ts}] ` : ''}[${e.tag}] ${e.message}`;
}
