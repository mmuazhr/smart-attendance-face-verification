# Interview Brief

Use this brief to explain PresenceGuard accurately and concisely. Keep the distinction between measured evidence and future work clear.

## 30-second explanation

“I modernised my university face-verification attendance project into PresenceGuard, a local FastAPI reference system. The original project used a custom Siamese CNN and a leaky notebook split. I retained the research question but replaced the runtime with YuNet detection and SFace embeddings, encrypted multi-sample templates, a transactional SQLite attendance domain, and a camera-first web interface. The strongest private-archive test reached 93.3% accuracy with zero observed false accepts, but I explicitly treat that as narrow one-person evidence because liveness, fairness, and production authentication are not solved.”

## Two-minute explanation

The original FYP aimed to reduce manual attendance and proxy attendance using face verification. I first reconstructed the archive instead of trusting the thesis summary. The executable notebook used a custom four-convolution Siamese network with an L1 distance layer, not the FaceNet pipeline described in the thesis. It also used a random pair-level split whose seed and membership were missing, so the historical metrics could not be treated as clean generalisation results.

I created a separate, Git-ignored workspace for the reconstruction. The modern system keeps the original verification intent but uses a compact local YuNet + SFace pipeline. Enrollment captures several quality-filtered frames, creates normalized embeddings, and encrypts them with AES-GCM. Verification requires exactly one face, compares a query against the reference template, and writes attendance only after a threshold match. SQLite transactions provide idempotency and duplicate-window protection.

I measured the legacy artifact at 77.8% accuracy under a deterministic replay. The modern multi-reference protocol reached 93.3% accuracy, 100% precision, 86.7% recall, and zero observed false accepts on a small source/session-aware test. The result is not a production claim: the archive represents one enrolled person, the original training manifest is missing, and the system has no validated liveness detector or institutional identity layer.

## Five-minute technical explanation

### Problem formulation

The useful unit for attendance is not an arbitrary image pair. It is a query frame compared against multiple enrollment references for one authorized participant, followed by an auditable attendance decision. That reframing drove the template protocol and the database design.

### Architecture

- Browser camera interface: ephemeral capture, consent prompt, and clear verification feedback.
- FastAPI boundary: upload type/size limits, response schemas, admin-token boundary, and request IDs.
- Face engine: YuNet detection, single-face policy, alignment, quality gates, and normalized SFace embedding.
- Enrollment service: consent, sample limits, rejection accounting, encryption, and template persistence.
- Verification service: template decryption, maximum cosine similarity, calibrated threshold, and attendance decision.
- SQLite repository: encrypted participant templates, UTC attendance events, foreign keys, idempotency, and duplicate suppression.
- Model downloader: fixed upstream URLs, SHA-256 verification, and atomic installation.

### Why these technologies?

YuNet and SFace provide a compact local pipeline with an explicit OpenCV interface and no biometric cloud dependency. FastAPI gives typed request/response boundaries and a small deployable surface. SQLite is sufficient for a localhost reference and provides transactions that a CSV cannot. AES-GCM provides confidentiality and integrity for the stored templates; it does not solve key management by itself.

### Hardest engineering problem

The hardest engineering problem was defining the privacy and attendance boundary. The system must accept an image long enough to extract a feature, but it should not create a face gallery. The solution is in-memory processing plus encrypted templates, followed by an atomic attendance write that handles retries and concurrent duplicate submissions.

### Hardest AI/data problem

The hardest AI problem was discovering that the original evidence did not support the strength of its claims. Pair-level randomization, missing split membership, exact duplicates, and absent participant labels make it impossible to claim demographic generalisation from the recovered archive. I therefore calibrated the modern threshold on development data and separated capture time and negative identity where the available data allowed.

### Trade-offs

- Local processing improves privacy and reproducibility but increases the operator's responsibility for model files and keys.
- Multi-sample templates improve robustness but still contain biometric data and require deletion/rotation policies.
- A strict single-face quality policy rejects ambiguous frames rather than guessing.
- SFace is compact and fast, but its exact training-data provenance and fairness properties need independent review.
- The app is intentionally localhost-first; network deployment requires a stronger identity and security architecture.

## Likely interview questions

### Why not keep the Siamese CNN?

I kept it as a private, reproducible historical baseline. The runtime artifact is large, its training manifest is missing, and the original evaluation protocol is uncertain. The modern pipeline is smaller and better aligned with one-query-to-template attendance verification.

### Did accuracy improve?

It depends on the protocol. The deterministic legacy replay was 77.8% accuracy; the selected modern template test was 93.3%. These are not a controlled retraining comparison because the legacy artifact's training membership is unknown and the datasets/protocols differ. I report the measurements with those caveats instead of claiming a universal improvement.

### How did you prevent biometric leakage?

I did not publish the historical images, attendance files, or legacy weights. In the application, raw uploads are not persisted. Stored templates are encrypted and participant-bound. The repository ignores private data, model binaries, secrets, and runtime databases, and CI includes source/dependency security checks.

### What happens if two requests arrive together?

The repository opens an immediate SQLite transaction, checks the unique idempotency key, checks the participant's duplicate window, and inserts at most one attendance row for the accepted request. A retry returns the original record; a different request inside the window returns a duplicate decision.

### Can a photo spoof it?

Yes, potentially. There is no validated presentation-attack detector. That is a deliberate documented limitation. A real deployment needs liveness or a different high-assurance factor, plus institutional authentication and operator oversight.

### What would you do next?

Collect a properly consented multi-subject dataset, freeze subject/session-disjoint manifests, evaluate subgroup error rates and calibration, add validated anti-spoofing, integrate campus SSO and managed keys, and provide a non-biometric fallback.

## Claims to avoid

Do not say the system is production-ready, liveness-secure, fair for Malaysian students, or proven to have zero false accepts. The measured claim is narrower: a local reference implementation works end to end and produced the documented result on a small private protocol.
