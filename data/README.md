# Data Card

## Public Repository Data

No face images, embeddings, participant rosters, or attendance records are included. Tests use tiny synthetic vectors and byte labels through a fake face engine.

## Historical Private Dataset

The recovered FYP archive contains 1,378 readable 250 × 250 RGB JPEG files: 450 anchor, 450 positive, and 478 negative. Twelve exact duplicate groups were found within classes; no exact duplicate crossed labels. Anchor and positive represent one enrolled person captured in two short webcam sessions. Negatives are selected LFW images spanning 244 filename-derived identities.

The archive does not contain participant-level labels for the 30-person UKM cohort described in the thesis. Consent scope, retention permission, and publication rights are not documented. It must therefore remain private and cannot support population or demographic claims.

## Intended Schema for New Evaluation Data

Any future consented dataset should keep an out-of-Git manifest with:

- pseudonymous subject ID;
- capture session ID and UTC date;
- source/device and environment;
- consent version and permitted uses;
- demographic attributes only when ethically justified and voluntarily supplied;
- quality flags and rejection reason;
- cryptographic file hash;
- split assignment generated at subject/session level.

Training, calibration, and test partitions must be subject-disjoint for recognition research. For enrolled-person verification, enrollment and query capture sessions must be separated, negative identities must not cross calibration/test, and test data must not tune the threshold.

## Reproduction

Place authorized private files under `data/private/` or `.private/`; both are Git-ignored. Run `scripts/audit_dataset.py` to reproduce aggregate integrity checks. Never commit its path-level output because filenames may be identifying.
