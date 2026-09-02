# Reproduced Results

All values below were produced on 2026-09-02 on an Apple Silicon Mac running macOS 26.6.2. Raw images, embeddings, individual scores, and participant identifiers remain private.

## Artifact-Level Comparison

| Model/protocol | Samples | Accuracy | Precision | Recall | FAR | ROC AUC | Runtime |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Legacy CNN, deterministic replay, threshold 0.5 | 180 pairs | 77.8% | 94.8% | 59.8% | 3.4% | 0.968 | 61.4 ms/pair |
| Legacy CNN, chronological probe, threshold 0.5 | 270 pairs | 98.9% | 98.5% | 99.3% | 1.5% | 1.000 | 57.9 ms/pair |
| SFace, pairwise replay, upstream threshold 0.363 | 180 pairs | 59.4% | 100% | 20.7% | 0% | 0.790 | Not comparable after cache warm-up |
| SFace, calibrated one-to-one chronological probe | 270 pairs | 50.0% | 50.0% | 4.4% | 4.4% | 0.731 | Not comparable after cache warm-up |
| SFace, calibrated 48-reference template protocol | 270 queries | **93.3%** | **100%** | **86.7%** | **0%** | 0.891 | **9.0 ms/query** |

The pairwise SFace experiments are retained because negative results matter: a generic embedding plus an upstream threshold is not automatically suitable for these pose-heavy, low-resolution images. The attendance workflow improves when it is modeled correctly as one query against a multi-sample enrollment template.

## Template Protocol

- Enrollment: 50 evenly sampled frames from one capture session; 48 passed the strict single-face policy.
- Calibration positives: first 315 frames of a separate capture session.
- Test positives: last 135 frames from that separate session.
- Negatives: LFW identities split deterministically so calibration and test identities do not overlap.
- Score: maximum cosine similarity across encrypted enrollment references.
- Threshold: 0.554712, chosen on calibration data to maximize recall subject to false-accept rate ≤ 1%.
- Test confusion matrix: 117 true accepts, 135 true rejects, 0 false accepts, 18 false rejects.

## What Can and Cannot Be Claimed

The supplied legacy model may have trained on images present in both legacy probes because its training manifest is missing. Its 98.9% chronological result therefore cannot be interpreted as unseen-data generalization.

The SFace template test separates enrollment and query capture sources, separates query time, and prevents negative identity overlap between calibration and test. It is stronger evidence, but still covers one enrolled person and only 135 positive test queries. It does not establish fairness, spoof resistance, classroom-scale performance, or a reliable population false-accept rate.

Machine-readable aggregate outputs are available in `results/legacy-baseline.json` and `results/sface-candidate.json`.
