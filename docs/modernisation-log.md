# Modernisation Log

## 2026-09-02 - Discovery

### Finding

The requested source path resolves to the Google Drive folder `ONEDRIVE UKM/FYP`. The archive contains:

- notebook generations including `Final.ipynb`, `FACIAL RECOGNITION.ipynb`, desktop and Siamese variants;
- `data.zip` plus `data/{anchor,positive,negative}` and an LFW tree;
- `siamesemodelv2.h5` and TensorFlow checkpoints;
- `application_data` verification/input folders;
- demo images and a four-row attendance CSV.

The parent `ONEDRIVE UKM` folder contains the final thesis, technical report, proposals, a small presentation, and two tiny FYP ZIPs.

### Evidence

- Final thesis title: *Sistem Kehadiran Pintar Menggunakan Teknik Pengecaman Wajah Berasaskan Pembelajaran Mendalam*.
- Author: Muhammad Muaz Husaini bin Rosli, A182954, Universiti Kebangsaan Malaysia, 2023.
- Thesis-reported evaluation:
  - UKM: accuracy 0.8086, precision 0.7519, recall 0.9741.
  - LFW: accuracy 0.8125, precision 0.8222, recall 1.0000.
  - Cross-domain: accuracy 0.7344, precision 0.6863, recall 0.8633.
- The attendance artifact records MUAZ, TARIQ, BULYA, and BILL with times only.

### Contradictions and Risks

- Thesis: 80/20 split and K-fold validation. Notebook: shuffled pair construction followed by a 70/30 `take/skip` split.
- Thesis: FaceNet feature extractor. Notebook: a custom CNN embedding trained from scratch; no FaceNet model is used in the inspected implementation.
- Thesis: full Kivy/Firebase system. Inspected FYP source is predominantly notebooks; the described application source is not yet located.
- Augmentation appears to occur before splitting, which can place transformed versions of the same source face in both train and test sets.
- Pair-level splitting allows the same captured identity/image family to appear across partitions and cannot support demographic generalisation claims.
- The UKM face dataset contains sensitive biometric data from human subjects; consent and publication rights are not established.

### Decision

Treat the thesis results as historical reported results, not independently validated evidence. Reconstruct the baseline faithfully, then evaluate a modern approach with entity-aware and source-aware separation. Keep all personal biometric material private and Git-ignored.

## 2026-09-02 - Dataset and Model Forensics

### Finding

The recovered pair dataset has 1,378 readable RGB JPEG files at 250 × 250 pixels: 450 anchor, 450 positive, and 478 negative. Twelve exact duplicate groups exist within classes; no exact duplicate crosses a class label.

The saved `siamesemodelv2.h5` file is 155,886,704 bytes with SHA-256 `2db778b1395529527e02f8e94b5b85433be478f759ffdbc551f0f4359ff8f0fe`. Its metadata identifies Keras 2.12.0 and a TensorFlow backend. It contains a 38,964,545-parameter custom Siamese network and no training configuration.

### Decision

Use TensorFlow macOS 2.12.0 to maximize compatibility with the saved artifact on Apple Silicon. Keep the model and all face data Git-ignored. Publish only reproducible audit tooling, aggregate counts, architecture metadata, and defensible benchmark results.

### Notebook Lineage

Five substantial notebook variants were recovered. The top-level `Final.ipynb` is the most complete executed version and matches the saved model. It is the baseline authority; other variants are evidence of iteration, not separate product implementations.

## Engineering Decision - Workspace

### Options Considered

1. Modify the Google Drive archive directly.
2. Work in the dated projectless conversation folder.
3. Create a persistent project under the established `Documents/Codex/projects` area.

### Chosen Approach

Create `Documents/Codex/projects/smart-attendance-face-verification`.

### Reason

It is persistent, clearly named from the actual FYP, separate from the immutable source archive, and suitable for Git/GitHub work.
