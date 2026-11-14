"""App Streamlit. Carga resultados precomputados; solo el probador interactivo llama al motor."""
import json
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from scripts.evaluate import load_gold
from src import engine

CFG = engine.load_config("config.yaml")
st.set_page_config(page_title="De la voz al registro", layout="wide")


@st.cache_data
def load_results(extractor: str):
    p = Path(CFG["paths"]["results_dir"]) / f"results_{extractor}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def summary_df(summary, task):
    rows = [s for s in summary if s["task"] == task]
    return pd.DataFrame([{
        "modelo": s["model"], "precision": s["compute_type"], "dispositivo": s["device"],
        "glosario": s["glossary"], "nivel": s["level"], "clips": s["n_clips"],
        "WER": s["wer"], "WER IC95": f"[{s['wer_lo']:.3f}, {s['wer_hi']:.3f}]",
        "CER": s["cer"], "s/min audio": s["sec_per_audio_min"], "VRAM pico MB": s["vram_peak_mb"],
        "exactitud registro": s["record_acc"]} for s in rows])


tab1, tab2, tab3, tab4 = st.tabs(["Problema y metodo", "Corpus", "Resultados", "Probador"])

with tab1:
    st.header("Del audio al registro verificado")
    st.markdown("""
Transcribir no basta: una organizacion necesita **campos verificados en una tabla y una medida de cuanto confiar en ellos**.
- **Tarea 1** convierte una entrevista en un registro de candidato (6 campos).
- **Tarea 2** convierte una llamada de ventas en un pedido que se **auto-verifica aritmeticamente**.
- Un unico motor (`src/engine.py`) sirve ambos esquemas. Todo valor extraido debe existir **literalmente** en la
  transcripcion (los numeros dichos en palabras se normalizan: *seis mil quinientos* = 6500); si no, `sin_verificar`.
- La verdad de referencia la escribe el autor **antes** de grabar; nunca se usan subtitulos automaticos.
- **No debe usarse** para decisiones automaticas de contratacion ni de cobro sin revision humana.
""")

gold = load_gold(CFG)
with tab2:
    task = st.radio("Tarea", ["interview", "order"], horizontal=True, key="corp")
    for clip, g in gold[task].items():
        with st.expander(clip):
            cols = st.columns(2)
            audio_files = list((Path(CFG["paths"]["audio_dir"]) / task).glob(f"{clip}.*"))
            if audio_files:
                cols[0].audio(str(audio_files[0]))
            else:
                cols[0].info("Audio no versionado (ver README para regenerarlo).")
            cols[0].json(g["record"])
            cols[1].markdown("**Transcripcion de referencia**")
            cols[1].write(g["reference"])
    if not gold[task]:
        st.warning("Aun no hay ground truth en data/ground_truth/.")

