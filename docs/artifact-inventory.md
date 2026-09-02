# Historical Artifact Inventory

This inventory records what was recovered from the private Google Drive archive. It intentionally excludes biometric images, participant names, raw attendance entries, model weights, notebook outputs that embed faces, and private Drive identifiers.

## Source Scope

The historical source consists of a top-level FYP folder plus related academic documents in its parent university folder. Google Drive remains the immutable source of record; working copies live under the Git-ignored `.private/` directory.

| Artifact group | Recovered contents | Role | Publication decision |
| --- | --- | --- | --- |
| Notebooks | Five substantial notebook variants plus one empty/untitled draft | Data collection, training, evaluation, webcam verification | Do not publish raw notebooks; preserve private copies and publish clean-room modules/documentation |
| Trained model | `siamesemodelv2.h5`, 155,886,704 bytes | Saved custom Siamese model | Do not publish; record checksum and architecture only |
| Checkpoint | TensorFlow checkpoint index plus approximately 467 MB of weights | Training recovery | Do not publish or duplicate unless needed for a targeted recovery attempt |
| Pair dataset | `anchor`, `positive`, and `negative` JPEG classes | One-person face verification experiment | Never publish; biometric research data with unverified consent scope |
| LFW tree | Identity-organised negative examples | Public-dataset-derived negatives | Do not republish; document upstream acquisition instead |
| Application data | Verification reference images and a captured input image | Webcam verification prototype | Never publish; biometric data |
| Attendance output | Small CSV containing names and times | Prototype output | Never publish; personally identifiable data |
| Application code | A 17-byte `newApp.py` and two tiny/empty ZIP artifacts | Intended Kivy/Firebase application | Insufficient to reconstruct the claimed full application |
| Thesis and reports | Final thesis, final report, technical report, proposal, updated proposal | Requirements and historical claims | Cite/summarise; do not republish wholesale |
| Presentation/pitch | Small slide deck and idea-pitch document | Early design/process context | Summarise only where relevant |
| Demo images | A few named face images | Manual demonstration | Never publish; biometric data |

## Dataset Audit

The recovered `data.zip` archive passed extraction and readability checks.

| Check | Result |
| --- | ---: |
| Total images | 1,378 |
| Anchor | 450 |
| Positive | 450 |
| Negative | 478 |
| Image format | 1,378 JPEG |
| Dimensions | 1,378 at 250 × 250 pixels |
| Colour mode | 1,378 RGB |
| Unreadable files | 0 |
| Exact duplicate groups | 12 |
| Extra files represented by those groups | 12 |
| Exact duplicates crossing class labels | 0 |

The archive structure does not encode the 30 participant identities described in the thesis. Anchor and positive images are timestamp-like UUID captures from a single webcam workflow, while negatives originate from LFW. Consequently, the recovered data supports a narrow enrolled-person verification experiment, not a 30-person recognition or demographic-generalisation claim.

## Integrity Records

- Saved model SHA-256: `2db778b1395529527e02f8e94b5b85433be478f759ffdbc551f0f4359ff8f0fe`
- Saved model size: 155,886,704 bytes
- Dataset audit is reproducible with `scripts/audit_dataset.py`.
- Notebook source and metadata extraction is reproducible with `scripts/summarize_notebook.py`.
- Model metadata extraction is reproducible with `scripts/inspect_legacy_model.py`.

## Missing or Unrecoverable Material

- The complete Kivy interface described in the thesis was not found.
- Firebase schema, security rules, and deployable configuration were not found.
- Participant-level labels for the claimed 30-person UKM cohort were not found.
- Consent forms, data sheets, model cards, and a documented data-retention policy were not found.
- An environment lockfile and deterministic random seeds were not found.
- The exact train/test membership used for reported thesis metrics was not saved.

These absences are treated as evidence limitations, not silently reconstructed facts.
