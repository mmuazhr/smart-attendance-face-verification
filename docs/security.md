# Security and Privacy Model

## Protected Assets

- Face templates, which remain biometric data even when represented as embeddings.
- Participant names and identifiers.
- Attendance events and timestamps.
- Template-encryption key and local admin token.
- Integrity of detector/recognizer weights and decision thresholds.

## Implemented Controls

| Threat | Control |
| --- | --- |
| Raw image retention | Uploads are read into memory and never written by application code |
| Template database theft | AES-256-GCM per template with a random nonce and participant-bound additional authenticated data |
| Template swapping or tampering | AES-GCM authentication and participant ID binding fail closed |
| Duplicate or retried check-in | Unique participant/session attendance constraint plus transactional writes; legacy API also has idempotency and duplicate-window checks |
| Concurrent duplicate writes | `BEGIN IMMEDIATE`, unique constraint, and indexed participant/time lookup |
| Ambiguous image | Reject unreadable, undersized, no-face, multi-face, dim, bright, blurry, or small-face inputs |
| Unauthorized enrollment/export/deletion | Expiring signed sessions with server-side admin RBAC; legacy token comparison remains for compatibility routes |
| Browser cross-origin form abuse | State-changing admin routes require a custom header; verification requires a custom idempotency header |
| SQL injection | Parameterized SQLite statements only |
| Model supply-chain substitution | Fixed upstream URLs and SHA-256 checksums before atomic install |
| Sensitive logging | JSON logs use route templates and omit URLs, IDs, bodies, images, embeddings, tokens, and IP addresses |
| Accidental Git publication | Biometric directories, databases, model binaries, secrets, attendance CSVs, and HDF5 weights are ignored |

## Residual Risks

PresenceGuard does not implement validated presentation-attack detection. A high-quality replay could pass. Face matching is probabilistic, and the observed false-accept result is based on only 135 test negatives. An operator must not interpret “0 observed false accepts” as a zero population risk.

The local interface is a single-workspace role-aware reference application, not a multi-tenant
institutional authorization system. Binding beyond loopback, sharing an admin token broadly,
placing the database and key together, or using HTTP across a network invalidates the default
threat model. A real deployment requires campus SSO, TLS, managed key storage, audit retention
policy, role separation, rate limiting, backups, incident response, and a non-biometric recovery
path.

The SFace directory carries Apache-2.0 terms, but the precise training-data provenance for the distributed weight is not fully documented. Complete legal/model-risk review is required for commercial deployment.

## Privacy Lifecycle

1. Obtain explicit, revocable consent before enrollment.
2. Capture only the minimum burst needed for a stable template.
3. Discard frames after in-memory embedding extraction.
4. Encrypt reference embeddings before persistence.
5. Restrict attendance access to authorized operators.
6. Delete the participant to remove their template and cascade-delete attendance records.
7. Rotate keys and re-enroll participants when key compromise is suspected; automatic rotation is not implemented.

## Reporting a Vulnerability

Do not attach face images, templates, tokens, or attendance data to a public issue. Use GitHub's private security-advisory workflow for the repository owner.
