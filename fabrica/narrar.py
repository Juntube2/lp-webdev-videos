"""Gera a narração de um episódio no ElevenLabs (API) e os tempos de cada palavra.

Uso: python fabrica/narrar.py episodios/<pasta>
Lê  <pasta>/episodio.json  (campo "roteiro")
Gera <pasta>/narracao.mp3 e <pasta>/palavras.json
Precisa da variável de ambiente ELEVENLABS_API_KEY.
"""
import base64, json, os, re, sys, time, urllib.error, urllib.request
from pathlib import Path

VOICE_DEFAULT = "7lu3ze7orhWaNeSPowWx"   # Lucas - Engaging, Captivating and Kind (pt-BR)
MODELS = ["eleven_v3", "eleven_multilingual_v2"]


def tts(text, voice, model, key):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128"
    body = json.dumps({"text": text, "model_id": model, "language_code": "pt",
                       "voice_settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.3, "use_speaker_boost": True}}).encode()
    req = urllib.request.Request(url, data=body, headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "application/json"})
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


def main(folder):
    folder = Path(folder)
    ep = json.loads((folder / "episodio.json").read_text(encoding="utf-8"))
    key = os.environ["ELEVENLABS_API_KEY"]
    voice = ep.get("voz", VOICE_DEFAULT)
    text = ep["roteiro"].strip()
    last = None
    for model in ([ep["modelo"]] if ep.get("modelo") else []) + MODELS:
        for attempt in range(3):
            try:
                data = tts(text, voice, model, key)
                break
            except urllib.error.HTTPError as e:
                last = f"{model}: HTTP {e.code} {e.read()[:300]!r}"
                if e.code in (429, 500, 502, 503): time.sleep(20 * (attempt + 1)); continue
                data = None; break
            except Exception as e:  # rede
                last = f"{model}: {e}"; time.sleep(10); data = None
        else:
            data = None
        if data: break
        print("falhou:", last, file=sys.stderr)
    if not data:
        raise SystemExit(f"Narração falhou: {last}")
    (folder / "narracao.mp3").write_bytes(base64.b64decode(data["audio_base64"]))
    al = data.get("normalized_alignment") or data["alignment"]
    words = words_from_alignment(al)
    # normalized_alignment pode expandir números/siglas; se a contagem divergir muito do roteiro, usa o alinhamento original
    if data.get("alignment") and abs(len(words) - len(re.sub(r"\[[^\]]*\]", "", text).split())) > 2:
        words = words_from_alignment(data["alignment"])
    (folder / "palavras.json").write_text(json.dumps(words, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"ok: {len(words)} palavras, modelo {model}")


if __name__ == "__main__":
    main(sys.argv[1])
