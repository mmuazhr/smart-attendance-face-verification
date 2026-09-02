# Current Project State

## Current Phase

Engineering hardening and portfolio packaging.

## Last Completed

Recovered and independently measured the legacy artifact, selected and implemented the local YuNet/SFace architecture, added privacy-safe persistence and API boundaries, and completed the core portfolio documentation.

## Currently Working On

Final local quality gate and GitHub handoff preparation. Publication remains pending because no repository target has been selected or authorized in this resumed task.

## Important Findings

- Project title: *Smart Attendance System Using Face Recognition Techniques Based on Deep Learning*.
- Original objective: analyse facial features and build a face-recognition model suitable for the Malaysian student demographic.
- Intended users: students recording class attendance, with lecturers benefiting from reduced manual work and less proxy attendance.
- Original ML core: a custom Siamese convolutional network comparing 100x100 RGB image pairs with an L1 distance layer and sigmoid classifier.
- Original application concept: Kivy client, webcam capture, Firebase/Pyrebase student records, face verification, and attendance history.
- The Drive implementation archive is notebook-centric; the complete application code described in the thesis is not yet present in the inspected FYP folder.
- The thesis reports UKM accuracy 0.8086, precision 0.7519, recall 0.9741; LFW accuracy 0.8125, precision 0.8222, recall 1.0000; and cross-domain accuracy 0.7344, precision 0.6863, recall 0.8633.
- The notebook code uses a random shuffled pair-level 70/30 split, while the thesis states 80/20 data splits and mentions K-fold validation. This contradiction is a major reproducibility and leakage concern.
- The source contains personal face images and attendance records. These are private research artifacts and must not be pushed to GitHub.
- The recovered dataset contains 1,378 readable 250x250 RGB JPEGs: 450 anchor, 450 positive, and 478 negative, with 12 within-class exact duplicate groups.
- The supplied HDF5 model is a Keras 2.12 Functional model with 38,964,545 parameters. It includes weights and architecture but no training configuration.
- The latest root notebook is the best-matching authoritative implementation. Its stored test output reports precision and recall of 1.0, but the split is unseeded and its membership was not preserved.

## Current Baseline

Legacy artifact independently reproduced. Deterministic replay: 77.8% accuracy; contaminated chronological probe: 98.9%. Chosen SFace multi-reference protocol: 93.3% accuracy, 100% precision, 86.7% recall, 0 observed false accepts over 270 test queries.

## Major Decisions

- Preserve Google Drive as the immutable historical source.
- Use this repository as the reconstructed and modernised implementation.
- Keep original biometric data, raw notebooks with embedded outputs, trained weights, and attendance records outside Git tracking.
- Do not accept the thesis metrics as a valid modern baseline until the split methodology and model provenance are verified.
- Use YuNet detection and SFace embeddings as the default modern backend, with checksummed external weights and a clear training-provenance caveat.
- Use multi-sample encrypted templates; do not persist raw enrollment or verification images.
- Treat absence of liveness as an explicit deployment limitation, not a solved feature.
- The modern application now supports admin-authorized enrollment, 50-frame quality-filtered capture, AES-GCM template encryption, local SFace verification, idempotent attendance writes, duplicate-window suppression, admin-only attendance reads, and participant deletion.
- The real private-artifact E2E run accepted 48/50 enrollment frames, verified a separate-session query at 0.8212, wrote one attendance record, suppressed the immediate duplicate, returned the admin attendance view, and deleted the participant.
- Automated suite: 17 tests pass with 85% package statement coverage after observability coverage was added; Ruff, strict MyPy, Bandit, and pip-audit pass. Browser QA at 390x844 shows no horizontal overflow or console errors.

## Known Blockers

The original application source may be missing, and no GitHub repository target is established. The biometric system still has no validated liveness detector or institutional authentication by design.

## Next Actions

1. Review the final diff and commit the local hardening/documentation checkpoint.
2. Decide on a GitHub repository target and authentication/publishing workflow.
3. If publishing is authorized, push without exposing private artifacts and verify the rendered repository.

## Last Verified

2026-09-02; local quality gates passed; repository is initialized on `main` with uncommitted hardening/documentation changes.
