"""Genera los guiones .md y el ground truth (CSV de entrevistas, JSON de pedidos) desde script_data.

  python -m scripts.build_recording_scripts
La transcripcion de referencia es el dialogo sin etiquetas de hablante: lea el guion TAL CUAL.
"""
import csv
import json
from pathlib import Path

from scripts.script_data import INTERVIEWS, ORDERS
from src.engine import load_config


def reference(dialogue) -> str:
    return " ".join(text for _, text in dialogue)


def write_md(path: Path, item: dict, roles: str, gold_json: dict):
    lines = [f"# {item['clip']}", "", f"_{roles}_", "", f"**Variacion / trampas:** {item['notes']}", ""]
    lines += [f"**{s}:** {t}\n" for s, t in item["dialogue"]]
    lines += ["", "## Valores correctos", "```json", json.dumps(gold_json, ensure_ascii=False, indent=1), "```"]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    cfg = load_config()
    out = Path("data/recording_scripts")
    out.mkdir(parents=True, exist_ok=True)
    gt = Path(cfg["paths"]["ground_truth_interviews"])
    gt.parent.mkdir(parents=True, exist_ok=True)
    cols = ["clip", "reference_transcript", *cfg["interview"]["fields"].keys()]
    with gt.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for it in INTERVIEWS:
            g = dict(it["gold"])
            g["tecnologias"] = ";".join(g["tecnologias"])
            w.writerow({"clip": it["clip"], "reference_transcript": reference(it["dialogue"]), **g})
            write_md(out / f"{it['clip']}.md", it, "A entrevista, B es la candidata/candidato.", it["gold"])

    orders = []
    for it in ORDERS:
        g = dict(it["gold"])
        g["items"] = [{"product": p, "quantity": q, "unit_price": u} for p, q, u in g["items"]]
        orders.append({"clip": it["clip"], "reference_transcript": reference(it["dialogue"]),
                       "traps": it["traps"], "record": g})
        write_md(out / f"{it['clip']}.md", it, "A vende (restaurante), B es el cliente.", {"traps": it["traps"], **g})
    Path(cfg["paths"]["ground_truth_orders"]).write_text(json.dumps(orders, ensure_ascii=False, indent=1), encoding="utf-8")
    for it in INTERVIEWS + ORDERS:
        print(it["clip"], len(reference(it["dialogue"]).split()), "palabras")


if __name__ == "__main__":
    main()
