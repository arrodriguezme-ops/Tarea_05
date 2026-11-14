import subprocess
import sys

import pytest

from src import audio, engine, metrics, textnorm
from src.validate_order import diagnose, validate

CFG = engine.load_config("config.yaml")


@pytest.mark.parametrize("text,val", [
    ("seis mil quinientos", 6500), ("ciento veinte", 120), ("treinta y cinco", 35),
    ("dos mil veintiuno", 2021), ("6.500", 6500), ("cien mil", 100000), ("mil", 1),
])
def test_number_words(text, val):
    spans = textnorm.number_spans(text)
    assert spans[0]["value"] == val or (text == "mil" and spans[0]["value"] == 1000)


def test_number_roundtrip():
    for n in (0, 7, 21, 35, 100, 101, 560, 1000, 6500, 12345):
        assert textnorm.number_spans(textnorm.number_to_words(n))[0]["value"] == n


def test_interview_extraction_and_verification():
    t = ("Llevo tres años de experiencia. Trabajé como analista de datos en una financiera. "
         "Uso Python, SQL y Power BI. Mi pretensión es seis mil quinientos soles. "
         "Puedo empezar en dos semanas y mi inglés es intermedio.")
    r = engine.process_transcript(t, "interview", "rules", CFG)
    assert r["fields"]["anios_experiencia"] == 3
    assert r["fields"]["pretension_salarial"] == 6500
    assert r["fields"]["disponibilidad"] == "15_dias"
    assert r["fields"]["nivel_ingles"] == "intermedio"
    assert set(r["fields"]["tecnologias"]) == {"python", "sql", "power bi"}
    assert all(v == "verificado" for k, v in r["verified"].items() if r["fields"][k] is not None)


def test_unverified_when_evidence_missing():
    from src import verify
    assert verify.verify_field("numeric", {"value": 6500, "evidence": "seis mil quinientos"},
                               "pretension de siete mil") == "sin_verificar"


def test_order_with_self_correction_and_bad_total():
    t = ("Quiero dos hamburguesas y una gaseosa. Mejor tres hamburguesas. Pago en efectivo. "
         "Es en avenida lima 1234. El total es cien soles.")
    r = engine.process_transcript(t, "order", "rules", CFG)
    items = {i["product"]: i["quantity"] for i in r["fields"]["items"]}
    assert items == {"hamburguesa": 3, "gaseosa": 1}
    assert r["fields"]["total_dicho"] == 100
    assert r["validation"]["status"] == "descuadre"      # 3*18 + 6 = 60
    assert r["validation"]["diagnosis"] == "error_hablante"


def test_diagnose_asr_confusion():
    assert diagnose(60, 50, CFG) == "error_asr"          # sesenta vs cincuenta


def test_validate_ok():
    rec = {"items": [{"product": "pizza", "quantity": 1, "unit_price": 35}], "promocion": None,
           "total_dicho": 35}
    assert validate(rec, CFG)["status"] == "ok"


def test_wer_normalization():
    assert metrics.wer_cer("Hola, Mundo.", "hola mundo")[0] == 0


def test_snr_is_measured():
    import numpy as np
    x = np.sin(np.linspace(0, 400, 16000)).astype("float32")
    _, snr = audio.add_noise(x, 10, "pink", 1)
    assert abs(snr - 10) < 0.01


def test_engine_has_no_ui_imports():
    code = "import sys, src.engine; assert not {'streamlit','gradio'} & set(sys.modules)"
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0


def test_measure_words_and_no_false_quantity():
    t = "Quiero una porción de papas. Una de las pizzas no. El total es nueve soles."
    r = engine.process_transcript(t, "order", "rules", CFG)
    assert [(i["product"], i["quantity"]) for i in r["fields"]["items"]] == [("papas", 1)]
