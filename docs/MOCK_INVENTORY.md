# Requirement Radar — Frontend Mock Inventory & API Replacement Mapping

This document lists every mock object, hardcoded count, hardcoded score, static issue, and mock stream log currently present in the frontend (`frontend/src/data/mockData.ts` and view components), mapped to the specific backend REST/SSE endpoint that will replace it.

---

## 1. Dashboard View (`DashboardView.tsx`)

| Element / Visual Component | Current Hardcoded / Mock Value | Backend Source / API Endpoint | Notes |
| --- | --- | --- | --- |
| User Name Greeting | `"Jack"` | `GET /api/v1/me` (`name`) | Authenticated user profile |
| User Role | `"Lead Architect"` | `GET /api/v1/me` (`role`) | Auth RBAC profile |
| Active Specifications KPI | `3 Projects Enrolled` | `GET /api/v1/dashboard/summary` (`active_projects_count`) | Count of non-archived projects |
| Active Specs Subtext | `1 pending live analysis` | `GET /api/v1/dashboard/summary` (`analyzing_projects_count`) | Count of projects in `analyzing` status |
| Quality Index KPI | `83.3 / 100` | `GET /api/v1/dashboard/summary` (`overall_quality_score`) | Mean quality score across active projects |
| Quality Index Trend | `+5.4% vs last month` | `GET /api/v1/dashboard/summary` (`quality_trend_percentage`) | Delta between recent runs |
| Open Ambiguities KPI | `18 Detected` | `GET /api/v1/dashboard/summary` (`open_issues_count`) | Count of open issues (D1 spec) |
| Severity Split | `3 Crit · 7 High · 8 Med` | `GET /api/v1/dashboard/summary` (`open_issues_by_severity`) | `{ critical, high, medium, low }` |
| Parsed Requirements KPI | `248 Statements` | `GET /api/v1/dashboard/summary` (`total_requirements_count`) | Sum of requirements across active projects |
| Target Domains Subtext | `Across 3 target domains` | `GET /api/v1/dashboard/summary` (`domains_count`) | Unique project domains |
| Enrolled Specifications List | `mockProjects` (Smart Hospital, Drone Nav, FinTech Gateway) | `GET /api/v1/projects` | Real project list with score, status, file info |
| Radar Ingestion Stream | `mockLiveTelemetryLogs` | `GET /api/v1/events/stream` (SSE) | Org-level SSE telemetry event stream |

---

## 2. SRS Analysis Progress View (`SrsProgressView.tsx`)

| Element / Visual Component | Current Hardcoded / Mock Value | Backend Source / API Endpoint | Notes |
| --- | --- | --- | --- |
| Document Title | `"Smart-Hospital-SRS-v1.3.pdf"` | `GET /api/v1/analysis/{run_id}` (`document_filename`) | Active run document metadata |
| File Size | `"2.4 MB"` | `GET /api/v1/analysis/{run_id}` (`document_size_bytes`) | Formatted byte size |
| Parsed Statements Count | `"84 statements"` | `GET /api/v1/analysis/{run_id}` (`total_requirements`) | Extracted requirement count |
| Context Standard | `"ISO/IEC/IEEE 29148"` | `GET /api/v1/analysis/{run_id}` (`context_standard`) | Active lint context |
| Document Hash | `"0x9E2F...C1A0"` | `GET /api/v1/analysis/{run_id}` (`document_sha256`) | SHA-256 integrity hash |
| Engine Mode | `"Deep Semantics v2.4"` | `GET /api/v1/analysis/{run_id}` (`analysis_mode`) | `fast_scan`, `standard_audit`, `deep_semantics` |
| Privacy Ring | `"Zero-Retention Airgap"` | `GET /api/v1/projects/{id}` (`retention_mode`) | `standard` vs `zero_retention` badge |
| Elapsed Time | Local `setInterval` counter | `GET /api/v1/analysis/{run_id}/status` (`elapsed_seconds`) | Backend run duration |
| Estimated Remaining | `"00:01s"` | `GET /api/v1/analysis/{run_id}/status` (`eta_seconds`) | Computed throughput ETA |
| Processing Speed | `"9.3 req/s"` | `GET /api/v1/analysis/{run_id}/status` (`throughput`) | EMA req/sec calculation |
| Pipeline Stage Indicator | `"Stage 4 of 6"` | `GET /api/v1/analysis/{run_id}/status` (`current_stage`) | Map internal LangGraph node to UI stage 1-6 |
| Circular Progress % | `98%` (`82 / 84 REQ`) | `GET /api/v1/analysis/{run_id}/status` (`processed` / `total`) | Real-time requirement processing count |
| Scan Telemetry Log | `mockLiveTelemetryLogs` | `GET /api/v1/analysis/{run_id}/events` (SSE) | Real SSE event stream per run |

---

## 3. Requirements Matrix View (`RequirementsMatrixView.tsx`)

