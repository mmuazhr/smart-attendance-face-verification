# PresenceGuard Product Upgrade Plan

This document records the repository assessment and implementation plan derived from the
`CODEX MASTER PROMPT — UPGRADE PRESENCEGUARD INTO A COMPLETE ATTENDANCE & RESEARCH SYSTEM`.
The pasted prompt is treated as the product specification; this file is the engineering
translation of that specification for the current codebase.

## Repository assessment

### 1. Current architecture

PresenceGuard is a local modular monolith. A FastAPI application serves a static browser
camera console and JSON/multipart endpoints. Application services call a YuNet/SFace face
engine, an AES-256-GCM template cipher, and a SQLite repository. The repository currently
contains only `participants` and `attendance_events` tables. The default process binds to
loopback and raw camera uploads are processed in memory.

### 2. Technology stack

- Python 3.12, FastAPI, Pydantic Settings, Uvicorn, and SQLite.
- OpenCV YuNet face detection and SFace embeddings.
- AES-GCM encrypted multi-sample templates.
- Vanilla HTML, CSS, and JavaScript for the current browser interface.
- Pytest, Ruff, MyPy, Bandit, pip-audit, and GitHub Actions CI.

### 3. Existing features

- Consent-gated, multi-sample face enrollment.
- Face quality gates and single-face verification.
- Encrypted participant templates with no raw-image schema.
- Local face verification and attendance writes.
- Idempotency-key replay handling and a configurable duplicate time window.
- Admin-token protection for enrollment, deletion, and attendance listing.
- Health endpoint, CLI, model downloader, privacy-safe request logging, documentation, and
  a restrained camera-first demo UI.

### 4. Missing product capabilities

- Account authentication, persistent sessions, and server-side role-based access control.
- Attendance session/class/event entities and eligibility rules.
- User and admin dashboards, user management, session management, reports, CSV export,
  attendance corrections, audit log UI, settings, and privacy/research navigation.
- Persistent verification-attempt records separate from attendance records.
- A modular liveness-provider boundary and explicit experimental status in the product UI.
- Responsive multi-route product navigation, accessible empty/loading/error states, and a
  non-biometric/manual attendance fallback.

### 5. Security weaknesses to address

- The current admin token is a single shared local secret, not an account with roles,
  expiry, logout, or audit identity.
- The current verification route trusts a caller-supplied participant ID and has no
  authenticated user/session or session eligibility boundary.
- Attendance has a duplicate time window but not the required unique participant/session
  invariant because an attendance session entity does not yet exist.
- Administrative actions and failed verification attempts are not persistently auditable.
- Liveness is not available; the system must expose that limitation and keep liveness
  separate from face matching.

### 6. Database/schema issues

The schema is intentionally minimal for the original research reference: participants and
events are sufficient for a demo but cannot represent users, roles, sessions, statuses,
manual corrections, audit metadata, settings, or verification attempts. The upgrade will
extend SQLite with additive, idempotent schema creation and preserve existing participant
templates and attendance events where practical.

### 7. UX problems

The current UI is a single operator-oriented camera page. It does not distinguish admin and
participant journeys, has no login, does not select an active session, does not show a
participant's history, and gives limited context for duplicate, camera, or session errors.
It also requires a participant ID during verification and exposes the shared admin-token
workflow directly in the enrollment form.

### 8. Existing files/modules to retain or modify

- `src/presenceguard/api.py`: add authenticated product routes while retaining compatible
  legacy API boundaries where safe.
- `src/presenceguard/domain.py`: add typed account, session, attendance, audit, and liveness
  objects.
- `src/presenceguard/repository.py`: add schema and transactional domain queries.
- `src/presenceguard/services.py`: centralise authentication, attendance policy, audit, and
  biometric orchestration.
- `src/presenceguard/config.py`: add session/security and product defaults.
- `src/presenceguard/static/*`: replace the single console with a responsive role-aware UI.
- `tests/*`: preserve existing regression coverage and add business-rule/API coverage.
- `README.md`, `docs/architecture.md`, and `TASKS.md`: document the complete product and
  residual research limitations.

### 9. Files/modules to add

- `src/presenceguard/auth.py`: password hashing and signed session-cookie helpers.
- `src/presenceguard/liveness.py`: explicit provider interface and unavailable provider.
- `docs/product-upgrade-plan.md`: this assessment and implementation record.
- Additional repository/service tests for authentication, sessions, corrections, exports,
  auditability, and authorization.

### 10. Proposed implementation order

1. Foundation: additive schema, seed/bootstrap admin, password hashing, session cookies,
   role guards, and central error handling.
2. Attendance core: persisted sessions, eligibility, status classification, one-record-per-
   participant/session transaction, and verification-attempt recording.
3. User experience: authenticated dashboard, active-session check-in, history, profile,
   enrollment status, privacy, and accessible camera states.
4. Biometric integration: connect existing encrypted enrollment/verification to authenticated
   attendance and expose a liveness-provider boundary without overstating capability.
5. Administration: dashboard, participants, sessions, attendance correction, audit logs,
   settings, and CSV reporting.
6. Research experience: the one-page milestone timeline, architecture visualisation, and
   transparent metrics/limitations.
7. Hardening: authorization review, validation, race-condition tests, responsive QA,
   accessibility checks, documentation, and full quality gates.

## Delivery boundary

This upgrade will make the surrounding attendance product real and locally usable. It will
not claim validated presentation-attack detection, institutional SSO, demographic fairness,
regulatory compliance, or production biometric assurance. Where those capabilities cannot be
validated in this repository, the implementation will provide an explicit modular seam,
research labeling, and a documented future integration path.

## Progress log

- [x] Repository assessment recorded.
- [x] Foundation and domain schema.
- [x] Authenticated attendance workflows.
- [x] Admin operations and reports.
- [x] Research Journey and responsive product UI.
- [x] Regression, security, and documentation verification.
