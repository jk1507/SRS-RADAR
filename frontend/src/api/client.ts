/**
 * Typed API client — single source of truth for backend access (PRD 11).
 * Auth: auto-login with the seeded demo account (no login screen in the
 * existing design); token stored in localStorage, attached to every call.
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const TOKEN_KEY = 'rr_access_token';
const REFRESH_KEY = 'rr_refresh_token';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setTokens(access: string, refresh?: string) {
  localStorage.setItem(TOKEN_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';

  let res: Response;
  try {
    res = await fetch(url, { ...options, headers });
  } catch (err) {
    throw new ApiError(0, `Network error: ${(err as Error).message}`);
  }
  if (res.status === 401) {
    // token expired -> try once to refresh, else re-login
    const refreshed = await tryRefresh();
    if (refreshed) {
      headers['Authorization'] = `Bearer ${getToken()}`;
      res = await fetch(url, { ...options, headers });
    }
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || body.error?.message || detail;
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

async function tryRefresh(): Promise<boolean> {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!refresh) return false;
  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const body = await res.json();
    setTokens(body.access_token, body.refresh_token);
    return true;
  } catch {
    return false;
  }
}

/** Ensure we have a session (auto-login for the seeded demo user). */
export async function ensureAuth(): Promise<void> {
  if (getToken()) return;
  const email = import.meta.env.VITE_DEMO_EMAIL || 'jack@requirement-radar.dev';
  const password = import.meta.env.VITE_DEMO_PASSWORD || 'radar-demo-2026';
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new ApiError(res.status, 'Auto-login failed — start the backend and seed the demo user.');
  const body = await res.json();
  setTokens(body.access_token, body.refresh_token);
}

// ----------------------------------------------------------------- types
export interface DashboardSummary {
  active_projects_count: number;
  analyzing_projects_count: number;
  overall_quality_score: number;
  quality_trend_percentage: number | null;
  open_issues_count: number;
  open_issues_by_severity: { [k: string]: number };
  total_requirements_count: number;
  domains_count: number;
  projects: ProjectData[];
  recent_events: StreamEvent[];
}