| Element / Visual Component | Current Hardcoded / Mock Value | Backend Source / API Endpoint | Notes |
| --- | --- | --- | --- |
| Header Total Badge | `"6 TOTAL ENROLLED"` | `GET /api/v1/projects/{id}/requirements` (`total`) | Real total requirement count for project |
| SpecSentinel Sync Time | Hardcoded header label | `GET /api/v1/projects/{id}/summary` (`last_analyzed_at`) | Timestamp of last completed run |
| Lint Mode Chip | `"Strict INCOSE"` | `GET /api/v1/projects/{id}` (`lint_mode`) | Org/project settings |
| Requirement Table Items | `mockRequirements` (REQ-024, REQ-031, REQ-042, etc.) | `GET /api/v1/projects/{id}/requirements` | Server-paginated requirements list |
| Detail Panel Clarity Score | `42 / 100` (REQ-024) | `GET /api/v1/requirements/{id}` (`clarity_score`) | Computed Semantic Quality Index (Sec 20.8) |
| Rule Violations | Hardcoded `Subjective Lexicon`, `Weak Modal Verb` | `GET /api/v1/requirements/{id}` (`rule_violations`) | Real rule engine & LLM findings |
| AI Testable Rewrite | Hardcoded suggested rewrite string | `GET /api/v1/requirements/{id}` (`ai_recommendation`) | Validated proposal + score delta |
| Score Boost Delta | `"+50 Score Boost"` | `POST /api/v1/requirements/{id}/rewrite` | Re-analyzed score preview delta (D6) |
| Apply Rewrite Action | Local React state mutation | `POST /api/v1/recommendations/{id}/accept` | Creates `requirement_versions` + audit log |

---

## 4. Issues & Conflict Resolver View (`IssuesConflictResolverView.tsx`)

| Element / Visual Component | Current Hardcoded / Mock Value | Backend Source / API Endpoint | Notes |
| --- | --- | --- | --- |
| Header Issue Count | `"5 total issues detected..."` | `GET /api/v1/projects/{id}/issues` (`total_count`) | Shared API summary count (D1 spec) |
| Severity Badges | `3 Critical · 7 High · 8 Medium` | `GET /api/v1/projects/{id}/issues` (`severity_counts`) | Open issues severity breakdown |
| Issue List Items | `mockIssues` (ISS-001, ISS-002, etc.) | `GET /api/v1/projects/{id}/issues` | Open issues with evidence & quotes |
| Side-by-side Clauses | Hardcoded REQ-031 vs REQ-042 comparison | `GET /api/v1/issues/{id}` (`evidence_json`) | Normalized constraints + quotes |
| Root Cause Diagnostic | Hardcoded prose string | `GET /api/v1/issues/{id}` (`root_cause`) | LLM reasoning analysis |
| Harmonized Resolution | Hardcoded recommended resolution string | `GET /api/v1/issues/{id}` (`ai_recommendation`) | AI replacement proposals |
| Apply Resolution CTA | Local state mutation | `POST /api/v1/issues/{id}/resolve` | Updates affected requirements + audit |

---

## 5. Traceability View (`TraceabilityView.tsx`)

| Element / Visual Component | Current Hardcoded / Mock Value | Backend Source / API Endpoint | Notes |
| --- | --- | --- | --- |
| Coverage KPIs | Hardcoded % architecture & test coverage | `GET /api/v1/projects/{id}/traceability` (`coverage_stats`) | Calculated coverage percentages |
| Traceability Matrix | Hardcoded table rows | `GET /api/v1/projects/{id}/traceability` | Matrix of REQs vs ARCH/TEST targets |
| Dependency Graph | Static node connections | `GET /api/v1/projects/{id}/graph` | Graph nodes & typed relationship edges |

---

## 6. Reports View (`ReportsView.tsx`)

| Element / Visual Component | Current Hardcoded / Mock Value | Backend Source / API Endpoint | Notes |
| --- | --- | --- | --- |
| Audit Score & Radar Chart | Hardcoded 83.3 / 100 with dimension breakdown | `GET /api/v1/projects/{id}/report` | Real 7-dimension scoring breakdown |
| PDF Export Button | `alert("Generating PDF...")` | `GET /api/v1/projects/{id}/report.pdf` | Server-side PDF export |

---

## 7. Projects View (`ProjectsView.tsx`) & App Shell

| Element / Visual Component | Current Hardcoded / Mock Value | Backend Source / API Endpoint | Notes |
| --- | --- | --- | --- |
| Project Cards Grid | `mockProjects` | `GET /api/v1/projects` | All project cards with status & score |
| Target Engine Badge | `"SpecSentinel AI 🟢"` | `GET /api/v1/health/ai` | Real AI health check status badge |
| Notification Bell Count | `3` | `GET /api/v1/notifications` (`unread_count`) | Unread notifications count |
| Global Search (⌘K / Ctrl+K) | Static UI trigger | `GET /api/v1/search?q=...` | Hybrid vector + FTS search endpoint |
