# Phase 2 Integration Guide

## Overview of Phase 2 Features
Phase 2 introduces advanced collaboration and analysis capabilities on top of the existing Phase 1 workflow. Key features include:
- Enhanced CodeEditorPane with multi-file context and linting
- TaggingPane for semantic tagging and dataset labeling
- LogsPane for live run logs and historical execution trails
- New /api/phase2/* endpoints for feature control and data flow
- Feature-flag driven activation via config.js and backend env vars

## Activation Instructions (Frontend via config.js feature flags)
In config.js, add or update the featureFlags object and toggle Phase 2 features. Example:

module.exports = {
  // ...other config
  featureFlags: {
    PHASE_2_ENABLED: true,            // Master switch for Phase 2
    CODE_EDITOR_PHASE2: true,         // Enables enhanced CodeEditorPane behaviors
    TAGGING_PANE_ENABLED: true,       // Enables TaggingPane
    LOGS_PANE_ENABLED: true           // Enables LogsPane
  }
};

Notes:
- Keep PHASE_2_ENABLED = false until Phase 1 validation is complete.
- Individual flags allow incremental rollout and A/B validation.

## Backend Environment Variable Setup
Set the master environment variable to gate backend routes and processing:

PHASE_2_ENABLED=true

- For local development: add to .env or your shell export.
- For containerized deployments: set as an environment variable in your orchestrator (Docker Compose, Kubernetes, etc.).
- Backend must conditionally register /api/phase2/* routes when PHASE_2_ENABLED=true.

## Step-by-Step Integration Guide
1) Validate Phase 1 Baseline
   - Ensure core flows run: edit -> run -> evaluate.
   - Confirm API health for Phase 1 endpoints and that tests pass.

2) Enable Frontend Flags Incrementally (config.js)
   - Start with PHASE_2_ENABLED=false and turn on one UI flag at a time behind the master off state for QA builds.
   - Turn PHASE_2_ENABLED=true on a feature branch or staging only after verifying UI does not regress.

3) Backend Flagging
   - Set PHASE_2_ENABLED=true on backend in staging; verify /api/phase2/* routes respond.
   - Keep production PHASE_2_ENABLED=false until sign-off.

4) Verification per Feature
   - CodeEditorPane: open files, confirm linting/messages, multi-file context loads, saves do not regress Phase 1.
   - TaggingPane: create/edit tags, ensure tags persist via API; verify permissions and validation.
   - LogsPane: run a job; confirm live stream and historical retrieval; test pagination and filters.

5) End-to-End Tests
   - Add/update tests to cover Phase 2 routes and UI interactions.
   - Validate telemetry/analytics events for new interactions.

6) Rollout
   - Gradually enable flags in production per risk appetite; monitor logs and metrics.

## Component Descriptions
- CodeEditorPane: Enhanced editor that supports multi-file context, inline diagnostics, and save hooks. Exposes callbacks: onSave, onLintErrors, onFileSwitch.
- TaggingPane: UI for tagging code snippets, datasets, and runs. Supports CRUD operations and bulk apply. Emits events: onTagCreate, onTagUpdate, onTagDelete.
- LogsPane: Live and historical logs viewer. Supports stream follow, search, severity filters, and pagination. Emits events: onStreamStart, onStreamStop, onFilterChange.

## API Endpoint Documentation (/api/phase2/*)
Base path is gated by PHASE_2_ENABLED on the backend.

- GET /api/phase2/status
  - Returns: { enabled: boolean, components: { editor: bool, tagging: bool, logs: bool } }

- GET /api/phase2/tags
  - Query: search (optional), page, pageSize
  - Returns: { items: Tag[], page, pageSize, total }

- POST /api/phase2/tags
  - Body: { name: string, color?: string }
  - Returns: Tag

- PATCH /api/phase2/tags/:id
  - Body: { name?: string, color?: string }
  - Returns: Tag

- DELETE /api/phase2/tags/:id
  - Returns: { ok: true }

- GET /api/phase2/logs
  - Query: runId (required), cursor?, level?, q?
  - Returns: { items: LogEntry[], nextCursor? }

- GET /api/phase2/logs/stream
  - Query: runId (required)
  - Returns: Server-Sent Events (text/event-stream) stream of LogEntry

- POST /api/phase2/editor/lint
  - Body: { files: { path: string, content: string }[] }
  - Returns: { errors: LintError[] }

- POST /api/phase2/editor/save
  - Body: { path: string, content: string, message?: string }
  - Returns: { ok: true, version: string }

Error model:
- Status codes: 400 validation, 401/403 auth, 404 missing, 5xx server.
- Body: { error: { code: string, message: string, details?: any } }

## Troubleshooting
- Phase 2 UI hidden
  - Ensure config.js featureFlags.PHASE_2_ENABLED=true and that the build picked up changes.
- 404 on /api/phase2/*
  - Backend PHASE_2_ENABLED must be true; confirm route registration order and base path.
- Logs not streaming
  - Verify SSE endpoint enabled and reverse proxy supports streaming (disable buffering).
- Tag create fails (400)
  - Validate payload; check server validation messages and color format.
- Editor save conflicts
  - Ensure optimistic updates handle backend version; retry with latest version from server.

## Architecture Diagram (Textual)
Phase 1 Layout:
[UI] CodeEditorPane (basic) -> [API] /api/code/* -> [Engine] Runner -> [Store] Artifacts

Phase 2 Layout:
[UI] CodeEditorPane+TaggingPane+LogsPane -> [API] /api/phase2/* -> [Services] Linting/Tagging/Logging -> [Store] Tags+Logs+Artifacts

Legend: '->' request/stream, '+' composition, [ ] subsystem.

## Change Log
- Added Phase 2 integration documentation.
