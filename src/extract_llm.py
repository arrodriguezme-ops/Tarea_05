"""Extraccion con un LLM que devuelve JSON estructurado. Prompt y modelo viven en config.yaml."""
import json
import os
import re


def extract_llm(transcript: str, schema: str, cfg: dict) -> dict:
    from dotenv import load_dotenv
    import anthropic

    load_dotenv()
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("Falta ANTHROPIC_API_KEY en .env")
    lcfg = cfg["llm"]
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=lcfg["model"], max_tokens=lcfg["max_tokens"], temperature=lcfg["temperature"],
        system=lcfg["system_prompt"],
        messages=[{"role": "user",
                   "content": f"{lcfg['schemas'][schema]}\n\nTRANSCRIPCION:\n{transcript}"}],
    )
    raw = "".join(b.text for b in msg.content if b.type == "text")
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError(f"El LLM no devolvio JSON: {raw[:200]}")
    data = json.loads(m.group(0))
    fields = cfg[schema]["fields"]
    return {k: {"value": (data.get(k) or {}).get("value"),
                "evidence": (data.get(k) or {}).get("evidence")} for k in fields}
