# De la voz al registro: entrevistas y llamadas de venta

Un motor ASR + extracción + verificación que sirve a dos esquemas: **Tarea 1** (entrevista → registro de candidato) y **Tarea 2** (llamada de ventas → pedido que se auto-valida). Dominio de la Tarea 2: **restaurante**.

> **Estado:** código base completo y probado con pruebas unitarias. **Pendiente (depende de ti):** grabar el corpus, escribir el ground truth, correr la transcripción en GPU y rellenar las tablas de resultados.

## Declaraciones obligatorias
- **Datos inventados:** todo lo dicho en las grabaciones es ficticio. No hay salarios, direcciones ni datos personales reales.
- **Consentimiento:** todas las personas que aparecen en las grabaciones aceptaron participar. _(confirmar y completar)_
- **Herramientas de IA / MCP:** _(completar: p. ej. Claude Code — escribió el andamiaje del código; MCP servers conectados y qué hizo cada uno)._
- **Pipeline documentado en:** _(enlace público a Notion/Miro)_ · **Video:** _(enlace)_

## Instalación y ejecución
```bash
pip install -r requirements.txt        # ffmpeg debe estar en el PATH
python -m pytest -q                    # pruebas unitarias (sin audio ni GPU)
python -m scripts.evaluate --extractor rules   # métricas desde el caché
streamlit run app.py
```
Transcripción (en Colab con GPU; ver `scripts/transcribe_all.py` para más ejemplos):
```bash
python -m scripts.transcribe_all --task interview --models small large-v3 --compute float16 int8 --devices cuda
python -m scripts.transcribe_all --task interview --models small --compute int8 --devices cpu
python -m scripts.transcribe_all --task interview --models small --compute float16 --devices cuda --glossary
python -m scripts.transcribe_all --task order --levels L0 L1 L2 L3 --models small --compute float16 --devices cuda
```
El audio y los pesos de modelos **no se versionan**: pide los audios al autor o regrábalos siguiendo `data/recording_scripts/README.md` y colócalos en `data/audio/{interview,order}/<clip>.<ext>`. Las transcripciones **sí** se versionan en `cache/`.

## Arquitectura: un motor, dos esquemas
```
audio ─▶ [audio.apply_level L0-L3] ─▶ [asr.transcribe] ─▶ [extract rules|llm] ─▶ [verify literal] ─▶ (order) [validate_order]
```
`src/engine.py` expone `process_audio(audio_path, schema="interview"|"order", extractor="rules"|"llm", ...)`, que devuelve `transcript, fields, verified, device, elapsed_s, error` (+ `validation` para pedidos). El esquema solo cambia qué campos y reglas/prompt se usan (`config.yaml`, secciones `interview` y `order`); el código de ASR, verificación y métricas es el mismo. `process_transcript` aplica la misma lógica a transcripciones en caché (así corre el CI sin GPU).

Verificar que el motor no importa UI:
```bash
python -c "import sys, src.engine; assert not {'streamlit','gradio'} & set(sys.modules)"
```

## Decisiones clave
- **Normalización** (WER, CER y verificación): minúsculas, sin tildes (ñ→n), sin puntuación, separadores de miles eliminados (`6.500`→`6500`), espacios colapsados (`src/textnorm.py`).
- **Verificación literal:** cada campo lleva una *evidencia* (fragmento) que debe aparecer literalmente en la transcripción; para numéricos, la evidencia debe resolver al valor (`seis mil quinientos soles` → 6500). Si no: `sin_verificar`. Esto aplica igual a reglas y LLM (el LLM debe devolver la cita).
- **Números hablados:** parser de español hasta millones (`cien`, `treinta y cinco`, `dos mil veintiuno`, cifras con separadores). Limitación: no cubre decimales hablados ("doce con cincuenta").
- **GPU:** el dispositivo se lee de `model.model.device` (ctranslate2) en tiempo de ejecución, y la VRAM pico se mide con `nvidia-smi` (pico − VRAM en reposo). Si se pidió `cuda` y corrió en CPU, `process_audio` devuelve un `error` (sin fallback silencioso).
- **Glosario:** `asr.glossary_mechanism` en `config.yaml` (`hotwords` o `initial_prompt`). Verifica contra la documentación de tu versión de faster-whisper (`hotwords` requiere ≥ 1.0.3) y anota el resultado aquí: _(pendiente)_.
- **Escalera L0–L3:** L1 códec Opus 12 kbps mono; L2 pasa-banda 300–3400 Hz a 8 kHz; L3 = L1 + ruido rosa sintético a SNR 10 dB. La SNR se calcula como `10·log10(P_señal/P_ruido)` con potencias medias, y se **re-mide** tras mezclar (guardada como `snr_db_measured` y verificada en tests). Si L3 sigue perfecto, endurecer `ladder.l3.snr_db`.
- **Validación aritmética:** `Σ cantidad·precio − promoción` vs `total_dicho` (tolerancia en config). **Diagnóstico:** si las lecturas en palabras difieren en una sola palabra con distancia de edición relativa ≤ umbral → `error_asr`; si no → `error_hablante`. Se reporta cuántas veces acierta contra las trampas plantadas (`scripts/evaluate.py` → tabla de atrapados/perdidos/falsas alarmas por nivel).
- **Regression gate:** `.github/workflows/gate.yml` recalcula métricas desde el caché; los runners no tienen GPU, así que nunca transcribe.

## Corpus y desviaciones declaradas
| Clip | Duración (s) | | Clip | Duración (s) |
|---|---|---|---|---|
| interview_01 | 142 | | order_01 | 74 |
| interview_02 | 131 | | order_02 | 84 |
| interview_03 | 112 | | order_03 | 69 |
| interview_04 | 135 | | order_04 | 69 |
| interview_05 | 111 | | order_05 | 72 |

- **Duración de las llamadas de venta (≈ 1,2–1,4 min, menos de los 2–4 min pedidos):** se grabaron como *llamadas rápidas* de pedido a domicilio, que es el caso real del dominio restaurante: el cliente dicta el pedido, la dirección y el pago, y el vendedor confirma el total en poco más de un minuto. Alargarlas con conversación de relleno habría hecho el corpus menos realista sin agregar campos ni trampas. Consecuencia: ~5 min de audio de llamadas en total (frente a los 16–20 previstos), por lo que las métricas de la Tarea 2 tienen aún menos poder estadístico y sus intervalos de confianza son muy anchos.
- **Entrevistas (1,85–2,4 min):** tres de las cinco cumplen los 2 minutos; `interview_03` (112 s) e `interview_05` (111 s) quedan ligeramente por debajo.
- Los hablantes no leyeron los guiones palabra por palabra; las transcripciones de referencia se corrigen escuchando el audio (ver `data/ground_truth/review/`).

## Resultados
_(Pendiente: pegar aquí las tablas de `results/results_rules.json` / app, con IC al 95 % por bootstrap. Con ~5 clips por tarea los intervalos serán anchos; dilo explícitamente.)_

## Limitaciones
- Muestra muy pequeña (4–5 clips por tarea): sirve para ver efectos, no para estimar con precisión.
- Reglas calibradas para el menú/guiones de `config.yaml`; no generalizan a otros dominios sin reconfigurar.
- Ruido L3 sintético (rosa), no ruido ambiental real.
- **Nunca usar** para decisiones automáticas de contratación, ni para cobrar un pedido sin revisión humana.
