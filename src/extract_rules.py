"""Extraccion por reglas (regex + normalizacion de numeros). Devuelve {campo: {value, evidence}}."""
import re

from .textnorm import normalize, number_spans, tokens

EMPTY = {"value": None, "evidence": None}


def _span_text(toks, s, e):
    return " ".join(toks[s:e])


def extract_interview(transcript: str, cfg: dict) -> dict:
    icfg, gloss = cfg["interview"], cfg["glossary"]["tecnologias"]
    text, toks = normalize(transcript), tokens(transcript)
    spans = number_spans(transcript)
    out = {k: dict(EMPTY) for k in icfg["fields"]}

    for sp in spans:
        if sp["end"] < len(toks) and toks[sp["end"]] in ("ano", "anos", "anio", "anios"):
            out["anios_experiencia"] = {"value": sp["value"],
                                        "evidence": _span_text(toks, sp["start"], sp["end"] + 1)}
            break

    for pat in icfg["puesto_patterns"]:
        m = re.search(pat, text + " ")
        if m:
            out["ultimo_puesto"] = {"value": m.group(1).strip(), "evidence": m.group(1).strip()}
            break

    found, ev = [], []
    for canon, aliases in gloss.items():
        hit = next((a for a in aliases if f" {normalize(a)} " in f" {text} "), None)
        if hit:
            found.append(canon)
            ev.append(normalize(hit))
    if found:
        out["tecnologias"] = {"value": found, "evidence": ev}

    for sp in spans:
        if sp["value"] < icfg["salary_min"]:
            continue
        nxt = toks[sp["end"]] if sp["end"] < len(toks) else ""
        near_kw = any(k in toks[max(0, sp["start"] - 8):sp["start"]] for k in icfg["salary_keywords"])
        if nxt in icfg["currencies"] or near_kw:
            end = sp["end"] + (1 if nxt in icfg["currencies"] else 0)
            out["pretension_salarial"] = {"value": sp["value"],
                                          "evidence": _span_text(toks, sp["start"], end),
                                          "currency": icfg["currencies"].get(nxt)}
            break

    for field, key in (("disponibilidad", "disponibilidad_patterns"),
                       ("nivel_ingles", "nivel_ingles_patterns")):
        for pat, cat in icfg[key]:
            m = re.search(pat, text)
            if m:
                out[field] = {"value": cat, "evidence": m.group(0)}
                break
    return out


def extract_order(transcript: str, cfg: dict) -> dict:
    ocfg = cfg["order"]
    text, toks = normalize(transcript), tokens(transcript)
    spans = number_spans(transcript)
    out = {k: dict(EMPTY) for k in ocfg["fields"]}
    corr, cancel = set(ocfg["correction_markers"]), set(ocfg["cancel_markers"])
    skip = set(ocfg["measure_words"]) | {"de"}
    start_to_span = {sp["start"]: sp for sp in spans}
    end_to_span = {sp["end"]: sp for sp in spans}

    # Items: la ultima mencion de cada producto gana (autocorreccion).
    prod_re = {k: re.compile(v["pattern"]) for k, v in ocfg["catalog"].items()}
    items, last_prod = {}, None
    for i, tok in enumerate(toks):
        sp = start_to_span.get(i)
        # correccion sin producto: "mejor tres" -> aplica al ultimo producto
        if sp and last_prod and any(t in corr for t in toks[max(0, i - 3):i]):
            nxt = " ".join(toks[sp["end"]:sp["end"] + 2])
            if not any(r.match(nxt) for r in prod_re.values()):
                items[last_prod]["quantity"] = sp["value"]
                items[last_prod]["evidence"] = _span_text(toks, sp["start"], sp["end"])
                continue
        for key, rx in prod_re.items():
            if not rx.fullmatch(tok):
                continue
            # el numero va pegado al producto, saltando medidas ("una porcion de papas")
            # y admitiendo una palabra en medio ("dos grandes pizzas")
            j = i
            while j > 0 and toks[j - 1] in skip:
                j -= 1
            qty_sp = next((end_to_span[c] for c in (j, j - 1) if c in end_to_span), None)
            if any(t in cancel for t in toks[max(0, i - 4):i]) and key in items:
                del items[key]
                break
            if qty_sp:
                items[key] = {"product": key, "quantity": qty_sp["value"],
                              "unit_price": ocfg["catalog"][key]["price"],
                              "evidence": _span_text(toks, qty_sp["start"], i + 1)}
                last_prod = key
            break
    if items:
        out["items"] = {"value": [{k: v for k, v in it.items() if k != "evidence"} for it in items.values()],
                        "evidence": [it["evidence"] for it in items.values()]}

    for name, p in ocfg["promotions"].items():
        m = re.search(p["pattern"], text)
        if m:
            out["promocion"] = {"value": name, "evidence": m.group(0)}
            break

    m = re.search(ocfg["address_pattern"], text)
    if m:
        out["direccion_entrega"] = {"value": m.group(1), "evidence": m.group(1)}

    for name, pat in ocfg["payments"].items():
        m = re.search(pat, text)
        if m:
            out["metodo_pago"] = {"value": name, "evidence": m.group(0)}
            break

    kw = [i for i, t in enumerate(toks) if t in ocfg["total_keywords"]]
    if kw:
        after = next((sp for sp in spans if sp["start"] > kw[-1] and sp["start"] - kw[-1] <= 5), None)
        if after:
            out["total_dicho"] = {"value": after["value"],
                                  "evidence": _span_text(toks, after["start"], after["end"])}
    return out


EXTRACTORS = {"interview": extract_interview, "order": extract_order}
