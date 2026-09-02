# PresenceGuard

PresenceGuard is a local, privacy-first reference implementation for face verification in attendance workflows. It modernises a 2023 Malaysian university FYP that used a custom Siamese CNN, webcam capture, and Firebase-style attendance records into a typed FastAPI application with YuNet detection, SFace embeddings, encrypted multi-sample templates, and transactional SQLite attendance events.

> Research and portfolio reference only. This project does not provide validated liveness detection, institutional authentication, demographic fairness evidence, or production biometric assurance. Historical face data, attendance records, and model weights are private and excluded from Git.

## Why this project exists

The original FYP explored whether deep-learning face verification could reduce manual attendance work and proxy attendance. The recovered implementation was valuable as a research prototype, but its evidence and engineering boundaries were not strong enough for modern reuse. PresenceGuard preserves the verification question while making the data split, privacy model, failure policy, and operational limits explicit.

## What it does

1. An authorized operator enrolls a participant after explicit consent.
2. The local camera or API sends short-lived frames; the server does not write raw images.
3. YuNet requires exactly one sufficiently large face and applies lighting/sharpness gates.
4. SFace produces a normalized 128-dimensional embedding.
5. AES-256-GCM encrypts a multi-sample template bound to the participant ID.
6. A verification query compares against the template and applies a calibrated threshold.
7. A successful match writes one UTC attendance event with idempotency and duplicate-window protection.

See [`docs/architecture.md`](docs/architecture.md) for the component and trust-boundary diagrams.

## Evidence at a glance

These are artifact-level measurements on the recovered private archive, not population claims.

| Protocol | Accuracy | Precision | Recall | False accepts | Runtime |
| --- | ---: | ---: | ---: | ---: | ---: |
| Legacy CNN deterministic replay | 77.8% | 94.8% | 59.8% | 3 / 88 negatives | 61.4 ms/pair |
| Legacy CNN chronological probe* | 98.9% | 98.5% | 99.3% | 2 / 135 negatives | 57.9 ms/pair |
| PresenceGuard SFace template test | **93.3%** | **100%** | **86.7%** | **0 / 135 negatives** | **9.0 ms/query** |

\* The legacy model's training manifest is missing, so the chronological probe may contain training examples and must not be read as clean generalisation evidence. The modern test covers one enrolled person, 135 positive queries, and 135 identity-disjoint negative queries. Full methodology is in [`docs/results.md`](docs/results.md).

## Quick start

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), and a browser with camera support for the web interface.

```bash
uv sync --extra dev
cp .env.example .env
uv run presenceguard generate-key
```

Copy the generated key into `PRESENCEGUARD_TEMPLATE_KEY` in `.env`, then set a local operator token in `PRESENCEGUARD_ADMIN_TOKEN`. Do not commit `.env`.

Download the checksummed OpenCV Zoo models and initialize the private database:

```bash
uv run presenceguard download-models
uv run presenceguard init-db
uv run presenceguard serve
```

Open <http://127.0.0.1:8000>. The default bind address is loopback. The application intentionally refuses enrollment, deletion, and attendance listing when no admin token is configured.

For a container workflow, copy `.env.example` to `.env`, set both secrets, place model files in `models/`, and run:

```bash
docker compose up --build
```

The compose file publishes only `127.0.0.1:8000` and mounts the database separately from the read-only application image.

## API outline

Enrollment is an admin action and requires a multipart request with 3–50 images in the default configuration:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/participants/student-042/enrollment \
  -H "X-Admin-Token: $PRESENCEGUARD_ADMIN_TOKEN" \
  -F display_name="Student 042" \
  -F consent_confirmed=true \
  -F images=@frame-01.jpg \
  -F images=@frame-02.jpg \
  -F images=@frame-03.jpg
```

Verification requires a unique `Idempotency-Key` and does not require the admin token:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/participants/student-042/verification \
  -H "Idempotency-Key: $(uuidgen)" \
  -F image=@query.jpg
```

