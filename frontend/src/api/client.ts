const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
      ...options,
    });
    if (!res.ok) {
      throw new Error(`API error ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    console.warn(`[API Client] Fallback mode active for ${endpoint}:`, err);
    throw err;
  }
}

export interface DashboardSummary {
  active_projects_count: number;
  analyzing_projects_count: number;
  overall_quality_score: number;
  quality_trend_percentage: number;
  open_issues_count: number;
  open_issues_by_severity: { critical: number; high: number; medium: number; low: number };
  total_requirements_count: number;
  domains_count: number;
}

export interface ProjectData {
  id: string;
  name: string;
  version: string;
  domain: string;
  description?: string;
  status: string;
  quality_score: number;
  open_ambiguities_count: number;
  parsed_requirements_count: number;
  lint_mode: string;
  retention_mode: string;
  document_filename?: string;
  document_size_bytes?: number;
  document_sha256?: string;
  last_analyzed_at?: string;
  created_at: string;
  updated_at: string;
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
  rule_violations: Array<{ rule_id: string; type: string; term: string; severity: string }>;
  ai_recommendation?: string;
  score_boost?: number;
  created_at: string;
  updated_at: string;
}

export interface IssueData {
  id: string;
  project_id: string;
  issue_id_str: string;
  title: string;
  severity: string;
  category: string;
  affected_req_ids: string[];
  root_cause?: string;
  evidence_json: Record<string, any>;
  ai_recommendation?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AnalysisRunData {
  id: string;
  project_id: string;
  document_filename: string;
  document_size_bytes: number;
  document_sha256: string;
  context_standard: string;
  analysis_mode: string;
  status: string;
  current_stage: string;
  progress_percentage: number;
  total_requirements: number;
  processed_requirements: number;
  throughput_req_per_sec: number;
  elapsed_seconds: number;
  eta_seconds: number;
  logs: Array<{ timestamp: string; level: string; message: string }>;
  created_at: string;
  updated_at: string;
}

export const api = {
  getHealth: () => fetchJson<{ status: string }>('/health'),
  getDashboardSummary: () => fetchJson<DashboardSummary>('/dashboard/summary'),
  getProjects: () => fetchJson<ProjectData[]>('/projects'),
  getProject: (id: string) => fetchJson<ProjectData>(`/projects/${id}`),
  getRequirements: (params?: { project_id?: string; type?: string; status?: string }) => {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return fetchJson<RequirementData[]>(`/requirements${query ? `?${query}` : ''}`);
  },
  applyRequirementRewrite: (reqId: string) =>
    fetchJson<RequirementData>(`/requirements/${reqId}/rewrite`, { method: 'POST' }),
  getIssues: (params?: { project_id?: string; severity?: string; status?: string }) => {
    const query = new URLSearchParams(params as Record<string, string>).toString();
    return fetchJson<IssueData[]>(`/issues${query ? `?${query}` : ''}`);
  },
  resolveIssue: (issueId: string) =>
    fetchJson<IssueData>(`/issues/${issueId}/resolve`, { method: 'POST' }),
  getAnalysisRun: (runId: string) => fetchJson<AnalysisRunData>(`/analysis/${runId}`),
  uploadDocument: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch(`${API_BASE_URL}/analysis/upload`, {
      method: 'POST',
      body: formData,
    }).then((res) => {
      if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);
      return res.json() as Promise<AnalysisRunData>;
    });
  },
  getEventStreamUrl: () => `${API_BASE_URL}/events/stream`
};
