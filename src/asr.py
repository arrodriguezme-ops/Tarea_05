"""ASR con faster-whisper. El dispositivo se LEE de la libreria en tiempo de ejecucion."""
import subprocess
import threading
import time

import numpy as np

_MODELS: dict = {}
_IDLE_MB = None  # VRAM usada antes de cargar ningun modelo en este proceso


def cuda_available() -> bool:
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


def _vram_used_mb() -> float | None:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=5).stdout.split()[0]
        return float(out)
    except Exception:
        return None


class VramSampler:
    """Muestrea nvidia-smi en un hilo; reporta el pico sobre la linea base."""

    def __init__(self, period: float):
        self.period, self.peak, self.base = period, None, _IDLE_MB
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop.is_set():
            v = _vram_used_mb()
            if v is not None:
                self.peak = v if self.peak is None else max(self.peak, v)
            time.sleep(self.period)

    def __enter__(self):
        self._t.start()
        return self

    def __exit__(self, *a):
        self._stop.set()
        self._t.join()

    @property
    def peak_mb(self):
        return self.peak


def clear_models():
    """Libera modelos para que el pico de VRAM de la siguiente config sea comparable."""
    global _MODELS
    _MODELS = {}
    import gc
    gc.collect()


def get_model(name: str, device: str, compute_type: str):
    global _IDLE_MB
    if _IDLE_MB is None and not _MODELS:
        _IDLE_MB = _vram_used_mb()
    key = (name, device, compute_type)
    if key not in _MODELS:
        from faster_whisper import WhisperModel
        _MODELS[key] = WhisperModel(name, device=device, compute_type=compute_type)
    return _MODELS[key]


def transcribe(samples: np.ndarray, cfg: dict, model: str | None = None, compute_type: str | None = None,
               device: str | None = None, glossary: bool = False) -> dict:
    acfg = cfg["asr"]
    model = model or acfg["default_model"]
    compute_type = compute_type or acfg["default_compute_type"]
    requested = device or acfg["default_device"]
    if requested == "auto":
        requested = "cuda" if cuda_available() else "cpu"
    m = get_model(model, requested, compute_type)
    actual = str(m.model.device)  # lo que reporta ctranslate2, no la configuracion

    kwargs = {"language": acfg["language"], "beam_size": acfg["beam_size"]}
    if glossary:
        terms = ", ".join(cfg["glossary"]["tecnologias"].keys())
        kwargs["hotwords" if acfg["glossary_mechanism"] == "hotwords" else "initial_prompt"] = terms

    t0 = time.perf_counter()
    with VramSampler(acfg["vram_poll_seconds"]) as vs:
        segments, _ = m.transcribe(samples, **kwargs)
        text = " ".join(s.text.strip() for s in segments)
    elapsed = time.perf_counter() - t0
    audio_s = len(samples) / cfg["ladder"]["target_sr"]
    # pico absoluto menos VRAM en reposo (incluye pesos + activaciones)
    peak = None if vs.peak_mb is None or vs.base is None else max(vs.peak_mb - vs.base, 0.0)
    return {"text": text, "model": model, "compute_type": compute_type, "device_requested": requested,
            "device": actual, "elapsed_s": elapsed, "audio_s": audio_s,
            "sec_per_audio_min": elapsed / (audio_s / 60) if audio_s else None,
            "vram_peak_mb": peak, "glossary": glossary,
            "cpu_fallback": requested == "cuda" and actual != "cuda"}