The API returns `verified`, `duplicate`, or `rejected`; a rejected match never writes attendance. See the OpenAPI document at `/docs` while the server is running.

## Privacy and security boundaries

- Raw uploads are decoded and processed in memory; they are not stored by application code.
- Only encrypted numerical templates and attendance events persist locally.
- Templates use AES-256-GCM with random nonces and participant-bound authenticated data.
- Enrollment, deletion, and attendance reads require a local admin token.
- Request logs are compact JSON containing route templates, status, duration, and a request ID; they omit URLs, bodies, IPs, participant IDs, images, embeddings, and tokens.
- Model downloads use fixed HTTPS sources and SHA-256 verification before atomic installation.
- The interface is localhost-first and contains no cloud biometric call.

The threat model and residual risks are documented in [`docs/security.md`](docs/security.md). In particular, a single-frame verifier is not a liveness detector; real deployment needs a second factor, institutional identity, TLS, managed keys, rate limits, retention controls, and a recovery path that does not depend on biometrics.

## Original FYP → modernised system

| Original artifact | PresenceGuard response |
| --- | --- |
| Pair-level custom Siamese CNN | Retained as a private baseline; default runtime uses compact YuNet + SFace embeddings |
| Fixed webcam crop | Single-face detection, landmark alignment, and quality gates |
| Hard-coded 0.5 decision | Threshold calibrated on development data under an explicit false-accept policy |
| Raw verification images and CSV output | Encrypted templates and transactional SQLite events; no raw image retention |
| Notebook-centric workflow | Typed package, FastAPI API, browser demo, CLI, tests, CI, and container packaging |
| Unseeded pair split with possible leakage | Source/session-aware protocols with deterministic seeds and documented limitations |

The detailed reasoning and rejected alternatives are in [`docs/fyp-evolution.md`](docs/fyp-evolution.md). The original artifact inventory and research contradictions are in [`docs/artifact-inventory.md`](docs/artifact-inventory.md), [`docs/original-baseline.md`](docs/original-baseline.md), and [`docs/audit.md`](docs/audit.md).

## Validation

```bash
uv run --extra dev pytest -q --cov=presenceguard --cov-report=term-missing
uv run --extra dev ruff check src tests scripts
uv run --extra dev ruff format --check src tests scripts
uv run --extra dev mypy src
uv run --extra dev bandit -q -r src
uv run --extra dev pip-audit
```

The private-model smoke test is skipped unless authorized model files and face data exist under `.private/`. The public test suite uses synthetic vectors and fake image labels; no biometric data is required to run it.

## Repository layout

```text
src/presenceguard/       Typed application, domain, persistence, crypto, and model boundary
src/presenceguard/static/Camera-first local web interface
tests/                   Unit, API, repository, model-download, and private-model smoke tests
scripts/                 Historical audit, notebook summary, and baseline evaluation tools
docs/                    Architecture, audit, results, security, evolution, and interview notes
data/README.md           Private-data policy and reproducible manifest guidance
models/README.md         Model card, checksums, licensing, and provenance caveats
```

## Limitations and next research steps

The recovered archive does not contain the claimed 30-person UKM participant labels, consent records, or original split manifest. The strongest modern result is therefore narrow evidence for one enrolled person, not a fairness or production benchmark. SFace model training-data provenance also requires separate review before commercial or high-risk use.

Meaningful next steps are a consented multi-subject evaluation with subject/session-disjoint splits, validated presentation-attack detection, campus SSO plus a second factor, measured hardware-specific latency, key rotation, and a non-biometric attendance fallback.

## Author and license

Built by Muaz Husaini as a modern engineering continuation of the FYP *Smart Attendance System Using Face Recognition Techniques Based on Deep Learning*.

Application code is MIT-licensed. Third-party OpenCV Zoo model terms and checksums are listed in [`models/README.md`](models/README.md); the historical private artifacts are not part of the license grant.
