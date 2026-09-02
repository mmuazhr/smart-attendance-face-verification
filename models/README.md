# Model Card

## Default Pipeline

PresenceGuard uses two external ONNX artifacts downloaded from the official OpenCV Zoo:

| Role | Artifact | Size | SHA-256 | License stated by model directory |
| --- | --- | ---: | --- | --- |
| Detection and five-point landmarks | `face_detection_yunet_2023mar.onnx` | 232,589 bytes | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` | MIT |
| 128D face embedding | `face_recognition_sface_2021dec.onnx` | 38,696,353 bytes | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` | Apache-2.0 |

Run `presenceguard download-models`. The downloader uses fixed HTTPS URLs, verifies both checksums, and only then atomically installs the files. Binary weights are excluded from Git.

## Input and Output

YuNet accepts the decoded frame and returns bounding boxes, five landmarks, and confidence. PresenceGuard requires exactly one detection and applies size, brightness, and sharpness policies. SFace aligns the face and returns a normalized 128D embedding. Verification uses maximum cosine similarity against the encrypted enrollment references.

## Threshold

The project default is 0.554712, calibrated on the historical private dataset to maximize recall subject to a 1% false-accept ceiling. That threshold is evidence for this experiment only. Every real deployment must calibrate once on representative development data and then freeze the threshold before evaluating a held-out test set.

## Evaluation

The strongest reproducible protocol enrolled 50 frames from one session, of which 48 passed quality policy. Calibration used the first 315 queries of another session and development-only LFW identities. Testing used the last 135 queries plus 135 identity-disjoint LFW negatives: 93.3% accuracy, 100% precision, 86.7% recall, 0 observed false accepts, and ROC AUC 0.891.

This is one-enrollee evidence, not a production benchmark. It does not establish demographic fairness, liveness, classroom-scale throughput, or population false-accept probability.

## Provenance and Licensing Caveat

OpenCV Zoo states that all files in the SFace directory are Apache-2.0 licensed and identifies the architecture/loss, but the exact training dataset for this distributed ONNX weight is not fully documented. Redistributable code and checksums are provided; the weight itself is fetched from upstream. Commercial or high-risk use requires independent provenance, dataset-rights, and regulatory review.
