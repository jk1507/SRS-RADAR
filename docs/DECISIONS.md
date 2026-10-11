# Requirement Radar — Architecture Decisions Record (ADR)

## Decision Log

### ADR-001: Run Profile & Provider Abstraction (`local-free`)
- **Status:** Approved
- **Context:** System target is 100% zero-cost local execution (`PROFILE=local-free`).
- **Decision:** All LLM, embedding, storage, and database services sit behind standard protocols/interfaces (`LLMProvider`, `EmbeddingProvider`, `StorageBackend`). Local execution uses Ollama (`qwen2.5:7b-instruct`), local CPU embeddings (`BAAI/bge-small-en-v1.5`), Docker Postgres+pgvector, Redis (pub/sub), and MinIO (S3-compatible).

### ADR-002: Containerized Backend & Async Job Queue
- **Status:** Approved
- **Context:** Avoid heavy Windows native python dependencies for worker tasks and ensure deterministic execution environment.
- **Decision:**
  1. The FastAPI backend API server and background worker process run inside **Docker Compose Linux containers**.
  2. Frontend (Next.js/Vite) and Ollama host server run natively on the host machine.
  3. Celery is replaced with a **Postgres-backed asynchronous job queue** (`jobs` table in PostgreSQL) processed by a dedicated worker container (`backend-worker`). Redis is retained optionally for SSE pub/sub events.

### ADR-003: Section 34.1 Generation Settings
- **Status:** Approved
- **Context:** Temperature settings across LLM providers vary (e.g. reasoning models vs standard instruct models).
- **Decision:** Implementation follows PRD Section 34.1. The LLM wrapper exposes `generation_profile = deterministic` (mapping to provider-specific low-variance parameters). Reproducibility is strictly guaranteed via input hash caching (`llm_cache` table) and full run snapshotting (`config_snapshot_json`), rather than relying on global temperature assumptions.

### ADR-004: PDF Report Generation (Deferred to M9)
- **Status:** Decision deferred
- **Context:** Executive PDF export requires HTML-to-PDF rendering capability.
- **Decision:** The final selection between containerized WeasyPrint vs Chromium headless export will be made at Milestone M9 after evaluating Docker image size, font rendering quality, and build speed.

### ADR-005: Full Schema Migration & pgvector Extension
- **Status:** Approved
- **Context:** Comprehensive data model with 23 tables required for SRS RADAR (organizations, users, projects, requirements, issues, analysis_runs, audit_logs, etc.).
- **Decision:** Created Alembic initial migration `0001_initial_schema.py` covering all core entities and vector extension creation.

### ADR-006: AI Engine & INCOSE Rule Solvers
- **Status:** Approved
- **Context:** Syntactic and semantic requirement quality validation required without relying solely on LLM calls.
- **Decision:** Implemented `ai_engine/rules/incose.py` for deterministic INCOSE rule parsing and `ai_engine/solvers/z3_solver.py` for numerical/logical contradiction detection (e.g. auto-lock timeout conflicts).

### ADR-007: Server-Sent Events (SSE) Telemetry Stream
- **Status:** Approved
- **Context:** Real-time ingestion stream and live scan progress needed on frontend.
- **Decision:** Implemented `/api/v1/events/stream` SSE endpoint delivering live telemetry logs to the frontend App Shell and SRS progress scanner views.

### ADR-008: Automated OpenAPI Spec & Typed Frontend Client
- **Status:** Approved
- **Context:** Keep frontend and backend strictly synchronized through single source of truth contract.
- **Decision:** Created `scripts/generate-openapi.py` producing `frontend/src/api/openapi.json` and `frontend/src/api/client.ts` typed API client wrapper.
