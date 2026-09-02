# Original Baseline Reconstruction

## Authoritative Implementation

The root `Final.ipynb` is treated as the latest historical implementation because it is the top-level notebook, has the fullest executed state, saves `siamesemodelv2.h5`, and its model configuration matches the supplied HDF5 file. Earlier notebook variants are retained privately as lineage evidence.

The saved model reports Keras 2.12.0 with a TensorFlow backend. Its HDF5 file contains model configuration and weights but no training configuration, so loading it does not restore the optimizer, loss, or metric state.

## Actual Model

The delivered implementation is a custom Siamese convolutional network, not FaceNet.

1. Two 100 × 100 RGB inputs share one embedding network.
2. The embedding network applies four valid-padded convolution layers with 64, 128, 128, and 256 filters.
3. Max pooling follows each of the first three convolutions.
4. A 9,216-value flattened representation feeds a 4,096-unit sigmoid layer.
5. A custom `L1Dist` layer computes absolute element-wise embedding differences.
6. A one-unit sigmoid classifier produces a similarity score.

The HDF5 weights contain 38,964,545 parameters. The 9,216 × 4,096 dense matrix alone holds 37,748,736 weights, making the model unusually large for the available dataset and deployment target.

Training code uses binary cross-entropy and Adam with learning rate 0.0001 for ten epochs. The saved HDF5 artifact does not include this training configuration.

## Actual Data Pipeline

The notebook independently asks TensorFlow to choose up to 300 anchor, 300 positive, and 300 negative paths. It forms 300 positive pairs by zipping anchor with positive and 300 negative pairs by reusing the same anchor dataset with negative. Images are decoded as JPEG, resized to 100 × 100, and divided by 255.

The resulting 600 pairs are cached, shuffled without a saved seed, and divided with `take(round(600 × 0.7))` and `skip(...)`. Therefore:

- the observed code uses a 70/30 pair split, not the thesis's stated 80/20 split;
- the same enrolled identity and likely the same capture sessions occur in both partitions;
- the shuffled order is not reproducible;
- exact duplicate captures can cross partitions;
- no identity-, participant-, or session-disjoint evaluation exists;
- the reported UKM demographic analysis cannot be derived from the recovered archive.

## Historical Outputs

The latest notebook's stored output reports training recall and precision of 1.0 and test recall and precision of 1.0. Another final-named variant reports test recall 0.9756098 and precision 1.0. Because random seeds and split membership were not saved, these outputs are historical observations rather than reproducible measurements.

The thesis separately reports:

| Evaluation | Accuracy | Precision | Recall |
| --- | ---: | ---: | ---: |
| UKM | 0.8086 | 0.7519 | 0.9741 |
| LFW | 0.8125 | 0.8222 | 1.0000 |
| LFW-trained, UKM-tested | 0.7344 | 0.6863 | 0.8633 |

No saved pair manifest or evaluation script connects those values to the supplied model. They will remain labelled “thesis-reported” unless independently reproduced.

## Runtime Reconstruction

The notebook kernel metadata records Python 3.9.13. Some commented setup cells request TensorFlow 2.4.1, while the actual model was saved by Keras 2.12.0. On the recovered Apple Silicon environment, TensorFlow 2.4.1 is not a viable native target; TensorFlow macOS 2.12.0 is the closest matching runtime for loading the supplied artifact.

## Verification and Attendance Behavior

The webcam prototype crops a fixed 250 × 250 region rather than detecting or aligning a face. Verification compares the captured image against every file in `application_data/verification_images`, counts scores above 0.5, and accepts when more than half of references pass. Thresholds are hard-coded and uncalibrated.

This procedure has no face-presence check, quality gate, liveness or replay defense, multi-face policy, calibrated false-accept target, or secure template storage. The small CSV is evidence of attendance output, but the recoverable code does not provide a complete attendance service.

## Reproduced Baseline

The saved model loads successfully under TensorFlow macOS 2.12.0. A deterministic analogue of the notebook's 300-per-class selection and 70/30 pair split produced 77.8% accuracy, 94.8% precision, 59.8% recall, and 3.4% false-accept rate at threshold 0.5 over 180 pairs.

A chronological probe over 270 pairs produced 98.9% accuracy, 98.5% precision, 99.3% recall, and 1.5% false-accept rate. This stronger number is not a clean generalisation result: the supplied model's original training membership is missing and may include probe images.

See `docs/results.md` and the aggregate JSON outputs for the complete metrics and limitations.
