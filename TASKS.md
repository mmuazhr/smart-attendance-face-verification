# Smart Attendance Face Verification - Modernisation Tasks

## Discovery

- [x] Locate and verify the source Google Drive archive.
- [x] Confirm the project identity from code and academic reports.
- [x] Inventory the top-level FYP folder and immediate subfolders.
- [x] Locate the final thesis, technical report, proposal, presentation, notebooks, dataset archive, trained model, checkpoints, demo images, and attendance output.
- [x] Complete a privacy-aware recursive inventory with counts, sizes, roles, relevance, and contradictions.
- [x] Extract the original notebook lineage and application requirements.
- [x] Inspect the original trained model metadata without publishing biometric data or large binaries.

## Original Baseline

- [x] Reconstruct the original environment and dependency constraints.
- [x] Extract the original architecture and data pipeline from the authoritative notebook.
- [x] Audit the original train/test split for leakage and entity overlap.
- [x] Attempt original-model loading and evaluation.
- [ ] Reproduce reported metrics where the available artifacts permit it.
- [x] Record precisely why any reported result cannot be reproduced.

## Audit

- [x] Audit data provenance, consent, privacy, labels, duplicates, imbalance, and demographic claims.
- [x] Audit model choice, objective, thresholds, calibration, and evaluation methodology.
- [x] Audit architecture, application code, persistence, security, and UX.
- [x] Produce a P0-P3 improvement backlog and compare modernisation options.

## Modernisation

- [x] Select the strongest direction while preserving the original research intent.
- [x] Implement a reproducible, privacy-preserving face-verification core.
- [x] Implement deterministic attendance-domain logic with duplicate and replay protection.
- [x] Add configuration, error handling, and typed interfaces.
- [x] Add a restrained camera-first demo interface and CLI.
- [x] Add structured privacy-safe logging.
- [x] Add data and model documentation with explicit ethical limitations.

## Validation

- [x] Add unit tests for preprocessing boundaries, verification, encryption, and attendance logging.
- [x] Add integration, API, private-model, and end-to-end smoke tests.
- [x] Benchmark the original baseline and modern alternative on defensible splits.
- [x] Measure latency and document hardware/runtime assumptions.
- [x] Run formatting, linting, type checking, tests, package/build checks, and security scans.

## Portfolio Documentation

- [x] Complete the portfolio-quality README.
- [x] Create docs/architecture.md.
- [x] Create docs/fyp-evolution.md.
- [x] Create docs/interview-brief.md.
- [x] Create data/README.md and model documentation.
- [ ] Add measured results and safe visual assets.

## Git and GitHub

- [ ] Initialise Git and establish a meaningful commit history.
- [ ] Confirm no pre-existing repository should be reused.
- [x] Scan history and working tree for secrets, personal data, biometric data, and oversized files.
- [x] Create or configure the GitHub repository.
- [ ] Push without rewriting existing history.
- [ ] Verify README rendering, links, repository description, topics, and published contents.

## Final Quality Gate

- [ ] All understanding, baseline, engineering, AI/data, validation, documentation, and GitHub checks in PROJECT_INSTRUCTIONS.md are satisfied or transparently documented as limitations.
