# From FYP to PresenceGuard

This document explains how the 2023 face-verification FYP became a modern, reproducible reference project. It separates historical evidence from newly measured behaviour and keeps the original research intent traceable.

## Original system

The FYP explored whether a deep-learning face-verification model could reduce manual classroom attendance and proxy attendance. The recovered implementation was notebook-centric:

- a custom Siamese CNN accepted two 100 × 100 RGB images;
- a shared convolutional branch produced an embedding;
- an L1 distance layer and sigmoid classifier returned a similarity score;
- a webcam prototype captured a fixed 250 × 250 crop;
- verification compared a query against reference images and wrote attendance-like output;
- the thesis described a Kivy/Firebase application, although the complete application source was not recovered.

The delivered HDF5 model contains 38,964,545 parameters and was saved by Keras/TensorFlow 2.12. The thesis refers to FaceNet and K-fold validation, but the executable notebook uses a custom CNN and an unseeded shuffled pair split. Those contradictions are preserved as historical findings rather than silently corrected in the record.

## Problems discovered

### Research evidence

The pair-level 70/30 split does not separate participants, capture sessions, or source image families. Augmentation appears before splitting, and the random seed and membership were not saved. Exact duplicates exist within classes. The archive also lacks the participant-level labels and consent evidence needed to substantiate the thesis's Malaysian demographic claims.

### Model and product

The custom network is large for the available data and deployment target. The fixed crop has no face-presence or multi-face policy. The 0.5 threshold is hard-coded rather than calibrated against a false-accept objective. A CSV-style attendance output does not provide transactional idempotency, duplicate protection, or a clear retention boundary.

### Privacy and operations

The source contains raw face images, attendance records, and a trained model. The original archive does not establish a publishable data license, key lifecycle, authentication design, liveness policy, or deployable environment.

## Options considered

1. Wrap the legacy CNN: preserves the artifact but inherits its size, provenance, split, and preprocessing uncertainty.
2. Retrain the legacy network: technically possible, but the recovered data is too narrow to support a sound recognition claim.
3. Use a cloud face API: reduces local implementation work but sends biometric data to a vendor and weakens research reproducibility.
4. Use a modern local embedding pipeline: keeps the face-verification question while reducing the model surface and enabling a clear template protocol.
5. Remove biometrics entirely: strongest deployment privacy, but it would no longer be a faithful modernisation of the FYP research intent.

The chosen direction is the fourth option, with non-biometric attendance documented as the recommended high-assurance fallback.

## Improvements implemented

| Traceability | Change |
| --- | --- |
| Fixed crop → pose-sensitive failures | YuNet single-face detection, landmark alignment, size/brightness/sharpness gates |
| Pair comparison → attendance enrollment | 3–50 quality-filtered samples stored as one encrypted template |
| Raw reference files → privacy boundary | AES-256-GCM encrypted embeddings; frames are not persisted |
| Hard-coded threshold → explicit policy | Deployment threshold stored with the template and calibrated on development data |
| CSV writes → attendance domain | SQLite, UTC timestamps, foreign keys, unique request IDs, transaction locking, and duplicate window |
| Notebook scripts → maintainable software | Typed services, configuration, FastAPI routes, CLI, model downloader, tests, CI, and container packaging |
| Silent failure → fail closed | Stable error codes for no face, multiple faces, low quality, invalid media, missing models, and unauthorized admin actions |
| Uncontrolled logs → privacy-safe telemetry | JSON request logs with route templates, status, duration, and no biometric or identity fields |

## Evidence

The legacy artifact loaded successfully under its matching TensorFlow/Keras runtime. A deterministic replay of the notebook-like protocol achieved 77.8% accuracy, 94.8% precision, 59.8% recall, and 3.4% false-accept rate over 180 pairs. A chronological probe achieved 98.9% accuracy, but it is potentially contaminated because the training manifest is missing.

The selected YuNet + SFace template protocol enrolled 48 usable samples from 50 captured frames. With a threshold calibrated on an earlier portion of a separate session and identity-disjoint LFW negatives, the held-out probe achieved 93.3% accuracy, 100% precision, 86.7% recall, and zero observed false accepts over 270 queries, at 9.0 ms/query on the recorded Apple Silicon run.

These results are useful for engineering comparison, not population assurance. The modern test covers one enrolled person and a small negative sample; it does not establish fairness, liveness, or classroom-scale performance.

## Current architecture

PresenceGuard is a local modular monolith. The browser or CLI calls FastAPI; the service layer validates the request and delegates face extraction to YuNet/SFace; the template cipher protects embeddings; SQLite records only encrypted templates and attendance events. Admin-only operations use a local token, and verification uses an idempotency key.

The architecture, data model, trust boundaries, and deployment flow are documented in [`architecture.md`](architecture.md). The privacy model and residual risks are in [`security.md`](security.md).

## What remains intentionally unsolved

- presentation-attack detection/liveness;
- institutional identity and role-based authorization;
- automatic key rotation and managed secrets;
- large, consented, subject-disjoint Malaysian evaluation data;
- the original thesis's exact split and metric reproduction;
- a claim that 0 observed false accepts equals zero real-world risk.

The correct next step is to expand the evidence and safety controls, not to hide these limits behind a more elaborate model.
