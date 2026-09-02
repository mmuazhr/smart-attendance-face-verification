# Modernisation Log

## 2026-09-02 - Discovery

### Finding

The requested source path resolves to the Google Drive folder `ONEDRIVE UKM/FYP`. The archive contains:

- notebook generations including `Final.ipynb`, `FACIAL RECOGNITION.ipynb`, desktop and Siamese variants;
- `data.zip` plus `data/{anchor,positive,negative}` and an LFW tree;
- `siamesemodelv2.h5` and TensorFlow checkpoints;
- `application_data` verification/input folders;
- demo images and a four-row attendance CSV.

The parent `ONEDRIVE UKM` folder contains the final thesis, technical report, proposals, a small presentation, and two tiny FYP ZIPs.

### Evidence

- Final thesis title: *Sistem Kehadiran Pintar Menggunakan Teknik Pengecaman Wajah Berasaskan Pembelajaran Mendalam*.
- Author: Muhammad Muaz Husaini bin Rosli, A182954, Universiti Kebangsaan Malaysia, 2023.
- Thesis-reported evaluation:
  - UKM: accuracy 0.8086, precision 0.7519, recall 0.9741.
  - LFW: accuracy 0.8125, precision 0.8222, recall 1.0000.
  - Cross-domain: accuracy 0.7344, precision 0.6863, recall 0.8633.
- The attendance artifact records MUAZ, TARIQ, BULYA, and BILL with times only.

### Contradictions and Risks

- Thesis: 80/20 split and K-fold validation. Notebook: shuffled pair construction followed by a 70/30 `take/skip` split.
- Thesis: FaceNet feature extractor. Notebook: a custom CNN embedding trained from scratch; no FaceNet model is used in the inspected implementation.
- Thesis: full Kivy/Firebase system. Inspected FYP source is predominantly notebooks; the described application source is not yet located.
- Augmentation appears to occur before splitting, which can place transformed versions of the same source face in both train and test sets.
- Pair-level splitting allows the same captured identity/image family to appear across partitions and cannot support demographic generalisation claims.
- The UKM face dataset contains sensitive biometric data from human subjects; consent and publication rights are not established.

### Decision

Treat the thesis results as historical reported results, not independently validated evidence. Reconstruct the baseline faithfully, then evaluate a modern approach with entity-aware and source-aware separation. Keep all personal biometric material private and Git-ignored.

## 2026-09-02 - Dataset and Model Forensics

### Finding

The recovered pair dataset has 1,378 readable RGB JPEG files at 250 × 250 pixels: 450 anchor, 450 positive, and 478 negative. Twelve exact duplicate groups exist within classes; no exact duplicate crosses a class label.

The saved `siamesemodelv2.h5` file is 155,886,704 bytes with SHA-256 `2db778b1395529527e02f8e94b5b85433be478f759ffdbc551f0f4359ff8f0fe`. Its metadata identifies Keras 2.12.0 and a TensorFlow backend. It contains a 38,964,545-parameter custom Siamese network and no training configuration.

### Decision

Use TensorFlow macOS 2.12.0 to maximize compatibility with the saved artifact on Apple Silicon. Keep the model and all face data Git-ignored. Publish only reproducible audit tooling, aggregate counts, architecture metadata, and defensible benchmark results.

### Notebook Lineage

Five substantial notebook variants were recovered. The top-level `Final.ipynb` is the most complete executed version and matches the saved model. It is the baseline authority; other variants are evidence of iteration, not separate product implementations.

## Engineering Decision - Workspace

### Options Considered

1. Modify the Google Drive archive directly.
2. Work in the dated projectless conversation folder.
3. Create a persistent project under the established `Documents/Codex/projects` area.

### Chosen Approach

Create `Documents/Codex/projects/smart-attendance-face-verification`.

### Reason

It is persistent, clearly named from the actual FYP, separate from the immutable source archive, and suitable for Git/GitHub work.

## Experiment 001 - Legacy Artifact Replay

### Question

Can the supplied HDF5 model be loaded and independently evaluated?

### Method

Use TensorFlow macOS/Keras 2.12.0, a fixed seed of 42, a deterministic analogue of the notebook's 300-image selection and 70/30 pair split, and the original 0.5 decision threshold. Also run a later-capture probe.

### Result

- Deterministic replay: accuracy 0.7778, precision 0.9483, recall 0.5978, FAR 0.0341, ROC AUC 0.9679, 61.4 ms/pair.
- Chronological probe: accuracy 0.9889, precision 0.9853, recall 0.9926, FAR 0.0148, ROC AUC 0.9997, 57.9 ms/pair.

### Interpretation

The artifact is runnable, but the missing original training manifest means neither protocol is guaranteed independent of training. The chronological number is likely optimistic and cannot validate the thesis's population claims.

