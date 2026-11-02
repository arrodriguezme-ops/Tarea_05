"""Calcula ambas capas de metricas desde transcripciones en cache (sin GPU, sin audio).

  python -m scripts.evaluate --extractor rules
  python -m scripts.evaluate --extractor rules --gate     # sale con codigo 1 si baja del umbral (CI)
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from src import engine, metrics


def load_gold(cfg):
    gold = {"interview": {}, "order": {}}
    p = Path(cfg["paths"]["ground_truth_interviews"])
    if p.exists():
        for r in csv.DictReader(p.open(encoding="utf-8")):
            rec = {k: (r[k] or None) for k in cfg["interview"]["fields"]}
            for k in ("anios_experiencia", "pretension_salarial"):
                rec[k] = float(rec[k]) if rec[k] else None
            rec["tecnologias"] = [t.strip() for t in (r["tecnologias"] or "").split(";") if t.strip()]
            gold["interview"][r["clip"]] = {"reference": r["reference_transcript"], "record": rec, "traps": {}}
    p = Path(cfg["paths"]["ground_truth_orders"])
    if p.exists():
        for r in json.loads(p.read_text(encoding="utf-8")):
            gold["order"][r["clip"]] = {"reference": r["reference_transcript"], "record": r["record"],
                                        "traps": r.get("traps", {})}
    return gold


def get_result(path: Path, tr: dict, schema: str, extractor: str, cfg: dict) -> dict:
    cache = Path(cfg["paths"]["cache_records"]) / extractor / schema / path.name
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    res = engine.process_transcript(tr["text"], schema, extractor, cfg)
    if extractor == "llm":  # las llamadas a la API se cachean; las reglas son gratis
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def evaluate(cfg, extractor):
    gold, rows = load_gold(cfg), []
    for schema in ("interview", "order"):
        for f in sorted((Path(cfg["paths"]["cache_transcripts"]) / schema).glob("*.json")):
            tr = json.loads(f.read_text(encoding="utf-8"))
            g = gold[schema].get(tr["clip"])
            if not g:
                continue
            res = get_result(f, tr, schema, extractor, cfg)
            w, c = metrics.wer_cer(g["reference"], tr["text"])
            sc = metrics.score_record(res["fields"], res["verified"], g["record"], cfg[schema]["fields"])
            rows.append({"task": schema, "clip": tr["clip"], "model": tr["model"], "compute_type": tr["compute_type"],
                         "device": tr["device"], "glossary": tr["glossary"], "level": tr.get("level", "L0"),
                         "wer": w, "cer": c, "sec_per_audio_min": tr["sec_per_audio_min"],
                         "vram_peak_mb": tr["vram_peak_mb"], "snr_db_measured": tr.get("snr_db_measured"),
                         "text": tr["text"], "fields": sc, "validation": res.get("validation"),
                         "traps": g["traps"],
                         "record_acc": sum(v["correct"] for v in sc.values()) / len(sc)})
    return rows


def summarize(rows, cfg):
    ev, groups = cfg["evaluation"], defaultdict(list)
    for r in rows:
        groups[(r["task"], r["model"], r["compute_type"], r["device"], r["glossary"], r["level"])].append(r)
    out = []
    for (task, model, ct, dev, gl, lvl), rs in groups.items():
        n, seed = ev["bootstrap_resamples"], ev["bootstrap_seed"]
        s = {"task": task, "model": model, "compute_type": ct, "device": dev, "glossary": gl, "level": lvl,
             "n_clips": len(rs)}
        for key in ("wer", "cer"):
            s[key], s[f"{key}_lo"], s[f"{key}_hi"] = metrics.bootstrap_ci([r[key] for r in rs], n, seed)
        s["sec_per_audio_min"] = sum(r["sec_per_audio_min"] for r in rs) / len(rs)
        vr = [r["vram_peak_mb"] for r in rs if r["vram_peak_mb"] is not None]
        s["vram_peak_mb"] = max(vr) if vr else None
        kinds = cfg[task]["fields"]
        s["field_accuracy"], s["abs_error"], s["coverage"], s["acc_verified"], s["macro_f1"] = {}, {}, {}, {}, {}
        for f, kind in kinds.items():
            cells = [r["fields"][f] for r in rs]
            s["field_accuracy"][f] = sum(c["correct"] for c in cells) / len(cells)
            ver = [c for c in cells if c["status"] == "verificado"]
            s["coverage"][f] = len(ver) / len(cells)
            s["acc_verified"][f] = sum(c["correct"] for c in ver) / len(ver) if ver else None
            if kind == "numeric":
                errs = [c["abs_err"] for c in cells if c["abs_err"] is not None]
                s["abs_error"][f] = sum(errs) / len(errs) if errs else None
            if kind == "categorical":
                s["macro_f1"][f] = metrics.macro_f1([c["pred"] for c in cells], [c["gold"] for c in cells])
        s["record_acc"] = sum(s["field_accuracy"].values()) / len(kinds)
        if task == "order":
            s["traps"] = trap_table(rs)
        out.append(s)
    return out


def trap_table(rs):
    planted = [r for r in rs if r["traps"].get("total_incorrecto")]
    clean = [r for r in rs if not r["traps"].get("total_incorrecto")]
    flag = lambda r: (r["validation"] or {}).get("status") == "descuadre"
    caught = sum(flag(r) for r in planted)
    flagged = [r for r in rs if flag(r)]
    truth = lambda r: "error_hablante" if r["traps"].get("total_incorrecto") else "error_asr"
    return {"planted": len(planted), "caught": caught, "missed": len(planted) - caught,
            "false_alarms": sum(flag(r) for r in clean),
            "diagnosis_correct": sum(r["validation"]["diagnosis"] == truth(r) for r in flagged),
            "diagnosis_total": len(flagged)}


def gate(summary, cfg):
    g = cfg["evaluation"]["gate"]
    base = [s for s in summary if s["level"] == "L0" and not s["glossary"]]
    fails = []
    for task in ("interview", "order"):
        cand = [s for s in base if s["task"] == task]
        if not cand:
            fails.append(f"{task}: no hay transcripciones en cache")
            continue
        best = min(cand, key=lambda s: s["wer"])
        if best["wer"] > g["max_wer"]:
            fails.append(f"{task}: WER {best['wer']:.3f} > {g['max_wer']}")
        if task == "interview" and best["record_acc"] < g["min_interview_field_accuracy"]:
            fails.append(f"interview: exactitud {best['record_acc']:.2f} < {g['min_interview_field_accuracy']}")
        if task == "order":
            t = best["traps"]
            rate = t["caught"] / t["planted"] if t["planted"] else 0
            if rate < g["min_order_trap_catch_rate"]:
                fails.append(f"order: trampas atrapadas {rate:.2f} < {g['min_order_trap_catch_rate']}")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extractor", default="rules", choices=["rules", "llm"])
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--gate", action="store_true")
    a = ap.parse_args()
    cfg = engine.load_config(a.config)
    rows = evaluate(cfg, a.extractor)
    summary = summarize(rows, cfg)
    out = Path(cfg["paths"]["results_dir"])
    out.mkdir(parents=True, exist_ok=True)
    (out / f"results_{a.extractor}.json").write_text(
        json.dumps({"rows": rows, "summary": summary}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(rows)} filas, {len(summary)} grupos -> {out / f'results_{a.extractor}.json'}")
    if a.gate:
        fails = gate(summary, cfg)
        print("GATE FALLA:\n  " + "\n  ".join(fails) if fails else "GATE OK")
        sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
