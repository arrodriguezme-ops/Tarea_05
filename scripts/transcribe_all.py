"""Transcribe el corpus y deja el resultado en cache/ (correr en Colab con GPU).

Ejemplos:
  python -m scripts.transcribe_all --task interview --models small large-v3 --compute float16 int8 --devices cuda
  python -m scripts.transcribe_all --task interview --models small --compute int8 --devices cpu
  python -m scripts.transcribe_all --task order --levels L0 L1 L2 L3 --models small --compute float16 --devices cuda
  (anada --glossary para repetir con vocabulario de dominio)
"""
import argparse
import json
from pathlib import Path

from src import asr, audio
from src.engine import load_config

AUDIO_EXT = {".wav", ".mp3", ".m4a", ".mp4", ".aac", ".ogg", ".opus", ".flac"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=["interview", "order"], required=True)
    ap.add_argument("--models", nargs="+")
    ap.add_argument("--compute", nargs="+")
    ap.add_argument("--devices", nargs="+", default=["auto"])
    ap.add_argument("--levels", nargs="+", default=["L0"])
    ap.add_argument("--glossary", action="store_true", help="solo con vocabulario (si no, plano)")
    ap.add_argument("--config", default="config.yaml")
    a = ap.parse_args()
    cfg = load_config(a.config)
    models = a.models or [cfg["asr"]["default_model"]]
    computes = a.compute or [cfg["asr"]["default_compute_type"]]
    clips = sorted(p for p in (Path(cfg["paths"]["audio_dir"]) / a.task).glob("*") if p.suffix in AUDIO_EXT)
    if not clips:
        raise SystemExit(f"No hay audios en {Path(cfg['paths']['audio_dir']) / a.task}")
    outdir = Path(cfg["paths"]["cache_transcripts"]) / a.task
    outdir.mkdir(parents=True, exist_ok=True)

    for dev in a.devices:
        for model in models:
            for ct in computes:
                asr.clear_models()
                for clip in clips:
                    base = audio.load_audio(str(clip), cfg["ladder"]["target_sr"])
                    for level in a.levels:
                        pre = f"{clip.stem}__{model}__{ct}__{dev}__{'gloss' if a.glossary else 'plain'}__{level}.json"
                        if dev != "auto" and (outdir / pre).exists():
                            continue  # ya transcrito: permite retomar
                        x, info = audio.apply_level(level, base, cfg)
                        tr = asr.transcribe(x, cfg, model, ct, dev, a.glossary)
                        tr.update(clip=clip.stem, task=a.task, level=level, **{k: v for k, v in info.items() if k != "level"})
                        name = f"{clip.stem}__{model}__{ct}__{tr['device']}__{'gloss' if a.glossary else 'plain'}__{level}.json"
                        (outdir / name).write_text(json.dumps(tr, ensure_ascii=False, indent=1), encoding="utf-8")
                        print(f"{name}: device={tr['device']} {tr['sec_per_audio_min']:.1f}s/min vram={tr['vram_peak_mb']}")


if __name__ == "__main__":
    main()
