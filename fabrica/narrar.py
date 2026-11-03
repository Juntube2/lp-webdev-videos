"""Gera a narração de um episódio e os tempos de cada palavra.

Uso: python fabrica/narrar.py episodios/<pasta>
Lê  <pasta>/episodio.json  (campos "roteiro", e opcionais "motor", "voz", "velocidade")
Gera <pasta>/narracao.mp3 e <pasta>/palavras.json

Motores:
  "edge"        (padrão, grátis) vozes neurais do Microsoft Edge via pacote edge-tts. Voz padrão pt-BR-AntonioNeural.
  "elevenlabs"  precisa da variável de ambiente ELEVENLABS_API_KEY. Voz padrão: Lucas.
"""
import asyncio, base64, json, os, re, sys, time, urllib.error, urllib.request
from pathlib import Path

EDGE_VOICE = "pt-BR-AntonioNeural"
EDGE_RATE = "+12%"
ELEVEN_VOICE = "7lu3ze7orhWaNeSPowWx"
ELEVEN_MODELS = ["eleven_v3", "eleven_multilingual_v2"]


def clean(text):
    """Remove etiquetas tipo [animado] e espaços duplicados."""
    return re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", " ", text)).strip()


# ---------------- Edge (grátis) ----------------
async def _edge(text, voice, rate, mp3_path):
    import edge_tts
    try:
        comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    except TypeError:  # versões antigas já emitem WordBoundary por padrão
        comm = edge_tts.Communicate(text, voice, rate=rate)
    words = []
    with open(mp3_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                st = chunk["offset"] / 1e7
                words.append({"text": chunk["text"], "start": round(st, 3), "end": round(st + chunk["duration"] / 1e7, 3)})
    return words


def attach_punctuation(words, text):
    """O Edge devolve palavras sem pontuação; recoloca a pontuação do roteiro para a legenda e para casar as cenas."""
    script = text.split()
    out, j = [], 0
    def core(s): return re.sub(r"[^\wÀ-ÿ]", "", s.lower())
    for w in words:
        k = j
        while k < len(script) and core(script[k]) != core(w["text"]) and k < j + 4:
            k += 1
        if k < len(script) and core(script[k]) == core(w["text"]):
            w = dict(w, text=script[k]); j = k + 1
        out.append(w)
    return out


def narrar_edge(ep, folder):
    text = clean(ep["roteiro"])
    voice = ep.get("voz") if str(ep.get("voz", "")).startswith("pt-") else EDGE_VOICE
    rate = ep.get("velocidade", EDGE_RATE)
    last = None
    for attempt in range(4):
        try:
            words = asyncio.run(_edge(text, voice, rate, folder / "narracao.mp3"))
            if words and (folder / "narracao.mp3").stat().st_size > 10000:
                return attach_punctuation(words, text), f"edge:{voice}"
            last = "resposta vazia"
        except Exception as e:
            last = repr(e)
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"Edge TTS falhou: {last}")


# ---------------- ElevenLabs (pago) ----------------
def _eleven(text, voice, model, key):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128"
    body = json.dumps({"text": text, "model_id": model, "language_code": "pt",
                       "voice_settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.3, "use_speaker_boost": True}}).encode()
    req = urllib.request.Request(url, data=body, headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def words_from_alignment(al):
    chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    words, cur, t0, t1, in_tag = [], "", None, None, False
    for c, a, b in zip(chars, st, en):
        if c == "[": in_tag = True
        if in_tag:
            if c == "]": in_tag = False
            continue
        if c.isspace():
            if cur.strip(): words.append({"text": cur, "start": round(t0, 3), "end": round(t1, 3)})
            cur, t0 = "", None
            continue
        if t0 is None: t0 = a
        cur += c; t1 = b
    if cur.strip(): words.append({"text": cur, "start": round(t0, 3), "end": round(t1, 3)})
    return words


def narrar_eleven(ep, folder):
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key: raise RuntimeError("ELEVENLABS_API_KEY não configurada")
    voice = ep.get("voz") if ep.get("voz") and not str(ep["voz"]).startswith("pt-") else ELEVEN_VOICE
    text = ep["roteiro"].strip(); last = None
    for model in ([ep["modelo"]] if ep.get("modelo") else []) + ELEVEN_MODELS:
        try:
            data = _eleven(text, voice, model, key)
            (folder / "narracao.mp3").write_bytes(base64.b64decode(data["audio_base64"]))
            return words_from_alignment(data["alignment"]), f"elevenlabs:{model}"
        except urllib.error.HTTPError as e:
            last = f"{model}: HTTP {e.code} {e.read()[:200]!r}"
        except Exception as e:
            last = f"{model}: {e!r}"
    raise RuntimeError(f"ElevenLabs falhou: {last}")


def main(folder):
    folder = Path(folder)
    ep = json.loads((folder / "episodio.json").read_text(encoding="utf-8"))
    motor = ep.get("motor", os.environ.get("TTS_MOTOR", "edge"))
    try:
        words, used = (narrar_eleven if motor == "elevenlabs" else narrar_edge)(ep, folder)
    except Exception as e:
        if motor == "elevenlabs":
            print(f"{e} — usando a voz grátis do Edge", file=sys.stderr)
            words, used = narrar_edge(ep, folder)
        else:
            raise SystemExit(str(e))
    (folder / "palavras.json").write_text(json.dumps(words, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"ok: {len(words)} palavras, {used}")


if __name__ == "__main__":
    main(sys.argv[1])
