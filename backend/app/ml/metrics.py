from __future__ import annotations

import numpy as np


def clip01(x: np.ndarray) -> np.ndarray:
    return np.clip(x.astype(float), 0.0, 1.0)


def brier(y_true: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean((clip01(p) - y_true.astype(float)) ** 2))


def roc_auc(y_true: np.ndarray, p: np.ndarray) -> float:
    y = y_true.astype(int)
    p = clip01(p)
    pos = p[y == 1]
    neg = p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")

    scores = np.concatenate([pos, neg])
    ranks = scores.argsort().argsort().astype(float) + 1.0
    ranks_pos = ranks[: len(pos)]
    n_pos = len(pos)
    n_neg = len(neg)
    u = ranks_pos.sum() - n_pos * (n_pos + 1) / 2
    return float(u / (n_pos * n_neg))


def risk_any(ps: np.ndarray) -> float:
    ps = clip01(ps)
    return float(1.0 - np.prod(1.0 - ps))


def horizon_labels(y: np.ndarray, h: int) -> np.ndarray:
    n = len(y)
    out = np.zeros(n, dtype=int)
    for i in range(n):
        j = min(n, i + h)
        out[i] = 1 if np.any(y[i:j] == 1) else 0
    return out


def logloss(y_true: np.ndarray, p: np.ndarray, eps: float = 1e-12) -> float:
    y = y_true.astype(int)
    p = np.clip(p.astype(float), eps, 1 - eps)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def confusion(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, int]:
    y = y_true.astype(int)
    yp = y_pred.astype(int)
    tp = int(np.sum((y == 1) & (yp == 1)))
    tn = int(np.sum((y == 0) & (yp == 0)))
    fp = int(np.sum((y == 0) & (yp == 1)))
    fn = int(np.sum((y == 1) & (yp == 0)))
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn}


def precision_recall_f1(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    c = confusion(y_true, y_pred)
    tp, fp, fn, tn = c["tp"], c["fp"], c["fn"], c["tn"]
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else float("nan")
    acc = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) else float("nan")
    specificity = tn / (tn + fp) if (tn + fp) else float("nan")
    return {"accuracy": acc, "precision": precision, "recall": recall, "f1": f1, "specificity": specificity}


def average_precision(y_true: np.ndarray, p: np.ndarray) -> float:
    y = y_true.astype(int)
    p = p.astype(float)

    n_pos = int(np.sum(y == 1))
    if n_pos == 0:
        return float("nan")

    order = np.argsort(-p)
    y_sorted = y[order]

    tp = 0
    fp = 0
    ap = 0.0
    prev_recall = 0.0

    for yi in y_sorted:
        if yi == 1:
            tp += 1
        else:
            fp += 1
        recall = tp / n_pos
        precision = tp / (tp + fp)
        if yi == 1:
            ap += precision * (recall - prev_recall)
            prev_recall = recall

    return float(ap)