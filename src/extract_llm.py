"""Extraccion con un LLM que devuelve JSON estructurado. Prompt y modelo viven en config.yaml."""
import json
import os
import re


def _call_anthropic(prompt: str, lcfg: dict) -> str:
    import anthropic
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("Falta ANTHROPIC_API_KEY en .env")
    msg = anthropic.Anthropic().messages.create(
        model=lcfg["model"], max_tokens=lcfg["max_tokens"], temperature=lcfg["temperature"],
        system=lcfg["system_prompt"], messages=[{"role": "user", "content": prompt}])
    return "".join(b.text for b in msg.content if b.type == "text")


def _call_google(prompt: str, lcfg: dict) -> str:
    """Gemini via REST (Google AI Studio). La clave va en el header, nunca en la URL."""
    import urllib.request
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("Falta GOOGLE_API_KEY en .env")
    body = {"systemInstruction": {"parts": [{"text": lcfg["system_prompt"]}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": lcfg["temperature"], "maxOutputTokens": lcfg["max_tokens"],
                                 "responseMimeType": "application/json"}}
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{lcfg['model']}:generateContent",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
    import time
    import urllib.error
    for attempt in range(5):  # 429/503 son transitorios
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.load(r)
            break
        except (urllib.error.HTTPError, urllib.error.URLError, ConnectionError) as e:
            transient = not isinstance(e, urllib.error.HTTPError) or e.code in (429, 503)
            if not transient or attempt == 4:
                raise
            time.sleep(3 * 2 ** attempt)
    return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])


PROVIDERS = {"anthropic": _call_anthropic, "google": _call_google}


_LAST = [0.0]


def extract_llm(transcript: str, schema: str, cfg: dict) -> dict:
    from dotenv import load_dotenv

    load_dotenv()
    lcfg = cfg["llm"]
    prompt = "\n\n".join([lcfg["schemas"][schema], "TRANSCRIPCION:", transcript])
    import time
    time.sleep(max(0.0, _LAST[0] + lcfg.get("min_interval_s", 0) - time.time()))
    raw = PROVIDERS[lcfg["provider"]](prompt, lcfg)
    _LAST[0] = time.time()
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError(f"El LLM no devolvio JSON: {raw[:200]}")
    data = json.loads(m.group(0))
    fields = cfg[schema]["fields"]
    return {k: {"value": (data.get(k) or {}).get("value"),
                "evidence": (data.get(k) or {}).get("evidence")} for k in fields}
