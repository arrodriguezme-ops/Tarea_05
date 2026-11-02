"""Carga de audio y escalera de degradacion L0-L3 (reproducible, sin UI)."""
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from scipy import signal


def load_audio(path: str, sr: int = 16000) -> np.ndarray:
    """Decodifica cualquier formato a mono float32 con ffmpeg."""
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def _resample(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    if sr_in == sr_out:
        return x
    g = np.gcd(sr_in, sr_out)
    return signal.resample_poly(x, sr_out // g, sr_in // g).astype(np.float32)


def _codec_roundtrip(x: np.ndarray, sr: int, codec: str, bitrate: str) -> np.ndarray:
    """L1: comprime a bitrate bajo (como una nota de voz) y decodifica de vuelta."""
    with tempfile.TemporaryDirectory() as d:
        raw, enc = Path(d) / "in.f32", Path(d) / "enc.ogg"
        raw.write_bytes(x.astype(np.float32).tobytes())
        subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1",
                        "-i", str(raw), "-c:a", codec, "-b:a", bitrate, str(enc)], check=True)
        return load_audio(str(enc), sr)


def _pink_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.arange(len(spec), dtype=np.float64)
    f[0] = 1
    return np.fft.irfft(spec / np.sqrt(f), n).astype(np.float32)


def power(x: np.ndarray) -> float:
    return float(np.mean(x.astype(np.float64) ** 2))


def add_noise(x: np.ndarray, snr_db: float, kind: str, seed: int) -> tuple[np.ndarray, float]:
    """Suma ruido escalado a una SNR objetivo y devuelve (audio, SNR medida).

    SNR = 10*log10(P_senal / P_ruido) con potencia media sobre toda la senal.
    """
    rng = np.random.default_rng(seed)
    noise = _pink_noise(len(x), rng) if kind == "pink" else rng.standard_normal(len(x)).astype(np.float32)
    noise *= np.sqrt(power(x) / (power(noise) * 10 ** (snr_db / 10)))
    measured = 10 * np.log10(power(x) / power(noise))
    return (x + noise).astype(np.float32), float(measured)


def apply_level(level: str, x: np.ndarray, cfg: dict) -> tuple[np.ndarray, dict]:
    """Aplica un nivel de la escalera a audio 16 kHz mono. Devuelve (audio 16 kHz, info)."""
    lc, sr = cfg["ladder"], cfg["ladder"]["target_sr"]
    info = {"level": level}
    if level == "L0":
        return x, info
    if level in ("L1", "L3"):
        x = _codec_roundtrip(x, sr, lc["l1"]["codec"], lc["l1"]["bitrate"])
        if level == "L3":
            x, info["snr_db_measured"] = add_noise(x, lc["l3"]["snr_db"], lc["l3"]["noise"], lc["l3"]["seed"])
            info["snr_db_target"] = lc["l3"]["snr_db"]
        return x, info
    if level == "L2":
        c = lc["l2"]
        sos = signal.butter(c["order"], [c["low_hz"], c["high_hz"]], btype="band", fs=sr, output="sos")
        y = signal.sosfilt(sos, x)
        y = _resample(_resample(y, sr, c["sample_rate"]), c["sample_rate"], sr)  # 8 kHz de ancho de banda
        return y.astype(np.float32), info
    raise ValueError(f"Nivel desconocido: {level}")