with tab3:
    extractor = st.radio("Extractor", ["rules", "llm"], horizontal=True)
    res = load_results(extractor)
    if not res:
        st.warning(f"Ejecute `python -m scripts.evaluate --extractor {extractor}` primero.")
    else:
        rows, summary = res["rows"], res["summary"]
        st.subheader("Tarea 1 - Entrevistas")
        st.dataframe(summary_df(summary, "interview"), use_container_width=True)
        iv = [s for s in summary if s["task"] == "interview"]
        if iv:
            s = st.selectbox("Configuracion", range(len(iv)), format_func=lambda i: f"{iv[i]['model']}/{iv[i]['compute_type']}/{iv[i]['device']}/{'gloss' if iv[i]['glossary'] else 'plain'}/{iv[i]['level']}")
            st.write("Exactitud por campo", pd.Series(iv[s]["field_accuracy"]))
            st.write("F1 macro (categoricos)", pd.Series(iv[s]["macro_f1"]))
            st.write("Error absoluto medio (numericos)", pd.Series(iv[s]["abs_error"]))
            st.write("Cobertura verificada", pd.Series(iv[s]["coverage"]))
        st.subheader("WER no predice la utilidad del registro")
        per = pd.DataFrame([{"tarea": r["task"], "clip": r["clip"], "nivel": r["level"], "modelo": r["model"],
                             "WER": r["wer"], "campos correctos": r["record_acc"]} for r in rows])
        if len(per):
            st.dataframe(per.sort_values("WER"), use_container_width=True)
            st.caption("Busque: un clip con WER alto y registro perfecto, y otro con WER bajo y registro roto.")
        ap = Path(CFG["paths"]["results_dir"]) / "analysis.json"
        if ap.exists():
            an = json.loads(ap.read_text(encoding="utf-8"))
            st.subheader("Analisis: casos extremos, precision y glosario")
            for task, d in an["wer_vs_registro"].items():
                st.markdown(f"**{task}** - correlacion WER vs exactitud del registro: `{d['corr_pearson_wer_exactitud']}`")
                st.write("WER alto con registro perfecto:", d["wer_alto_registro_perfecto"] or "ninguno en esta muestra")
                st.write("WER bajo con registro roto:", d["wer_bajo_registro_roto"] or "ninguno en esta muestra")
            st.write("Cambio de texto entre precisiones", pd.DataFrame(an["cambio_de_texto"]))
            st.write("Efecto del glosario (diferencia pareada, IC95 bootstrap)", an["glosario"])
        st.subheader("Tarea 2 - Pedidos")
        st.dataframe(summary_df(summary, "order"), use_container_width=True)
        od = [s for s in summary if s["task"] == "order"]
        if od:
            ladder = pd.DataFrame([{"nivel": s["level"], "WER": s["wer"], "exactitud de campos": s["record_acc"],
                                    "atrapados": s["traps"]["caught"], "perdidos": s["traps"]["missed"],
                                    "falsas alarmas": s["traps"]["false_alarms"],
                                    "diagnostico correcto": f"{s['traps']['diagnosis_correct']}/{s['traps']['diagnosis_total']}"}
                                   for s in od if not s["glossary"]]).sort_values("nivel")
            st.markdown("**Escalera de degradacion y validacion aritmetica**")
            st.dataframe(ladder, use_container_width=True)
            st.line_chart(ladder.set_index("nivel")[["WER", "exactitud de campos"]])
            snr = [(r["level"], r["snr_db_measured"]) for r in rows if r.get("snr_db_measured") is not None]
            if snr:
                st.caption(f"SNR medida en L3 (media): {sum(v for _, v in snr) / len(snr):.2f} dB")

with tab4:
    st.write("Suba un clip: se transcribe con el motor (puede tardar sin GPU).")
    schema = st.selectbox("Esquema", ["interview", "order"])
    ext = st.selectbox("Extractor", ["rules", "llm"])
    up = st.file_uploader("Audio", type=["wav", "mp3", "m4a", "mp4", "aac", "ogg", "opus", "flac"])
    if up and st.button("Procesar"):
        with tempfile.NamedTemporaryFile(suffix=Path(up.name).suffix, delete=False) as f:
            f.write(up.read())
        with st.spinner("Transcribiendo..."):
            out = engine.process_audio(f.name, schema, ext)
        if out["error"]:
            st.error(out["error"])
        st.caption(f"dispositivo: {out['device']} - {out['elapsed_s']:.1f}s")
        st.text_area("Transcripcion", out["transcript"] or "", height=150)
        if out["fields"]:
            st.dataframe(pd.DataFrame([{"campo": k, "valor": json.dumps(v, ensure_ascii=False),
                                        "estado": out["verified"].get(k)} for k, v in out["fields"].items()]),
                         use_container_width=True)
        if out.get("validation"):
            v = out["validation"]
            (st.success if v["status"] == "ok" else st.warning)(
                f"Validacion aritmetica: {v['status']} - calculado {v['computed_total']} vs dicho {v['said_total']}"
                + (f" - diagnostico: {v['diagnosis']}" if v["diagnosis"] else ""))
