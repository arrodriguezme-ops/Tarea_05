"""Normalizacion de texto y numeros hablados en espanol.

Regla unica de normalizacion (WER, CER y verificacion literal):
minusculas, sin tildes (la n con tilde pasa a n), sin puntuacion, separadores de
miles dentro de cifras eliminados ("6.500" -> "6500"), espacios colapsados.
"""
import re
import unicodedata

UNITS = {
    "cero": 0, "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
    "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16, "diecisiete": 17,
    "dieciocho": 18, "diecinueve": 19, "veinte": 20, "veintiun": 21, "veintiuno": 21,
    "veintiuna": 21, "veintidos": 22, "veintitres": 23, "veinticuatro": 24,
    "veinticinco": 25, "veintiseis": 26, "veintisiete": 27, "veintiocho": 28,
    "veintinueve": 29,
}
TENS = {"treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70,
        "ochenta": 80, "noventa": 90}
HUNDREDS = {"cien": 100, "ciento": 100, "doscientos": 200, "doscientas": 200,
            "trescientos": 300, "trescientas": 300, "cuatrocientos": 400,
            "cuatrocientas": 400, "quinientos": 500, "quinientas": 500,
            "seiscientos": 600, "seiscientas": 600, "setecientos": 700,
            "setecientas": 700, "ochocientos": 800, "ochocientas": 800,
            "novecientos": 900, "novecientas": 900}
NUMBER_WORDS = set(UNITS) | set(TENS) | set(HUNDREDS) | {"mil", "millon", "millones"}
_DIGITS = re.compile(r"^\d+(?:\.\d+)?$")


def normalize(text: str) -> str:
    t = text.lower()
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    t = re.sub(r"(?<=\d)[.,](?=\d{3}(?!\d))", "", t)      # miles: 6.500 -> 6500
    t = re.sub(r"(?<=\d),(?=\d)", ".", t)                  # decimal: 12,5 -> 12.5
    t = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", t)              # puntos que no son decimales
    t = re.sub(r"[^a-z0-9. ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def tokens(text: str) -> list[str]:
    return normalize(text).split()


def _is_num(tok: str) -> bool:
    return tok in NUMBER_WORDS or bool(_DIGITS.match(tok))


def _eval_run(run: list[str]) -> float:
    total, current = 0.0, 0.0
    for tok in run:
        if tok == "y":
            continue
        if _DIGITS.match(tok):
            current += float(tok)
        elif tok == "mil":
            total += max(current, 1) * 1000
            current = 0
        elif tok in ("millon", "millones"):
            total += max(current, 1) * 1_000_000
            current = 0
        else:
            current += UNITS.get(tok) or TENS.get(tok) or HUNDREDS.get(tok) or 0
    value = total + current
    return int(value) if float(value).is_integer() else value


def number_spans(text: str) -> list[dict]:
    """Devuelve [{value, start, end, text}] con indices de token sobre normalize(text)."""
    toks = tokens(text)
    spans, i = [], 0
    while i < len(toks):
        if not _is_num(toks[i]):
            i += 1
            continue
        j = i + 1
        while j < len(toks):
            if _is_num(toks[j]) and not (_DIGITS.match(toks[j]) and _DIGITS.match(toks[j - 1])):
                j += 1
            elif toks[j] == "y" and toks[j - 1] in TENS and j + 1 < len(toks) \
                    and toks[j + 1] in UNITS:
                j += 1
            else:
                break
        spans.append({"value": _eval_run(toks[i:j]), "start": i, "end": j,
                      "text": " ".join(toks[i:j])})
        i = j
    return spans


_UNIT_W = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
           "nueve", "diez", "once", "doce", "trece", "catorce", "quince", "dieciseis",
           "diecisiete", "dieciocho", "diecinueve", "veinte", "veintiuno", "veintidos",
           "veintitres", "veinticuatro", "veinticinco", "veintiseis", "veintisiete",
           "veintiocho", "veintinueve"]
_TEN_W = {30: "treinta", 40: "cuarenta", 50: "cincuenta", 60: "sesenta", 70: "setenta",
          80: "ochenta", 90: "noventa"}
_HUN_W = {100: "ciento", 200: "doscientos", 300: "trescientos", 400: "cuatrocientos",
          500: "quinientos", 600: "seiscientos", 700: "setecientos", 800: "ochocientos",
          900: "novecientos"}


def number_to_words(n: int) -> str:
    """Entero 0..999999 a palabras (para comparar un total con su lectura hablada)."""
    n = int(n)
    if n < 30:
        return _UNIT_W[n]
    if n < 100:
        t, u = divmod(n, 10)
        return _TEN_W[t * 10] + (f" y {_UNIT_W[u]}" if u else "")
    if n < 1000:
        h, r = divmod(n, 100)
        if n == 100:
            return "cien"
        return _HUN_W[h * 100] + (f" {number_to_words(r)}" if r else "")
    k, r = divmod(n, 1000)
    head = "mil" if k == 1 else f"{number_to_words(k)} mil"
    return head + (f" {number_to_words(r)}" if r else "")


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def contains_literal(haystack: str, needle: str) -> bool:
    """Busqueda literal por palabras completas sobre texto ya normalizado."""
    n = normalize(needle)
    return bool(n) and f" {n} " in f" {normalize(haystack)} "
