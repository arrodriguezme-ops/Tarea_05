"""Analisis pedidos por la tarea, desde cache + results (sin GPU):
 1. WER vs utilidad del registro (casos extremos)
 2. Cambio de texto entre precisiones (int8 vs float32 / float16) y CPU vs GPU
 3. Efecto del glosario con IC (diferencia pareada por clip)

  python -m scripts.analysis        -> results/analysis.json y tabla en consola
"""
import json
from itertools import product
from pathlib import Path

from src import engine, metrics
from src.textnorm import normalize


def load_rows(cfg, extractor="rules"):
    p = Path(cfg["paths"]["results_dir"]) / f"results_{extractor}.json"
    return json.loads(p.read_text(encoding="utf-8"))["rows"]


def pick(rows, **kw):
    return {r["clip"]: r for r in rows if all(r[k] == v for k, v in kw.items())}


def wer_vs_record(rows):
    """Casos extremos entre todos los clips/configuraciones: WER alto + registro perfecto y viceversa."""
    out = {}
    for task in ("interview", "order"):
        rs = [r for r in rows if r["task"] == task]
        if not rs:
            continue
        med = sorted(r["wer"] for r in rs)[len(rs) // 2]
        hi_perfect = [r for r in rs if r["wer"] >= med and r["record_acc"] == 1.0]
        lo_broken = [r for r in rs if r["wer"] <= med and r["record_acc"] < 1.0]
        fmt = lambda r: {"clip": r["clip"], "model": r["model"], "compute_type": r["compute_type"],
                         "glosario": r["glossary"], "level": r["level"], "wer": r["wer"], "record_acc": r["record_acc"],
                         "campos_mal": [f for f, c in r["fields"].items() if not c["correct"]]}
        out[task] = {"mediana_wer": med,
                     "wer_alto_registro_perfecto": [fmt(r) for r in sorted(hi_perfect, key=lambda r: -r["wer"])[:3]],
                     "wer_bajo_registro_roto": [fmt(r) for r in sorted(lo_broken, key=lambda r: r["wer"])[:3]],
                     "corr_pearson_wer_exactitud": _pearson([r["wer"] for r in rs], [r["record_acc"] for r in rs])}
    return out


def _pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sx = sum((a - mx) ** 2 for a in x) ** 0.5
    sy = sum((b - my) ** 2 for b in y) ** 0.5
    return None if sx == 0 or sy == 0 else sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def text_change(rows, task="interview", model="small", level="L0"):
    """Para cada par de configuraciones del mismo modelo: cuantas palabras cambian entre sus textos."""
    cfgs = sorted({(r["compute_type"], r["device"]) for r in rows
                   if r["task"] == task and r["model"] == model and not r["glossary"] and r["level"] == level})
    res = []
    for a, b in product(cfgs, cfgs):
        if a >= b:
            continue
        ra = pick(rows, task=task, model=model, compute_type=a[0], device=a[1], glossary=False, level=level)
        rb = pick(rows, task=task, model=model, compute_type=b[0], device=b[1], glossary=False, level=level)
        per = {c: metrics.wer_cer(ra[c]["text"], rb[c]["text"])[0] for c in ra if c in rb}
        if per:
            res.append({"a": f"{a[0]}/{a[1]}", "b": f"{b[0]}/{b[1]}", "clips_identicos": sum(v == 0 for v in per.values()),
                        "n": len(per), "diferencia_media_palabras_pct": 100 * sum(per.values()) / len(per),
                        "speedup_sec_por_min": _speed(ra, rb)})
    return res


def _speed(ra, rb):
    sa = sum(r["sec_per_audio_min"] for r in ra.values()) / len(ra)
    sb = sum(r["sec_per_audio_min"] for r in rb.values() if r) / len(rb)
    return {"a": sa, "b": sb}


def glossary_effect(rows, cfg, task="interview", model="small", ct="int8", dev="cpu"):
    plain = pick(rows, task=task, model=model, compute_type=ct, device=dev, glossary=False, level="L0")
    gloss = pick(rows, task=task, model=model, compute_type=ct, device=dev, glossary=True, level="L0")
    clips = sorted(set(plain) & set(gloss))
    if not clips:
        return None
    d_wer = [gloss[c]["wer"] - plain[c]["wer"] for c in clips]
    d_acc = [gloss[c]["record_acc"] - plain[c]["record_acc"] for c in clips]
    ev = cfg["evaluation"]
    mw = metrics.bootstrap_ci(d_wer, ev["bootstrap_resamples"], ev["bootstrap_seed"])
    ma = metrics.bootstrap_ci(d_acc, ev["bootstrap_resamples"], ev["bootstrap_seed"])
    # terminos del glosario: aparecen en la referencia y se oyen bien?
    terms = {t for t in cfg["glossary"]["tecnologias"]}
    hits = lambda grp: sum(normalize(t) in normalize(grp[c]["text"]).split() or normalize(t) in normalize(grp[c]["text"])
                           for c in clips for t in terms)
    return {"n_clips": len(clips), "delta_wer_media": mw[0], "delta_wer_ic95": [mw[1], mw[2]],
            "delta_exactitud_media": ma[0], "delta_exactitud_ic95": [ma[1], ma[2]],
            "terminos_del_glosario_en_texto": {"plano": hits(plain), "con_glosario": hits(gloss)},
            "lectura": {k: ("IC incluye 0: sin efecto demostrable" if lo <= 0 <= hi else "IC excluye 0 (con 5 clips es optimista)")
                        for k, (lo, hi) in {"wer": (mw[1], mw[2]), "exactitud": (ma[1], ma[2])}.items()}}


def main():
    cfg = engine.load_config()
    rows = load_rows(cfg)
    out = {"wer_vs_registro": wer_vs_record(rows), "cambio_de_texto": text_change(rows),
           "glosario": glossary_effect(rows, cfg)}
    p = Path(cfg["paths"]["results_dir"]) / "analysis.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
