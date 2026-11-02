"""Metricas en dos capas: transcripcion (WER, CER) y registro (exactitud por campo, F1 macro, error abs)."""
import numpy as np
import jiwer

from .textnorm import normalize


def wer_cer(reference: str, hypothesis: str) -> tuple[float, float]:
    r, h = normalize(reference), normalize(hypothesis)
    return float(jiwer.wer(r, h)), float(jiwer.cer(r, h))


def bootstrap_ci(values, n: int, seed: int, alpha: float = 0.05):
    """IC percentil de la media. Con muestras de ~5 clips es ancho: es la advertencia, no un defecto."""
    v = np.asarray([x for x in values if x is not None and not np.isnan(x)], dtype=float)
    if len(v) == 0:
        return None, None, None
    rng = np.random.default_rng(seed)
    means = rng.choice(v, size=(n, len(v)), replace=True).mean(axis=1)
    return float(v.mean()), float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def _norm(v):
    return normalize(str(v)) if v is not None else None


def field_match(kind: str, pred, gold) -> dict:
    """Devuelve {correct: bool, abs_err: float|None}."""
    if kind == "numeric":
        if pred is None or gold is None:
            return {"correct": pred is None and gold is None, "abs_err": None}
        err = abs(float(pred) - float(gold))
        return {"correct": err < 1e-9, "abs_err": err}
    if kind == "list":
        return {"correct": {_norm(x) for x in (pred or [])} == {_norm(x) for x in (gold or [])},
                "abs_err": None}
    if kind == "items":
        key = lambda L: {(_norm(i["product"]), float(i["quantity"])) for i in (L or [])}
        return {"correct": key(pred) == key(gold), "abs_err": None}
    return {"correct": _norm(pred) == _norm(gold), "abs_err": None}


def macro_f1(preds: list, golds: list) -> float | None:
    classes = sorted({g for g in golds if g is not None})
    if not classes:
        return None
    f1s = []
    for c in classes:
        tp = sum(p == c and g == c for p, g in zip(preds, golds))
        fp = sum(p == c and g != c for p, g in zip(preds, golds))
        fn = sum(p != c and g == c for p, g in zip(preds, golds))
        f1s.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return float(np.mean(f1s))


def score_record(fields: dict, verified: dict, gold: dict, kinds: dict) -> dict:
    """Puntua un registro contra el oro. Devuelve por campo: correct, abs_err, status."""
    rows = {}
    for f, kind in kinds.items():
        m = field_match(kind, fields.get(f), gold.get(f))
        rows[f] = {**m, "status": verified.get(f), "pred": fields.get(f), "gold": gold.get(f)}
    return rows
