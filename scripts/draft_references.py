"""Borrador de revision de transcripciones de referencia (NO modifica el ground truth).

Compara el guion con lo que oyo el ASR y marca solo las diferencias, para que una persona
escuche esos tramos y decida cual es la referencia real.

  python -m scripts.draft_references
Salida: data/ground_truth/review/<clip>.md y review/_resumen.md
"""
import difflib
import json
from pathlib import Path

from scripts.evaluate import load_gold
from src import engine
from src.textnorm import normalize

CONTEXT = 4  # palabras de contexto alrededor de cada diferencia


def diff_markup(script: str, heard: str):
    a, b = normalize(script).split(), normalize(heard).split()
    ops = difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
    out, n_diff = [], 0
    for k, (tag, i1, i2, j1, j2) in enumerate(ops):
        if tag == "equal":
            seg = a[i1:i2]
            if k == 0:
                seg = ["..."] + seg[-CONTEXT:] if len(seg) > CONTEXT else seg
            elif k == len(ops) - 1:
                seg = seg[:CONTEXT] + ["..."] if len(seg) > CONTEXT else seg
            elif len(seg) > 2 * CONTEXT:
                seg = seg[:CONTEXT] + ["..."] + seg[-CONTEXT:]
            out.append(" ".join(seg))
        else:
            n_diff += max(i2 - i1, j2 - j1)
            out.append(f"**[guion: {' '.join(a[i1:i2]) or '∅'} | oído: {' '.join(b[j1:j2]) or '∅'}]**")
    return " ".join(out), n_diff, len(a)


def main():
    cfg = engine.load_config()
    gold = load_gold(cfg)
    outdir = Path(cfg["paths"]["ground_truth_interviews"]).parent / "review"
    outdir.mkdir(parents=True, exist_ok=True)
    summary = ["# Revision de referencias\n",
               "Borrador generado comparando guion vs lo que oyo `small`/`int8`. **Escuche cada tramo marcado** y "
               "edite `scripts/script_data.py` (o la referencia) segun lo que REALMENTE se dijo. "
               "Aviso: si acepta el texto del ASR sin escuchar, el WER de ese modelo queda subestimado (evaluacion circular).\n",
               "| clip | palabras guion | palabras en desacuerdo |", "|---|---|---|"]
    for task in ("interview", "order"):
        for clip, g in gold[task].items():
            f = Path(cfg["paths"]["cache_transcripts"]) / task / f"{clip}__small__int8__cpu__plain__L0.json"
            if not f.exists():
                continue
            heard = json.loads(f.read_text(encoding="utf-8"))["text"]
            marked, n_diff, n_words = diff_markup(g["reference"], heard)
            (outdir / f"{clip}.md").write_text(
                f"# {clip}\n\nDiferencias guion vs audio (revisar escuchando):\n\n{marked}\n\n"
                f"---\n## Texto oido completo (borrador de referencia)\n\n{heard}\n", encoding="utf-8")
            summary.append(f"| {clip} | {n_words} | {n_diff} ({n_diff / n_words:.0%}) |")
    (outdir / "_resumen.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
