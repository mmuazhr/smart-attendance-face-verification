#!/usr/bin/env python3
"""Evaluate the private legacy model with reproducible aggregate protocols.

No image paths, identities, embeddings, or individual predictions are written to
the public result. The model and source dataset must remain under `.private/`.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import random
import time
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf

SEED = 42


class L1Dist(tf.keras.layers.Layer):
    """Compatibility implementation for the notebook's custom distance layer."""

    def call(self, input_embedding: tf.Tensor, validation_embedding: tf.Tensor) -> tf.Tensor:
        return tf.math.abs(input_embedding - validation_embedding)


@dataclass(frozen=True)
class Pair:
    left: Path
    right: Path
    label: int


def _files(root: Path, class_name: str) -> list[Path]:
    return sorted((root / class_name).glob("*.jpg"))


def _uuid_time(path: Path) -> int:
    return uuid.UUID(path.stem).time


def _negative_identity(path: Path) -> str:
    stem = path.stem
    head, separator, tail = stem.rpartition("_")
    return head if separator and tail.isdigit() else stem


def legacy_replay(root: Path, seed: int = SEED) -> list[Pair]:
    """Deterministic analogue of list_files().take(300), shuffle, and 70/30 split."""

    rng = random.Random(seed)
    anchors = _files(root, "anchor")
    positives = _files(root, "positive")
    negatives = _files(root, "negative")
    rng.shuffle(anchors)
    rng.shuffle(positives)
    rng.shuffle(negatives)
    anchors, positives, negatives = anchors[:300], positives[:300], negatives[:300]
    pairs = [Pair(a, p, 1) for a, p in zip(anchors, positives, strict=False)]
    pairs.extend(Pair(a, n, 0) for a, n in zip(anchors, negatives, strict=False))
    rng.shuffle(pairs)
    return pairs[round(len(pairs) * 0.7) :]


def chronological_probe(root: Path, seed: int = SEED) -> list[Pair]:
    """Later-capture probe with negative identities sampled deterministically.

    This is a stress test, not a leakage-free test: the supplied model's original
    training membership was not preserved.
    """

    anchors = sorted(_files(root, "anchor"), key=_uuid_time)
    positives = sorted(_files(root, "positive"), key=_uuid_time)
    holdout = round(min(len(anchors), len(positives)) * 0.3)
    anchors = anchors[-holdout:]
    positives = positives[-holdout:]

    by_identity: dict[str, list[Path]] = {}
    for path in _files(root, "negative"):
        by_identity.setdefault(_negative_identity(path), []).append(path)
    identities = sorted(by_identity)
    rng = random.Random(seed)
    rng.shuffle(identities)
    negatives: list[Path] = []
    cursor = 0
    while len(negatives) < holdout:
        identity = identities[cursor % len(identities)]
        candidates = sorted(by_identity[identity])
        negatives.append(candidates[(cursor // len(identities)) % len(candidates)])
        cursor += 1

    pairs = [Pair(a, p, 1) for a, p in zip(anchors, positives, strict=False)]
    pairs.extend(Pair(a, n, 0) for a, n in zip(anchors, negatives, strict=False))
    rng.shuffle(pairs)
    return pairs


def _decode(path: Path) -> tf.Tensor:
    image = tf.io.decode_jpeg(tf.io.read_file(str(path)), channels=3)
    image = tf.image.resize(image, (100, 100))
    return tf.cast(image, tf.float32) / 255.0


def _scores(
    model: tf.keras.Model, pairs: Iterable[Pair], batch_size: int
) -> tuple[np.ndarray, float]:
    pair_list = list(pairs)
    started = time.perf_counter()
    values: list[np.ndarray] = []
    for offset in range(0, len(pair_list), batch_size):
        batch = pair_list[offset : offset + batch_size]
        left = tf.stack([_decode(pair.left) for pair in batch])
        right = tf.stack([_decode(pair.right) for pair in batch])
        values.append(model.predict([left, right], verbose=0).reshape(-1))
    elapsed = time.perf_counter() - started
    return np.concatenate(values), elapsed


def _auc(labels: np.ndarray, scores: np.ndarray) -> float:
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=float)
    cursor = 0
    while cursor < len(scores):
        end = cursor + 1
        while end < len(scores) and scores[order[end]] == scores[order[cursor]]:
            end += 1
        ranks[order[cursor:end]] = (cursor + 1 + end) / 2
        cursor = end
    positives = labels == 1
    n_positive = int(positives.sum())
    n_negative = int((~positives).sum())
    return float(
        (ranks[positives].sum() - n_positive * (n_positive + 1) / 2) / (n_positive * n_negative)
    )


def _metrics(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, float | int]:
    predicted = scores > threshold
    positive = labels == 1
    tp = int(np.sum(predicted & positive))
    tn = int(np.sum(~predicted & ~positive))
    fp = int(np.sum(predicted & ~positive))
    fn = int(np.sum(~predicted & positive))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "samples": len(labels),
        "positive_pairs": int(positive.sum()),
        "negative_pairs": int((~positive).sum()),
        "threshold": threshold,
        "accuracy": (tp + tn) / len(labels),
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "specificity": tn / (tn + fp) if tn + fp else 0.0,
        "false_accept_rate": fp / (fp + tn) if fp + tn else 0.0,
        "false_reject_rate": fn / (fn + tp) if fn + tp else 0.0,
        "roc_auc": _auc(labels, scores),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "score_min": float(scores.min()),
        "score_max": float(scores.max()),
        "positive_score_mean": float(scores[positive].mean()),
        "negative_score_mean": float(scores[~positive].mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    np.random.seed(SEED)
    tf.random.set_seed(SEED)
    model = tf.keras.models.load_model(
        args.model,
        custom_objects={"L1Dist": L1Dist},
        compile=False,
    )

    result: dict[str, object] = {
        "schema_version": 1,
        "seed": SEED,
        "model": {
            "name": model.name,
            "parameters": model.count_params(),
            "keras_version": tf.keras.__version__,
            "tensorflow_version": tf.__version__,
        },
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor() or platform.machine(),
            "batch_size": args.batch_size,
        },
        "limitations": [
            "Original random seeds and train/test membership were not preserved.",
            "The supplied model may have trained on images used by both aggregate protocols.",
            "The recovered archive does not contain participant labels for the thesis's 30-person cohort.",
            "Results characterize this artifact and archive only; they do not establish demographic generalization.",
        ],
        "protocols": {},
    }

    protocols = {
        "legacy_replay": legacy_replay(args.data),
        "chronological_probe": chronological_probe(args.data),
    }
    for name, pairs in protocols.items():
        scores, elapsed = _scores(model, pairs, args.batch_size)
        labels = np.asarray([pair.label for pair in pairs])
        result["protocols"][name] = {
            **_metrics(labels, scores, args.threshold),
            "inference_seconds": elapsed,
            "milliseconds_per_pair": elapsed * 1000 / len(pairs),
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
