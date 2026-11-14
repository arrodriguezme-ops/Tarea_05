"""Regla de verificacion: todo valor extraido debe existir literalmente en la transcripcion.

Un campo es `verificado` si su evidencia aparece literalmente (normalizada) en la
transcripcion Y, para numericos, la evidencia (cifra o palabras) se resuelve al valor.
Si no, `sin_verificar`. Un valor nulo es `ausente`.
"""
from .textnorm import contains_literal, number_spans

OK, NO, ABSENT = "verificado", "sin_verificar", "ausente"


def _one(kind: str, value, evidence, transcript: str) -> bool:
    if evidence is None or not contains_literal(transcript, str(evidence)):
        return False
    if kind == "numeric":
        try:
            return any(abs(sp["value"] - float(value)) < 1e-9 for sp in number_spans(str(evidence)))
        except (TypeError, ValueError):
            return False
    return True


def verify_field(kind: str, entry: dict, transcript: str) -> str:
    value, ev = entry.get("value"), entry.get("evidence")
    if value is None:
        return ABSENT
    if kind in ("list", "items"):
        evs = ev if isinstance(ev, list) else [ev]
        return OK if evs and all(e and contains_literal(transcript, str(e)) for e in evs) else NO
    return OK if _one(kind, value, ev, transcript) else NO


def verify_record(record: dict, kinds: dict, transcript: str) -> dict:
    return {f: verify_field(kinds[f], record.get(f, {"value": None}), transcript) for f in kinds}