## Experiment 002 - YuNet and SFace

### Question

Can a compact, locally executed, pretrained embedding replace the large custom CNN while improving the methodology?

### Method

Use OpenCV 4.14, YuNet 2023mar single-face detection, SFace 2021dec embeddings, and cosine matching. Test pairwise use first, then test the correct attendance pattern: one query against multiple enrollment references. Calibrate on early query captures under a 1% false-accept ceiling and test on later captures plus negative identities unseen during calibration.

### Result

The upstream pair threshold performed poorly. The 48-reference template protocol produced accuracy 0.9333, precision 1.0, recall 0.8667, observed FAR 0.0, ROC AUC 0.8909, and 9.0 ms/query over 270 test queries.

### Decision

Adopt YuNet + SFace as the default reference backend and use multi-sample enrollment. Preserve the legacy model only as a private baseline. Explicitly document that SFace's precise training-data provenance is incomplete and that the small, single-enrollee test cannot establish production biometric performance.

## Engineering Decision - Modern Architecture

### Options Considered

Legacy model wrapping, retraining, a cloud API, InsightFace/ArcFace, YuNet + SFace, and a non-biometric redesign.

### Chosen Approach

Build a local FastAPI application with a typed service layer, OpenCV backend, encrypted face templates, SQLite attendance records, fail-closed face policy, duplicate protection, and a camera-first interface. Keep non-biometric attendance as the recommended high-assurance fallback and state that liveness is not solved.

### Reason

This keeps the original verification research intent, materially improves privacy and engineering quality, is reproducible without publishing personal data, and has a measured path to a compact deployable demo.

## Engineering Checkpoint - Core Application

### Implemented

- OpenCV YuNet/SFace extraction with one-face, size, lighting, and blur gates.
- Fifty-frame enrollment with rejected-frame accounting.
- AES-256-GCM authenticated encryption, participant-bound additional data, and no raw image persistence.
- SQLite participant and attendance repositories with foreign keys, UTC timestamps, transactional idempotency, and a duplicate window.
- FastAPI enrollment, verification, deletion, health, and admin attendance routes.
- Local admin-token protection for enrollment, deletion, and attendance access; required idempotency header for verification.
- Camera-first responsive interface and CLI/model downloader.

### Validation

Fourteen automated tests pass with 85% statement coverage. Ruff and strict MyPy pass. A real-model end-to-end run accepted 48 of 50 enrollment images, verified a separate-session probe at 0.8212, wrote exactly one attendance event, suppressed an immediate duplicate, listed the event with admin authorization, and deleted the participant. Browser inspection at 390 × 844 found no horizontal overflow or console errors.

### Remaining Boundary

The system does not implement validated liveness detection or institutional identity/authentication. It is intentionally localhost-first and requires a second factor and authorization redesign before real classroom deployment.

## 2026-09-02 - Operational and Portfolio Hardening

### Implemented

- Made the JSON request logger safe for embedding applications by preserving existing root handlers and applying the privacy-safe formatter without clearing unrelated handlers.
- Added formatter tests that verify the allowlist and ensure exception messages, participant identifiers, and embedding fields do not enter log output.
- Completed the portfolio README, FYP evolution narrative, interview brief, and operator runbook.
- Marked data/model documentation, latency measurement, CI/container packaging, and security checks complete based on the recorded artifacts and current validation.

### Validation

- `uv run --extra dev pytest -q --cov=presenceguard --cov-report=term-missing`: 17 passed, 85% total statement coverage.
- Ruff check and format check passed.
- Strict MyPy passed.
- Bandit reported no findings.
- pip-audit reported no known vulnerabilities; the local package itself is not published to PyPI and is therefore skipped by the auditor.

### Boundary

The local repository is ready for review and a deliberate GitHub target decision. No remote repository was invented or pushed during this continuation. Historical face images, private attendance data, legacy weights, runtime databases, and secrets remain outside Git tracking.

## 2026-09-02 - GitHub Publication Checkpoint

### Result

- Inspected the authenticated account and existing repositories. `mmuazhr/hadir` is a separate QR-badge attendance product and is not the face-verification FYP repository.
- Confirmed that `mmuazhr/smart-attendance-face-verification` did not exist, then created it as a public portfolio repository.
- The initial push was rejected by GitHub because the stored OAuth token has `repo`, `read:org`, and `gist` but not `workflow`; GitHub requires that scope for a commit containing `.github/workflows/ci.yml`.

### Decision

Preserve the complete local history and CI workflow. Do not create a second squashed snapshot or silently omit CI. The next operator action is `gh auth refresh --hostname github.com --scopes workflow`, followed by a normal push and public-repository verification.
