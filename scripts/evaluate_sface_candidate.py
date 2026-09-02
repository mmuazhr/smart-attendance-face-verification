#!/usr/bin/env python3
"""Evaluate the YuNet + SFace modernization candidate on private FYP data."""

from __future__ import annotations

import argparse
import json
import platform
import random
import time
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import cv2 as cv
import numpy as np

SEED = 42


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
    head, separator, tail = path.stem.rpartition("_")
    return head if separator and tail.isdigit() else path.stem


def legacy_replay(root: Path, seed: int = SEED) -> list[Pair]:
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
        candidates = sorted(by_identity[identities[cursor % len(identities)]])
        negatives.append(candidates[(cursor // len(identities)) % len(candidates)])
        cursor += 1
    pairs = [Pair(a, p, 1) for a, p in zip(anchors, positives, strict=False)]
    pairs.extend(Pair(a, n, 0) for a, n in zip(anchors, negatives, strict=False))
    rng.shuffle(pairs)
    return pairs


def calibrated_probe(root: Path, seed: int = SEED) -> tuple[list[Pair], list[Pair]]:
    """Create a calibration/test split separated by capture time and negative identity."""

    anchors = sorted(_files(root, "anchor"), key=_uuid_time)
    positives = sorted(_files(root, "positive"), key=_uuid_time)
    boundary = round(min(len(anchors), len(positives)) * 0.7)
    dev_anchors, test_anchors = anchors[:boundary], anchors[boundary:]
    dev_positives, test_positives = positives[:boundary], positives[boundary:]

    by_identity: dict[str, list[Path]] = {}
    for path in _files(root, "negative"):
        by_identity.setdefault(_negative_identity(path), []).append(path)
    identities = sorted(by_identity)
    rng = random.Random(seed)
    rng.shuffle(identities)
    test_identities: set[str] = set()
    test_file_count = 0
    for identity in identities:
        if test_file_count >= len(test_anchors):
            break
        test_identities.add(identity)
        test_file_count += len(by_identity[identity])
    test_negatives = [
        path
        for identity in identities
        if identity in test_identities
        for path in by_identity[identity]
    ]
    dev_negatives = [
        path
        for identity in identities
        if identity not in test_identities
        for path in by_identity[identity]
    ]
    rng.shuffle(test_negatives)
    rng.shuffle(dev_negatives)

    if len(test_negatives) < len(test_anchors) or len(dev_negatives) < len(dev_anchors):
        raise RuntimeError("Negative identity split does not contain enough files")

    dev = [Pair(a, p, 1) for a, p in zip(dev_anchors, dev_positives, strict=False)]
    dev.extend(Pair(a, n, 0) for a, n in zip(dev_anchors, dev_negatives, strict=False))
    test = [Pair(a, p, 1) for a, p in zip(test_anchors, test_positives, strict=False)]
    test.extend(Pair(a, n, 0) for a, n in zip(test_anchors, test_negatives, strict=False))
    rng.shuffle(dev)
    rng.shuffle(test)
    return dev, test


def template_protocol(
    root: Path, enrollment_samples: int = 50, seed: int = SEED
) -> tuple[list[Path], list[Path], list[Path], list[Path], list[Path]]:
    """Build enrollment, calibration, and test sets for one-to-template verification."""

    enrollment_pool = sorted(_files(root, "positive"), key=_uuid_time)
    indices = np.linspace(0, len(enrollment_pool) - 1, enrollment_samples, dtype=int)
    enrollment = [enrollment_pool[index] for index in indices]

    anchors = sorted(_files(root, "anchor"), key=_uuid_time)
    boundary = round(len(anchors) * 0.7)
    dev_positive, test_positive = anchors[:boundary], anchors[boundary:]

    by_identity: dict[str, list[Path]] = {}
    for path in _files(root, "negative"):
        by_identity.setdefault(_negative_identity(path), []).append(path)
    identities = sorted(by_identity)
    rng = random.Random(seed)
    rng.shuffle(identities)
    test_identities: set[str] = set()
    test_file_count = 0
    for identity in identities:
        if test_file_count >= len(test_positive):
            break
        test_identities.add(identity)
        test_file_count += len(by_identity[identity])
    dev_negative = [
        path
        for identity in identities
        if identity not in test_identities
        for path in by_identity[identity]
    ]
    test_negative = [
        path
        for identity in identities
        if identity in test_identities
        for path in by_identity[identity]
    ]
    rng.shuffle(dev_negative)
    random.Random(seed + 1).shuffle(test_negative)
    return (
        enrollment,
        dev_positive,
        dev_negative[: len(dev_positive)],
        test_positive,
        test_negative[: len(test_positive)],
    )


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
    positive_count = int(positives.sum())
    negative_count = int((~positives).sum())
    return float(
        (ranks[positives].sum() - positive_count * (positive_count + 1) / 2)
        / (positive_count * negative_count)
    )


def _metrics(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, float | int]:
    predicted = scores >= threshold
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


class SFaceEngine:
    def __init__(self, detector_path: Path, recognizer_path: Path, detection_threshold: float):
        self._detector = cv.FaceDetectorYN.create(
            str(detector_path), "", (250, 250), detection_threshold, 0.3, 5000
        )
        self._recognizer = cv.FaceRecognizerSF.create(str(recognizer_path), "")
        self._cache: dict[Path, np.ndarray | None] = {}

    def feature(self, path: Path) -> np.ndarray | None:
        if path in self._cache:
            return self._cache[path]
        image = cv.imread(str(path), cv.IMREAD_COLOR)
        if image is None:
            self._cache[path] = None
            return None
        self._detector.setInputSize((image.shape[1], image.shape[0]))
        _, faces = self._detector.detect(image)
        if faces is None or len(faces) != 1:
            self._cache[path] = None
            return None
        aligned = self._recognizer.alignCrop(image, faces[0])
        feature = self._recognizer.feature(aligned).reshape(-1)
        self._cache[path] = feature
        return feature

    def score(self, left: Path, right: Path) -> tuple[float, bool]:
        left_feature = self.feature(left)
        right_feature = self.feature(right)
        if left_feature is None or right_feature is None:
            return -1.0, False
        score = self._recognizer.match(
            left_feature.reshape(1, -1),
            right_feature.reshape(1, -1),
            cv.FaceRecognizerSF_FR_COSINE,
        )
        return float(score), True


def _evaluate(
    engine: SFaceEngine, pairs: Iterable[Pair], threshold: float
) -> dict[str, float | int]:
    pair_list = list(pairs)
    started = time.perf_counter()
    scored = [engine.score(pair.left, pair.right) for pair in pair_list]
    elapsed = time.perf_counter() - started
    scores = np.asarray([item[0] for item in scored])
    labels = np.asarray([pair.label for pair in pair_list])
    return {
        **_metrics(labels, scores, threshold),
        "face_detection_failed_pairs": sum(not detected for _, detected in scored),
        "inference_seconds": elapsed,
        "milliseconds_per_pair_amortized": elapsed * 1000 / len(pair_list),
    }


def _raw_scores(engine: SFaceEngine, pairs: list[Pair]) -> tuple[np.ndarray, np.ndarray]:
    scored = [engine.score(pair.left, pair.right)[0] for pair in pairs]
    return np.asarray([pair.label for pair in pairs]), np.asarray(scored)


def _template_scores(
    engine: SFaceEngine, references: np.ndarray, paths: list[Path]
) -> tuple[np.ndarray, int, float]:
    started = time.perf_counter()
    scores: list[float] = []
    failed = 0
    for path in paths:
        feature = engine.feature(path)
        if feature is None:
            scores.append(-1.0)
            failed += 1
            continue
        normalized = feature / np.linalg.norm(feature)
        scores.append(float(np.max(references @ normalized)))
    return np.asarray(scores), failed, time.perf_counter() - started


def _calibrate_threshold(
    labels: np.ndarray, scores: np.ndarray, maximum_false_accept_rate: float
) -> tuple[float, dict[str, float | int]]:
    candidates = np.unique(scores)
    candidates = np.concatenate(
        ([float(candidates.min()) - 1e-6], candidates, [float(candidates.max()) + 1e-6])
    )
    eligible: list[tuple[float, dict[str, float | int]]] = []
    for candidate in candidates:
        metrics = _metrics(labels, scores, float(candidate))
        if float(metrics["false_accept_rate"]) <= maximum_false_accept_rate:
            eligible.append((float(candidate), metrics))
    if not eligible:
        raise RuntimeError("No threshold satisfies the false-accept policy")
    return max(
        eligible,
        key=lambda item: (
            float(item[1]["recall"]),
            float(item[1]["accuracy"]),
            float(item[0]),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--detector", type=Path, required=True)
    parser.add_argument("--recognizer", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--detection-threshold", type=float, default=0.9)
    parser.add_argument("--match-threshold", type=float, default=0.363)
    args = parser.parse_args()

    engine = SFaceEngine(args.detector, args.recognizer, args.detection_threshold)
    protocols = {
        "legacy_replay": legacy_replay(args.data),
        "chronological_probe": chronological_probe(args.data),
    }
    calibration_pairs, calibrated_test_pairs = calibrated_probe(args.data)
    calibration_labels, calibration_scores = _raw_scores(engine, calibration_pairs)
    calibrated_threshold, calibration_metrics = _calibrate_threshold(
        calibration_labels, calibration_scores, maximum_false_accept_rate=0.01
    )
    enrollment, dev_positive, dev_negative, test_positive, test_negative = template_protocol(
        args.data
    )
    reference_features = [engine.feature(path) for path in enrollment]
    normalized_references = np.stack(
        [feature / np.linalg.norm(feature) for feature in reference_features if feature is not None]
    )
    dev_positive_scores, dev_positive_failed, dev_positive_seconds = _template_scores(
        engine, normalized_references, dev_positive
    )
    dev_negative_scores, dev_negative_failed, dev_negative_seconds = _template_scores(
        engine, normalized_references, dev_negative
    )
    template_dev_labels = np.concatenate(
        (np.ones(len(dev_positive), dtype=int), np.zeros(len(dev_negative), dtype=int))
    )
    template_dev_scores = np.concatenate((dev_positive_scores, dev_negative_scores))
    template_threshold, template_calibration_metrics = _calibrate_threshold(
        template_dev_labels, template_dev_scores, maximum_false_accept_rate=0.01
    )
    test_positive_scores, test_positive_failed, test_positive_seconds = _template_scores(
        engine, normalized_references, test_positive
    )
    test_negative_scores, test_negative_failed, test_negative_seconds = _template_scores(
        engine, normalized_references, test_negative
    )
    template_test_labels = np.concatenate(
        (np.ones(len(test_positive), dtype=int), np.zeros(len(test_negative), dtype=int))
    )
    template_test_scores = np.concatenate((test_positive_scores, test_negative_scores))
    result = {
        "schema_version": 1,
        "seed": SEED,
        "candidate": {
            "detector": "YuNet 2023mar",
            "recognizer": "SFace 2021dec",
            "opencv_version": cv.__version__,
            "detector_bytes": args.detector.stat().st_size,
            "recognizer_bytes": args.recognizer.stat().st_size,
        },
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor() or platform.machine(),
        },
        "limitations": [
            "Original model training membership was not preserved, so comparisons are artifact-level probes.",
            "The recovered archive represents one enrolled person plus LFW negatives, not the thesis's 30-person cohort.",
            "The fixed SFace threshold is an upstream default and must be calibrated for a real deployment population.",
            "SFace weight training-data provenance is not fully documented in the OpenCV Zoo model card.",
        ],
        "protocols": {
            name: _evaluate(engine, pairs, args.match_threshold)
            for name, pairs in protocols.items()
        },
        "calibrated_protocol": {
            "policy": "Maximize calibration recall subject to false-accept rate <= 1%.",
            "capture_split": "First 70% for calibration; last 30% for test, ordered by UUIDv1 capture time.",
            "negative_split": "Deterministic 70/30 identity-disjoint LFW partition.",
            "calibration": calibration_metrics,
            "test": _evaluate(engine, calibrated_test_pairs, calibrated_threshold),
        },
        "template_protocol": {
            "policy": "Maximum similarity across enrollment references; calibration recall maximized subject to false-accept rate <= 1%.",
            "enrollment": {
                "requested_samples": len(enrollment),
                "accepted_samples": len(normalized_references),
                "source": "One separate positive capture session, sampled evenly by capture time.",
            },
            "capture_split": "One anchor capture session split chronologically: first 70% for calibration, last 30% for test.",
            "negative_split": "Deterministic identity-disjoint LFW calibration/test partition.",
            "calibration": {
                **template_calibration_metrics,
                "face_detection_failed_queries": dev_positive_failed + dev_negative_failed,
                "inference_seconds": dev_positive_seconds + dev_negative_seconds,
            },
            "test": {
                **_metrics(template_test_labels, template_test_scores, template_threshold),
                "face_detection_failed_queries": test_positive_failed + test_negative_failed,
                "inference_seconds": test_positive_seconds + test_negative_seconds,
                "milliseconds_per_query_amortized": (
                    (test_positive_seconds + test_negative_seconds)
                    * 1000
                    / len(template_test_labels)
                ),
            },
        },
        "unique_images_processed": len(engine._cache),
        "unique_images_rejected_by_face_policy": sum(
            feature is None for feature in engine._cache.values()
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
