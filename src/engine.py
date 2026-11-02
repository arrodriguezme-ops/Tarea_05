"""Motor unico: audio -> transcripcion -> campos -> verificacion (-> validacion si es pedido).

No importa ninguna libreria de UI. Verificacion:
    python -c "import sys, src.engine; assert not {'streamlit','gradio'} & set(sys.modules)"
"""
import time
from pathlib import Path

import yaml

from . import audio, extract_rules, verify

SCHEMAS = ("interview", "order")


def load_config(path: str = "config.yaml") -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def extract(transcript: str, schema: str, extractor: str, cfg: dict) -> dict:
    if extractor == "rules":
        return extract_rules.EXTRACTORS[schema](transcript, cfg)
    if extractor == "llm":
        from .extract_llm import extract_llm
        return extract_llm(transcript, schema, cfg)
    raise ValueError(f"extractor desconocido: {extractor}")


def process_transcript(transcript: str, schema: str, extractor: str, cfg: dict) -> dict:
    """Etapa sin audio: se reutiliza sobre transcripciones en cache (CI, evaluacion)."""
    raw = extract(transcript, schema, extractor, cfg)
    kinds = cfg[schema]["fields"]
    status = verify.verify_record(raw, kinds, transcript)
    fields = {k: v.get("value") for k, v in raw.items()}
    result = {"fields": fields, "evidence": {k: v.get("evidence") for k, v in raw.items()},
              "verified": status}
    if schema == "order":
        from .validate_order import validate
        result["validation"] = validate(fields, cfg)
    return result


def process_audio(audio_path: str, schema: str = "interview", extractor: str = "rules",
                  config_path: str = "config.yaml", level: str = "L0", model: str | None = None,
                  compute_type: str | None = None, device: str | None = None,
                  glossary: bool = False) -> dict:
    """Unica funcion publica. Nunca lanza: los errores van en el campo `error`."""
    out = {"transcript": None, "fields": {}, "verified": {}, "device": None, "elapsed_s": None,
           "error": None, "schema": schema, "extractor": extractor}
    t0 = time.perf_counter()
    try:
        from . import asr
        cfg = load_config(config_path)
        if schema not in SCHEMAS:
            raise ValueError(f"schema debe ser uno de {SCHEMAS}")
        samples, info = audio.apply_level(level, audio.load_audio(audio_path, cfg["ladder"]["target_sr"]), cfg)
        tr = asr.transcribe(samples, cfg, model, compute_type, device, glossary)
        out.update(transcript=tr["text"], device=tr["device"], asr=tr, ladder=info)
        if tr["cpu_fallback"]:
            out["error"] = "Se pidio cuda pero el modelo corre en CPU (fallback silencioso)"
        out.update(process_transcript(tr["text"], schema, extractor, cfg))
    except Exception as e:  # el contrato es devolver el error, no lanzarlo
        out["error"] = f"{type(e).__name__}: {e}"
    out["elapsed_s"] = time.perf_counter() - t0
    return out
