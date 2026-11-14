"""Validacion aritmetica del pedido y diagnostico de la causa de un descuadre."""
from .textnorm import edit_distance, number_to_words


def compute_total(items: list[dict], promocion: str | None, cfg: dict) -> float:
    ocfg = cfg["order"]
    subtotal = sum(it["quantity"] * it["unit_price"] for it in items)
    promo = ocfg["promotions"].get(promocion or "", {})
    if "discount_pct" in promo:
        return subtotal * (1 - promo["discount_pct"] / 100)
    return subtotal - promo.get("discount_sol", 0)


def diagnose(said: float, computed: float, cfg: dict) -> str:
    """Regla: se comparan las lecturas habladas del total dicho y del calculado. Si tienen el
    mismo numero de palabras y difieren en UNA sola, con distancia de edicion relativa <= umbral
    (config), es plausible una confusion del ASR (p.ej. cincuenta/sesenta) -> `error_asr`.
    Cualquier otra diferencia (cifra distinta, otra magnitud) -> `error_hablante`."""
    if not (float(said).is_integer() and float(computed).is_integer() and 0 <= said < 10**6 and 0 <= computed < 10**6):
        return "error_hablante"
    a, b = number_to_words(int(said)).split(), number_to_words(int(computed)).split()
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    if len(a) == len(b) and len(diff) == 1:
        x, y = diff[0]
        if edit_distance(x, y) / max(len(x), len(y)) <= cfg["order"]["asr_error_max_rel_distance"]:
            return "error_asr"
    return "error_hablante"


def validate(record: dict, cfg: dict) -> dict:
    """record: {campo: valor}. Devuelve estado, total calculado y diagnostico."""
    items, said = record.get("items"), record.get("total_dicho")
    catalog = cfg["order"]["catalog"]
    items = [dict(it, unit_price=it.get("unit_price") if it.get("unit_price") is not None
                  else catalog.get(it.get("product"), {}).get("price")) for it in (items or [])]
    if any(it.get("quantity") is None or it["unit_price"] is None for it in items):
        return {"status": "no_validable", "computed_total": None, "said_total": said, "diagnosis": None}
    if not items or said is None:
        return {"status": "no_validable", "computed_total": None, "said_total": said, "diagnosis": None}
    computed = compute_total(items, record.get("promocion"), cfg)
    ok = abs(computed - said) <= cfg["order"]["tolerance_sol"]
    return {"status": "ok" if ok else "descuadre", "computed_total": computed, "said_total": said,
            "diagnosis": None if ok else diagnose(said, computed, cfg)}
