export type ActiveTab = 'dashboard' | 'projects' | 'srs-progress' | 'requirements' | 'issues' | 'traceability' | 'reports' | 'settings';

export type RequirementSeverity = 'critical' | 'high' | 'medium' | 'low' | 'clean';

export interface RequirementItem {
  id: string;
  title: string;
  category: string;
  type: 'functional' | 'non-functional';
  status: 'Needs Review' | 'Conflict' | 'Verified' | 'Analyzing';
  ambiguityScore: number; // 0 - 100
  originalText: string;
  suggestedRewrite?: string;
  issues: {
    id: string;
    type: string;
    description: string;
    severity: 'critical' | 'high' | 'medium';
  }[];
  conflictingReqId?: string;
  section: string;
  author: string;
  lastUpdated: string;
  acceptanceCriteria?: string[];
  traceabilityLinks?: string[];
}

export interface IssueItem {
  id: string;
  reqIds: string[];
  type: 'CRITICAL · REQUIREMENT CONFLICT' | 'HIGH · AMBIGUOUS WORDING' | 'HIGH · MISSING ACCEPTANCE' | 'MEDIUM · TRACEABILITY GAP';
  title: string;
  summary: string;
  section: string;
  severity: 'critical' | 'high' | 'medium';
  status: 'Active' | 'Resolved' | 'Under Review';
  details?: {
    reqA: { id: string; text: string; section: string };
    reqB?: { id: string; text: string; section: string };
    rootCause: string;
    recommendedResolution: string;
  };
}

export interface ProjectItem {
  id: string;
  name: string;
  fileName: string;
  version: string;
  requirementsCount: number;
  qualityScore: number;
  openIssuesCount: number;
  status: 'Completed' | 'Analyzing' | 'Draft';
  lastScan: string;
  domain: string;
}