export interface ProjectData {
  id: string;
  name: string;
  version: string;
  domain: string;
  description?: string;
  status: string;
  quality_score: number;
  previous_quality_score?: number | null;
  open_ambiguities_count: number;
  parsed_requirements_count: number;
  dimension_scores: Record<string, number | null>;
  lint_mode: string;
  retention_mode: string;
  is_archived: boolean;
  document_filename?: string;
  document_size_bytes?: number;
  document_sha256?: string;
  last_analyzed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectSummary {
  project: ProjectData;
  total_requirements: number;
  needs_review: number;
  verified: number;
  issues_total: number;
  issues_open: number;
  issues_resolved: number;
  issues_by_severity_open: Record<string, number>;
  issues_by_type_open: Record<string, number>;
  dimension_scores: Record<string, number | null>;
  quality_score: number;
  trend_percentage: number | null;
  coverage: Record<string, number>;
  active_run_id: string | null;
}

export interface RuleViolation {
  rule_id: string;
  type: string;
  term?: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  description: string;
  quote?: string;
  span?: number[] | null;
}

export interface RequirementData {
  id: string;
  project_id: string;
  req_id_str: string;
  type: string;
  category: string;
  clause_text: string;
  clarity_score: number;
  status: string;
  rule_violations: RuleViolation[];
  source_page?: number | null;
  source_section?: string | null;
  source_heading?: string | null;
  scores_json: Record<string, number>;
  ambiguities_json: { phrase: string; reason: string; severity: string; span?: number[] }[];
  constraints_json: unknown[];
  missing_information_json: string[];
  has_actor: boolean;
  is_testable: boolean;
  compound: boolean;
  version: number;
  ai_recommendation?: string | null;
  score_boost?: number | null;
  created_at: string;
  updated_at: string;
}

export interface IssueData {
  id: string;
  project_id: string;
  issue_id_str: string;
  issue_type: string;
  title: string;
  severity: string;
  category: string;
  affected_req_ids: string[];
  root_cause?: string;
  evidence_json: Record<string, any>;
  ai_recommendation?: string;
  rule_id?: string;
  confidence: number;
  verification_status: string;
  decision: string;
  status: string;
  assignee?: string;
  resolution_note?: string;
  created_at: string;
  updated_at: string;
}

export interface IssueCounts {
  total: number;
  open: number;
  resolved: number;
  dismissed: number;
  open_by_severity: Record<string, number>;
  open_by_type: Record<string, number>;
}

export interface AnalysisRunData {
  id: string;
  project_id: string;
  document_filename: string;
  document_size_bytes: number;
  document_sha256: string;
  context_standard: string;
  analysis_mode: string;
  lint_mode: string;
  status: string;
  current_stage: string;
  stage_index: number;
  progress_percentage: number;
  total_requirements: number;
  processed_requirements: number;
  throughput_req_per_sec: number;
  elapsed_seconds: number;
  eta_seconds: number;
  cancel_requested: boolean;
  error?: string;
  scores_json: Record<string, any>;
  llm_status: string;
  logs: { timestamp: string; level: string; message: string; tag?: string }[];
  created_at: string;
  updated_at: string;
  finished_at?: string;
}

export interface StreamEvent {
  event_id?: number;
  run_id: string;
  stage: number;
  stage_index: number;
  processed: number;
  total: number;
  percentage: number;
  tag: string;
  message: string;
  req_code?: string;
  timestamp?: string;
}

export interface RecommendationData {
  id: string;
  project_id: string;
  requirement_id?: string;
  requirement_code: string;
  kind: string;
  proposed_text?: string;
  assumptions_json: { field?: string; proposed_value?: string; rationale?: string; question?: string }[];
  rationale?: string;
  questions_json: string[];
  predicted_score_delta: number;
  status: string;
  edited_text?: string;
}

export interface TraceMatrixRow {
  req_id: string;
  req_clause: string;
  arch_targets: { code: string; name: string; status: string; confidence: number; link_id: string }[];
  test_targets: { code: string; name: string; status: string; confidence: number; link_id: string }[];
  compliance_targets: { code: string; name: string; status: string; confidence: number; link_id: string }[];
  coverage_percentage: number;
  status: string;
}

export interface TraceMatrix {
  rows: TraceMatrixRow[];
  totals: Record<string, number | string[]>;
}

export interface ProjectReport {
  generated_at: string;
  project: Record<string, any>;
  score: { overall: number; previous: number | null; trend: number | null;
           dimensions: Record<string, number | null>; weights: Record<string, number> };
  compliance: { incose_pct: number; compliant_requirements: number; total_requirements: number };
  issues: { total: number; open: number; resolved: number;
            by_severity_open: Record<string, number>;
            critical_factors: { title: string; severity: string; affected: string[]; root_cause?: string }[];
            conflicts: any[] };
  traceability: { linked_requirements: number; coverage_pct: number };
  recommendations: { requirement: string; kind: string; proposed_text?: string;
                     delta: number; assumptions: any[] }[];
  run_metadata: Record<string, any> | null;
}

export interface NotificationList {
  unread_count: number;
  items: { id: string; type: string; title: string; payload: any;
           read: boolean; created_at: string }[];
}

// ----------------------------------------------------------------- api
export const api = {
  // meta / health
  getHealth: () => request<{ status: string }>('/health'),
  getAIHealth: () => request<{ status: string; provider: string; fast_model: string }>('/health/ai'),
  getMeta: () => request<{ name: string; version: string; target_engine: string;
                           standard_context: string; profile: string }>('/meta'),

  // auth
  getMe: () => request<{ id: string; email: string; name: string; role: string;
                         organization?: { name: string; settings: any } }>('/auth/me'),
  logout: () => request('/auth/logout', { method: 'POST' }),

  // dashboard
  getDashboardSummary: () => request<DashboardSummary>('/dashboard/summary'),

  // projects
  getProjects: (params?: { search?: string; status?: string; sort?: string }) =>
    request<ProjectData[]>(`/projects${qs(params)}`),
  getProject: (id: string) => request<ProjectData>(`/projects/${id}`),
  createProject: (payload: Partial<ProjectData>) =>
    request<ProjectData>('/projects', { method: 'POST', body: JSON.stringify(payload) }),
  updateProject: (id: string, payload: Partial<ProjectData>) =>
    request<ProjectData>(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteProject: (id: string) => request(`/projects/${id}`, { method: 'DELETE' }),
  getProjectSummary: (id: string) => request<ProjectSummary>(`/projects/${id}/summary`),
  getRuns: (id: string) =>
    request<{ id: string; status: string; score?: number; progress: number;
              created_at: string; finished_at?: string }[]>(`/projects/${id}/runs`),

  // documents + analysis
  uploadDocument: (file: File, opts?: { projectId?: string; projectName?: string;
                                        onProgress?: (pct: number) => void }) => {
    const form = new FormData();
    form.append('file', file);
    if (opts?.projectId) form.append('project_id', opts.projectId);
    if (opts?.projectName) form.append('project_name', opts.projectName);
    return uploadWithProgress<AnalysisRunData>('/analysis/upload', form, opts?.onProgress);
  },
  analyzeProject: (projectId: string, mode = 'standard_audit') =>
    request<{ id: string }>(`/projects/${projectId}/analyze`, {
      method: 'POST', body: JSON.stringify({ mode }) }),
  getRun: (runId: string) => request<AnalysisRunData>(`/analysis/${runId}`),
  getRunStatus: (runId: string) =>
    request<{ status: string; stage: string; processed: number; total: number;
              percentage: number; eta_seconds: number; error?: string;
              scores: Record<string, any> }>(`/analysis/${runId}/status`),
  cancelRun: (runId: string) => request(`/analysis/${runId}/cancel`, { method: 'POST' }),
  retryRun: (runId: string) => request(`/analysis/${runId}/retry-failed`, { method: 'POST' }),
  getRunEventsUrl: (runId: string) =>
    `${API_BASE_URL}/analysis/${runId}/events?token=${encodeURIComponent(getToken() || '')}`,

  // requirements
  getRequirements: (params: { project_id?: string; type?: string; status?: string;
                              q?: string; page?: number; page_size?: number;
                              has_issues?: boolean }) =>
    request<RequirementData[]>(`/requirements${qs(params as Record<string, string>)}`),
  getRequirement: (id: string) => request<RequirementData>(`/requirements/${id}`),
  updateRequirement: (id: string, payload: { status?: string }) =>
    request<RequirementData>(`/requirements/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  getVersions: (id: string) =>
    request<{ id: string; version: number; text: string; source: string;
              change_reason?: string; created_at: string }[]>(`/requirements/${id}/versions`),
  getRecommendationsForReq: (id: string) =>
    request<RecommendationData[]>(`/requirements/${id}/recommendations`),
  generateRewrite: (id: string) =>
    request<RecommendationData>(`/requirements/${id}/rewrite`, { method: 'POST' }),
  getImpact: (id: string) =>
    request<{ affected_artifacts_count: number; impact_set: any[] }>(
      `/requirements/${id}/impact?depth=2`),

  // issues
  getIssues: (params: { project_id?: string; severity?: string; status?: string;
                        type?: string; q?: string }) =>
    request<IssueData[]>(`/issues${qs(params as Record<string, string>)}`),
  getIssue: (id: string) => request<IssueData>(`/issues/${id}`),
  getIssueCounts: (projectId?: string) =>
    request<IssueCounts>(`/issues/counts${qs({ project_id: projectId })}`),
  resolveIssue: (id: string, payload?: { note?: string; apply_text?: Record<string, string> }) =>
    request<IssueData>(`/issues/${id}/resolve`, {
      method: 'POST', body: JSON.stringify(payload || {}) }),
  dismissIssue: (id: string, reason: string) =>
    request<IssueData>(`/issues/${id}/dismiss`, {
      method: 'POST', body: JSON.stringify({ reason }) }),
  updateIssue: (id: string, payload: { status?: string; assignee?: string }) =>
    request<IssueData>(`/issues/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),

  // recommendations
  acceptRecommendation: (id: string, editedText?: string) =>
    request<RecommendationData>(`/recommendations/${id}/accept`, {
      method: 'POST', body: JSON.stringify(editedText ? { edited_text: editedText } : {}) }),
  rejectRecommendation: (id: string, reasonCode?: string) =>
    request<RecommendationData>(`/recommendations/${id}/reject`, {
      method: 'POST', body: JSON.stringify({ reason_code: reasonCode }) }),

  // traceability
  getTraceMatrix: (projectId: string) =>
    request<TraceMatrix>(`/traceability?project_id=${projectId}`),
  getTraceGraph: (projectId: string) =>
    request<{ nodes: any[]; edges: any[] }>(`/traceability/graph?project_id=${projectId}`),
  getTargets: (projectId: string) =>
    request<{ id: string; type: string; code: string; name: string }[]>(
      `/traceability/targets?project_id=${projectId}`),
  updateLink: (linkId: string, status: string) =>
    request(`/traceability/links/${linkId}`, {
      method: 'PATCH', body: JSON.stringify({ status }) }),

  // reports
  getReport: (projectId: string) =>
    request<ProjectReport>(`/projects/report?project_id=${projectId}`),
  getReportHtmlUrl: (projectId: string) =>
    `${API_BASE_URL}/projects/report.html?project_id=${projectId}`,
  getExportUrl: (projectId: string, kind: 'issues' | 'requirements', format: 'csv' | 'json') =>
    `${API_BASE_URL}/projects/export?project_id=${projectId}&kind=${kind}&format=${format}`,

  // search / notifications / settings
  search: (q: string, scope = 'all') =>
    request<{ scope: string; id: string; code?: string; title: string;
              subtitle?: string; score: number; project_id?: string }[]>(
      `/search?q=${encodeURIComponent(q)}&scope=${scope}`),
  getNotifications: () => request<NotificationList>('/notifications'),
  readNotification: (id: string) => request(`/notifications/${id}/read`, { method: 'POST' }),
  readAllNotifications: () => request('/notifications/read-all', { method: 'POST' }),
  getOrgSettings: () =>
    request<{ organization: any; settings: any; rules: any[]; platform: any }>('/org'),
  updateOrgSettings: (payload: { name?: string; settings?: any }) =>
    request('/org', { method: 'PATCH', body: JSON.stringify(payload) }),

  getEventStreamUrl: () =>
    `${API_BASE_URL}/events/stream?token=${encodeURIComponent(getToken() || '')}`,
};

// ----------------------------------------------------------------- helpers
function qs(params?: Record<string, any>): string {
  if (!params) return '';
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null && v !== '' && v !== false);
  return entries.length ? `?${new URLSearchParams(entries as any).toString()}` : '';
}

function uploadWithProgress<T>(endpoint: string, form: FormData,
                               onProgress?: (pct: number) => void): Promise<T> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}${endpoint}`);
    const token = getToken();
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      try {
        const body = JSON.parse(xhr.responseText || '{}');
        if (xhr.status >= 200 && xhr.status < 300) resolve(body as T);
        else reject(new ApiError(xhr.status, body.detail || xhr.statusText));
      } catch (err) {
        reject(new ApiError(xhr.status, xhr.statusText));
      }
    };
    xhr.onerror = () => reject(new ApiError(0, 'Upload failed'));
    xhr.send(form);
  });
}
