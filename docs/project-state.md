# Current Project State

## Current Phase

Discovery and baseline reconstruction.

## Last Completed

Located the historical archive and academic documentation, identified the project, confirmed that no matching GitHub repository exists, and created the persistent local workspace.

## Currently Working On

Implementing the selected privacy-first YuNet/SFace application architecture.

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

## Known Blockers

None at this phase. The original application source may be missing, but model and research reconstruction can continue.

## Next Actions

1. Implement the typed face, template-vault, attendance, and verification services.
2. Add FastAPI endpoints, a restrained camera interface, and model download tooling.
3. Add unit, integration, API, and model smoke tests.
4. Complete documentation, container, CI, security scans, and GitHub publishing.

## Last Verified

2026-09-02; repository not yet initialised.
