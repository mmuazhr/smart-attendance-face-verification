# Deep Audit and Improvement Backlog

## Executive Assessment

The original FYP chose a meaningful problem and demonstrated a complete machine-learning learning cycle: local data capture, pair construction, a Siamese network, webcam verification, and attendance output. Its strongest asset is the clear verification intent. Its weakest asset is evidence quality: the available code and data cannot support the thesis's multi-participant or demographic claims, and the random pair split substantially overstates generalization.

## P0 — Critical

| Finding | Evidence | Required response |
| --- | --- | --- |
| Biometric privacy is undefined | Raw face images, named demo photos, and attendance records are stored as ordinary files | Never publish historical data; avoid storing new images; encrypt templates; add deletion and retention controls |
| Evaluation leakage and non-reproducibility | Unseeded `list_files`, pair-level shuffle, 70/30 `take/skip`, duplicate captures, no saved manifest | Use deterministic manifests, capture-time separation, negative identity separation, and explicit limitations |
| Claimed method differs from code | Thesis describes FaceNet/triplet loss; artifact is a custom CNN/L1/sigmoid model | Document the contradiction and make executable code the authority for implementation claims |
| Authentication security is incomplete | No recoverable Firebase rules, secret handling, role enforcement, or deployable app | Build a local reference implementation with explicit authorization boundaries; do not claim production readiness |
| No liveness defense | A saved photo can plausibly satisfy the single-frame verifier | Label liveness as absent; require human supervision or a second factor for real use |

## P1 — High Impact

| Finding | Impact | Improvement |
| --- | --- | --- |
| Fixed crop, no detection/alignment | Pose and camera placement determine success | YuNet single-face detection plus five-landmark alignment |
| Uncalibrated 0.5 thresholds | Unknown false-accept and false-reject behavior | Calibration tool and deployment-specific threshold policy |
| 38.96M-parameter custom network | 156 MB artifact and about 61 ms per pair on the test machine | Compact pretrained 128D embeddings; about 39 MB recognizer and 0.23 MB detector |
| Single comparison as the research unit | Poor proxy for attendance enrollment | Multi-sample encrypted enrollment template with aggregate verification |
| CSV persistence | Race conditions, duplicates, weak auditability | SQLite transaction, idempotency key, duplicate window, UTC timestamps |
| Notebook-only implementation | Difficult to test, package, reuse, or deploy | Typed `src/` package, service layer, API, CLI, configuration, and tests |
| Missing failure policy | No-face, multi-face, and bad input paths are undefined | Typed rejection reasons with fail-closed behavior |

## P2 — Strong Portfolio Improvements

- Reproducible model acquisition with source, license, size, and SHA-256 verification.
- FastAPI reference API with a restrained camera-first interface.
- Encrypted template vault with no raw image retention.
- Structured JSON audit events without embeddings or face images.
- Architecture, evolution, model, data, security, and interview documentation.
- CI for linting, typing, tests, dependency audit, and secret scanning.
- Container and local quick-start paths.

## P3 — Nice to Have

- Platform authenticator or campus SSO as a second factor.
- Challenge-response liveness validated by a dedicated anti-spoof dataset.
- Lecturer dashboard, roster import, and signed attendance exports.
- Larger consented Malaysian cohort with subgroup error analysis.
- Hardware-specific ONNX quantization benchmark.

## Modernization Options

| Option | Accuracy evidence | Complexity | Privacy | Reproducibility | Portfolio value | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| Keep and wrap the legacy CNN | Strong contaminated artifact probe; no clean training split | Medium | Local, but large private weights | Poor without redistributable weights | Moderate | Preserve as historical baseline only |
| Retrain the legacy architecture | Dataset is insufficient for general recognition | High | Local | Possible but scientifically weak | Low | Reject |
| Cloud face API | Potentially strong | Low code, high operational dependency | Face data leaves device | Vendor-dependent | Low–moderate | Reject |
| InsightFace/ArcFace bundle | Strong public benchmarks | Medium | Local | Model licensing/training-data terms complicate redistribution | High technically | Do not use as default |
| YuNet + SFace | Best current result is 93.3% accuracy under a template protocol | Low–medium | Fully local | First-party OpenCV interfaces and checksummed weights | High | Chosen default, with provenance caveat |
| Non-biometric attendance only | Avoids biometric risk | Low | Strongest | Strong | Valuable but changes research intent | Provide as recommended deployment fallback, not the main FYP |

## Chosen Direction

Build PresenceGuard as a local, privacy-first face-verification reference system using YuNet detection, SFace embeddings, encrypted multi-sample templates, a transactional attendance domain, and a small FastAPI interface. Preserve the original verification objective while making the safety boundary explicit: this is a research/portfolio reference, not a claim of production biometric security.

The decision is based on the use-case-correct template experiment, not the poor pairwise SFace result. Fifty automatically captured enrollment frames yielded 48 usable references. With the threshold calibrated on the first 70% of a separate capture session under a 1% calibration false-accept ceiling, the last 30% plus identity-disjoint LFW negatives produced 93.3% accuracy, 100% precision, 86.7% recall, and 0% observed false accepts. The 270-query test is too small and narrow for production claims.
