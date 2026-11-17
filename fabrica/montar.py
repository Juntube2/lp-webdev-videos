"""Monta um vídeo vertical (1080x1920) de dicas de games a partir de clipes de gameplay.

Uso: python fabrica/montar.py episodios/<pasta>   -> gera <pasta>/video.mp4
Precisa de: <pasta>/episodio.json, <pasta>/narracao.mp3, <pasta>/palavras.json (gerados por narrar.py)
Os clipes ficam em gameplay/<jogo>/*.mp4 e são descritos em gameplay/catalogo.json.
Formato completo do episodio.json em fabrica/README.md.
"""
import json, math, re, subprocess, sys, unicodedata, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
FONTS = ROOT / "fontes"
F_BLACK, F_BOLD = str(FONTS / "Inter-Black.otf"), str(FONTS / "Inter-ExtraBold.otf")
YELLOW, WHITE, BLACK = (255, 212, 0), (255, 255, 255), (0, 0, 0)
GAME_COLORS = {"valorant": (255, 70, 85), "fortnite": (80, 140, 255)}
FG_CY = 900            # centro vertical do gameplay
CAPTION_Y = 1170       # legenda palavra por palavra (parte de baixo do gameplay)
TITLE_Y = 300          # título fixo no topo
BAND_TOP = 1400        # faixa de elementos abaixo do gameplay
BAND_BOTTOM = 1890
_fc = {}


def font(path, size):
    k = (path, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]


def hexrgb(h, default=(254, 44, 85)):
    if not h: return default
    if isinstance(h, (list, tuple)): return tuple(h)
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def tlen(txt, f): return ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(txt, font=f)


def fit_font(path, txt, max_w, start, minimum=28):
    s = start
    while s > minimum and tlen(txt, font(path, s)) > max_w: s -= 4
    return font(path, s)


def wrap(txt, fpath, size, max_w, max_lines=4):
    f = font(fpath, size); lines, cur = [], ""
    for w in txt.split():
        t = (cur + " " + w).strip()
        if tlen(t, f) <= max_w: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines[:max_lines]


def text_center(d, cx, cy, txt, f, fill, stroke=0, stroke_fill=BLACK):
    bb = d.textbbox((0, 0), txt, font=f, stroke_width=stroke)
    d.text((cx - (bb[2] + bb[0]) / 2, cy - (bb[3] + bb[1]) / 2), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)


def rounded(d, box, r, fill, outline=None, width=0): d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def sticker_frame(img, border=10):
    pad = border + 18
    big = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0)); big.paste(img, (pad, pad), img)
    m = big.split()[3].filter(ImageFilter.MaxFilter(border * 2 + 1))
    out = Image.new("RGBA", big.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", big.size, (0, 0, 0, 255)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * .55)))
    out.alpha_composite(sh, (6, 12))
    wl = Image.new("RGBA", big.size, (255, 255, 255, 255)); wl.putalpha(m)
    out.alpha_composite(wl); out.alpha_composite(big)
    return out


def card(w, h, fn, frame=True):
    im = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0)); fn(ImageDraw.Draw(im), im)
    return sticker_frame(im) if frame else im


# ---------------- elementos sobrepostos ----------------
def p_numero(p, ctx):
    size = 200; txt = str(p.get("texto", "1")); bg = hexrgb(p.get("cor"), ctx["cor"])
    return card(size, size, lambda d, im: (rounded(d, (0, 0, size, size), 40, bg), text_center(d, size / 2, size / 2, txt, fit_font(F_BLACK, txt, 160, 120), WHITE)))


def p_selo(p, ctx):
    txt = str(p.get("texto", "")); bg = hexrgb(p.get("cor"), ctx["cor"]); fg = hexrgb(p.get("cor_texto"), WHITE)
    f = fit_font(F_BLACK, txt, 860, 76); w = int(tlen(txt, f)) + 80
    return card(w, 130, lambda d, im: (rounded(d, (0, 0, w, 130), 30, bg), text_center(d, w / 2, 65, txt, f, fg)))


def p_texto(p, ctx):
    txt = str(p.get("texto", "")); bg = hexrgb(p.get("cor"), WHITE); fg = hexrgb(p.get("cor_texto"), (20, 20, 20))
    lines = wrap(txt, F_BLACK, 70, 820, 3); h = 70 + 88 * len(lines)
    def f(d, im):
        rounded(d, (0, 0, 900, h), 34, bg)
        for i, ln in enumerate(lines): text_center(d, 450, 62 + i * 88, ln, font(F_BLACK, 70), fg)
    return card(900, h, f)


def p_lista(p, ctx):
    itens = [str(t) for t in p.get("itens", [])][:4]; w = 900; h = 60 + 104 * len(itens); mark = p.get("marcar", "check")
    def f(d, im):
        rounded(d, (0, 0, w, h), 34, (250, 250, 250))
        for i, t in enumerate(itens):
            y = 34 + i * 104
            col = (230, 40, 50) if mark == "x" else (39, 160, 90)
            rounded(d, (34, y, 104, y + 70), 18, col)
            if mark == "x":
                d.line((52, y + 18, 86, y + 52), fill=WHITE, width=10); d.line((52, y + 52, 86, y + 18), fill=WHITE, width=10)
            else:
                d.line((50, y + 36, 64, y + 52), fill=WHITE, width=10); d.line((64, y + 52, 90, y + 18), fill=WHITE, width=10)
            d.text((130, y + 4), t, font=fit_font(F_BLACK, t, w - 160, 54), fill=(25, 25, 25))
    return card(w, h, f)


def p_versus(p, ctx):
    a, b = str(p.get("a", "A")), str(p.get("b", "B")); ca, cb = hexrgb(p.get("cor_a"), (39, 160, 90)), hexrgb(p.get("cor_b"), (230, 60, 60))
    w, h = 920, 220
    def f(d, im):
        rounded(d, (0, 0, 410, h), 34, ca); rounded(d, (510, 0, w, h), 34, cb)
        text_center(d, 205, h / 2, a, fit_font(F_BLACK, a, 360, 76), WHITE); text_center(d, 715, h / 2, b, fit_font(F_BLACK, b, 360, 76), WHITE)
        d.ellipse((400, 50, 520, 170), fill=(15, 15, 15)); text_center(d, 460, 110, "VS", font(F_BLACK, 46), YELLOW)
    return card(w, h, f)


def p_riscado(p, ctx):
    txt = str(p.get("texto", "")); lines = wrap(txt, F_BLACK, 68, 760, 2); h = 70 + 86 * len(lines)
    def f(d, im):
        rounded(d, (0, 0, 860, h), 34, (245, 245, 245))
        for i, ln in enumerate(lines): text_center(d, 430, 62 + i * 86, ln, font(F_BLACK, 68), (40, 40, 40))
        for i in range(len(lines)):
            y = 62 + i * 86
            d.line((40, y + 4, 820, y - 4), fill=(230, 40, 50), width=9)
        rounded(d, (760, 10, 840, 90), 20, (230, 40, 50)); d.line((782, 32, 818, 68), fill=WHITE, width=9); d.line((782, 68, 818, 32), fill=WHITE, width=9)
    return card(860, h, f)


def p_carimbo(p, ctx):
    txt = str(p.get("texto", "")); bg = hexrgb(p.get("cor"), ctx["cor"]); f = fit_font(F_BLACK, txt, 780, 96)
    return card(860, 200, lambda d, im: (rounded(d, (0, 0, 860, 200), 28, bg), text_center(d, 430, 100, txt, f, WHITE))).rotate(-4, expand=True, resample=Image.BICUBIC)


def p_pergunta(p, ctx):
    """Bolha estilo comentário com uma dúvida comum (sem inventar usuário)."""
    txt = str(p.get("texto", "")); rot = str(p.get("rotulo", "Dúvida que todo mundo tem:"))
    lines = wrap(txt, F_BOLD, 50, 780, 3); h = 120 + 64 * len(lines)
    def f(d, im):
        rounded(d, (0, 0, 900, h), 30, (255, 255, 255))
        d.ellipse((30, 28, 90, 88), fill=ctx["cor"]); text_center(d, 60, 58, "?", font(F_BLACK, 44), WHITE)
        d.text((112, 36), rot, font=font(F_BOLD, 34), fill=(120, 120, 130))
        for i, ln in enumerate(lines): d.text((40, 108 + i * 64), ln, font=font(F_BOLD, 50), fill=(20, 20, 20))
    return card(900, h, f)


def p_parte2(p, ctx):
    t, sub = str(p.get("texto", "PARTE 2")), str(p.get("sub", "segue pra não perder"))
    return card(760, 280, lambda d, im: (rounded(d, (0, 0, 760, 280), 40, hexrgb(p.get("cor"), (254, 44, 85))),
                                         text_center(d, 380, 105, t, fit_font(F_BLACK, t, 680, 116), WHITE),
                                         text_center(d, 380, 212, sub, fit_font(F_BOLD, sub, 680, 48), WHITE)))


PROPS = {"numero": p_numero, "selo": p_selo, "texto": p_texto, "lista": p_lista, "versus": p_versus, "riscado": p_riscado,
         "carimbo": p_carimbo, "pergunta": p_pergunta, "parte2": p_parte2}
SFX = {"numero": "ding", "riscado": "buzz", "carimbo": "thump", "parte2": "rise", "selo": "pop2", "versus": "thump",
       "lista": "pop2", "texto": "whoosh", "pergunta": "pop2", "marcador": "ping"}


# ---------------- clipes ----------------
def probe(path):
    out = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration", "-of", "json", str(path)]))
    v = next(s for s in out["streams"] if s["codec_type"] == "video")
    return v["width"], v["height"], float(out["format"]["duration"]), any(s["codec_type"] == "audio" for s in out["streams"])


def clip_frames(path, start, dur, zoom, foco_x):
    """Gera os quadros do clipe já recortados e escalados para largura 1080 (altura proporcional)."""
    sw, sh, sdur, _ = probe(path)
    zoom = max(1.0, min(2.2, float(zoom)))
    cw = int(sw / zoom) // 2 * 2; ch = sh
    fh = int(round(W * ch / cw / 2) * 2)
    if fh > 1150:  # limita a altura do gameplay na tela
        fh = 1150; ch = int(cw * fh / W) // 2 * 2
    cx = int((sw - cw) * max(0.0, min(1.0, float(foco_x))))
    cy = (sh - ch) // 2
    start = max(0.0, min(float(start), max(0.0, sdur - 0.5)))
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", str(path), "-t", f"{dur + 0.2:.3f}", "-an",
           "-vf", f"fps={FPS},crop={cw}:{ch}:{cx}:{cy},scale={W}:{fh}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = W * fh * 3; last = None
    try:
        while True:
            buf = p.stdout.read(n)
            if len(buf) < n: break
            last = Image.frombuffer("RGB", (W, fh), buf, "raw", "RGB", 0, 1); yield last
        while last is not None:  # clipe acabou antes da cena: congela o último quadro
            yield last
    finally:
        p.kill(); p.stdout.close(); p.wait()


def background_from(fg):
    small = fg.resize((54, 96), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    bg = small.resize((W, H), Image.BILINEAR)
    return Image.blend(bg, Image.new("RGB", (W, H), (0, 0, 0)), 0.45)


# ---------------- legenda e título ----------------
def caption_img(word, color):
    word = word.strip().strip(".,:;!?…\"'()").upper()
    f = font(F_BLACK, 118); stroke = 13
    bb = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), word, font=f, stroke_width=stroke)
    while bb[2] - bb[0] > W - 80 and f.size > 40:
        f = font(F_BLACK, f.size - 8); bb = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), word, font=f, stroke_width=stroke)
    im = Image.new("RGBA", (max(1, bb[2] - bb[0] + 40), bb[3] - bb[1] + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((20 - bb[0], 20 - bb[1]), word, font=f, fill=color, stroke_width=stroke, stroke_fill=BLACK)
    return im


def title_img(txt, cor):
    lines = wrap(txt.upper(), F_BLACK, 74, 900, 3); h = 50 + 90 * len(lines)
    def f(d, im):
        rounded(d, (0, 0, 980, h), 30, WHITE)
        d.rectangle((0, h - 14, 980, h), fill=cor); rounded(d, (0, h - 30, 980, h), 30, cor)
        for i, ln in enumerate(lines): text_center(d, 490, 50 + i * 90, ln, font(F_BLACK, 74), (15, 15, 15))
    return card(980, h, f)


def credit_img(txt):
    txt = f"gameplay: {txt}"; f = fit_font(F_BOLD, txt, 900, 34); w = int(tlen(txt, f)) + 40
    im = Image.new("RGBA", (w, 56), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rounded(d, (0, 0, w, 56), 28, (0, 0, 0, 150)); text_center(d, w / 2, 28, txt, f, (235, 235, 235))
    return im


# ---------------- estilo minimalista (padrão) ----------------
MIN_BG = (10, 10, 12)


def min_title_img(txt):
    lines = wrap(txt, F_BOLD, 62, 940, 3); lh = 78
    im = Image.new("RGBA", (W, 20 + lh * len(lines)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines): text_center(d, W / 2, 10 + lh * i + lh / 2, ln, font(F_BOLD, 62), WHITE)
    return im


def min_chunks(words, max_words=3):
    """Agrupa as palavras em blocos curtos (quebra em pontuação) para a legenda."""
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= max_words or re.search(r"[.,:;!?…]$", w["text"].strip()):
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    return [{"start": c[0]["start"], "end": c[-1]["end"], "text": " ".join(x["text"] for x in c).strip().rstrip(",;:.")} for c in chunks]


def min_caption_img(txt):
    f = fit_font(F_BOLD, txt, W - 140, 66, 40)
    bb = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), txt, font=f)
    im = Image.new("RGBA", (bb[2] - bb[0] + 60, bb[3] - bb[1] + 60), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((30 - bb[0], 34 - bb[1]), txt, font=f, fill=(0, 0, 0, 200))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(im).text((30 - bb[0], 30 - bb[1]), txt, font=f, fill=WHITE)
    return im


def render_minimal(ep, folder, words, dur, scenes, starts, enc):
    title = min_title_img(ep["titulo_tela"]) if ep.get("titulo_tela") else None
    chunks = min_chunks(words); caps = {}
    fi = 0
    for si, sc in enumerate(scenes):
        st, en = starts[si], starts[si + 1]; sdur = max(0.1, en - st)
        clip = REPO / sc["clipe"]
        if not clip.exists(): raise SystemExit(f"clipe não encontrado: {sc['clipe']}")
        frames = clip_frames(clip, float(sc.get("de", 0)), sdur, sc.get("zoom", 1.7), sc.get("foco_x", 0.5))
        while fi < int(en * FPS) and fi < int(dur * FPS):
            t = fi / FPS
            fg = next(frames)
            frame = Image.new("RGBA", (W, H), MIN_BG + (255,))
            fy = int(FG_CY - fg.height / 2)
            frame.paste(fg, (0, fy))
            if title is not None:
                frame.alpha_composite(title, (0, max(60, fy - title.height - 50)))
            cur = next((c for i, c in enumerate(chunks) if c["start"] <= t < (chunks[i + 1]["start"] if i + 1 < len(chunks) else c["end"] + 0.4)), None)
            if cur:
                if cur["text"] not in caps: caps[cur["text"]] = min_caption_img(cur["text"])
                paste_center(frame, caps[cur["text"]], W / 2, fy + fg.height + 110)
            enc.stdin.write(frame.convert("RGB").tobytes()); fi += 1


def marker_draw(frame, fg_box, m, t_local, cor):
    """Círculo pulsante + rótulo sobre um ponto do gameplay (x, y de 0 a 1 dentro do gameplay)."""
    x0, y0, fw, fh = fg_box
    x = x0 + float(m.get("x", .5)) * fw; y = y0 + float(m.get("y", .5)) * fh
    r = 46 + 10 * math.sin(t_local * 8)
    d = ImageDraw.Draw(frame)
    for rr, wd, col in ((r + 6, 12, BLACK), (r, 8, cor)):
        d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=col, width=wd)
    if m.get("texto"):
        txt = str(m["texto"]).upper(); f = font(F_BLACK, 46); tw = tlen(txt, f)
        lx = min(max(x - tw / 2 - 20, 20), W - tw - 60); ly = y - r - 90 if y - r - 90 > y0 else y + r + 20
        rounded(d, (lx, ly, lx + tw + 40, ly + 68), 18, cor); d.text((lx + 20, ly + 8), txt, font=f, fill=WHITE)
    if m.get("seta", True):
        ax, ay = x, y - r - 8
        d.polygon([(ax, ay), (ax - 22, ay - 34), (ax + 22, ay - 34)], fill=cor, outline=BLACK)


# ---------------- tempo ----------------
def norm(t): return unicodedata.normalize("NFC", re.sub(r"[^\wÀ-ÿ]", "", t.lower()))


def scene_starts(scenes, words):
    starts, wi = [], 0
    for k, sc in enumerate(scenes):
        if k == 0: starts.append(0.0); continue
        key = norm(sc.get("inicio", "")); j = wi
        while j < len(words) and norm(words[j]["text"]) != key: j += 1
        if j < len(words): starts.append(words[j]["start"]); wi = j + 1
        else: starts.append(starts[-1] + 2.5); print(f"aviso: palavra de início '{sc.get('inicio')}' não encontrada", file=sys.stderr)
    return starts


def ease_back(t):
    t = max(0, min(1, t)); c = 1.7
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def paste_center(canvas, im, cx, cy, scale=1.0):
    if scale <= 0.01: return
    if abs(scale - 1) > 1e-3: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


# ---------------- principal ----------------
def main(folder):
    folder = Path(folder)
    ep = json.loads((folder / "episodio.json").read_text(encoding="utf-8"))
    jogo = ep.get("jogo", "valorant"); cor = hexrgb(ep.get("cor"), GAME_COLORS.get(jogo, (254, 44, 85)))
    cap_color = hexrgb(ep.get("cor_legenda"), WHITE)
    ctx = {"cor": cor}
    words = [w for w in json.loads((folder / "palavras.json").read_text(encoding="utf-8")) if w["text"].strip()]
    audio = folder / "narracao.mp3"
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(audio)]).strip()) + 0.7
    scenes = ep["cenas"]; starts = scene_starts(scenes, words) + [dur]
    title = title_img(ep["titulo_tela"], cor) if ep.get("titulo_tela") else None
    credit = credit_img(ep["credito"]) if ep.get("credito") else None
    minimal = ep.get("estilo", "minimalista") == "minimalista"
    built = []
    for sc in ([] if minimal else scenes):
        items = []
        for p in sc.get("elementos", [])[:3]:
            fn = PROPS.get(p.get("tipo"))
            if fn: items.append((p["tipo"], fn(p, ctx)))
            elif p.get("tipo") != "marcador": print(f"aviso: tipo desconhecido {p.get('tipo')}", file=sys.stderr)
        built.append(items)
    caps, sfx, audio_parts = {}, [], []
    tmp_video = folder / "_video.mp4"
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(tmp_video)], stdin=subprocess.PIPE)
    fi = 0
    if minimal:
        render_minimal(ep, folder, words, dur, scenes, starts, enc)
    for si, sc in enumerate([] if minimal else scenes):
        st, en = starts[si], starts[si + 1]; sdur = max(0.1, en - st)
        clip = REPO / sc["clipe"]
        if not clip.exists(): raise SystemExit(f"clipe não encontrado: {sc['clipe']}")
        de = float(sc.get("de", 0)); zoom = sc.get("zoom", 1.35); fx = sc.get("foco_x", 0.5)
        audio_parts.append((clip, de, sdur, bool(sc.get("mudo"))))
        frames = clip_frames(clip, de, sdur, zoom, fx)
        sfx.append(("whoosh" if si else "pop", st))
        marcadores = [p for p in sc.get("elementos", []) if p.get("tipo") == "marcador"]
        while fi < int(en * FPS) and fi < int(dur * FPS):
            t = fi / FPS; lt = t - st
            fg = next(frames)
            frame = background_from(fg).convert("RGBA")
            # leve "punch-in" no começo de cada cena
            z = 1.0 + 0.04 * max(0.0, 1 - lt / 0.35)
            fgi = fg if z <= 1.001 else fg.resize((int(W * z), int(fg.height * z)), Image.BILINEAR).crop(
                (int((W * z - W) / 2), int((fg.height * z - fg.height) / 2), int((W * z - W) / 2) + W, int((fg.height * z - fg.height) / 2) + fg.height))
            fy = int(FG_CY - fg.height / 2)
            frame.paste(fgi, (0, fy))
            d = ImageDraw.Draw(frame)
            d.line((0, fy, W, fy), fill=cor, width=6); d.line((0, fy + fg.height, W, fy + fg.height), fill=cor, width=6)
            for m in marcadores:
                if lt >= float(m.get("aos", 0.3)):
                    if fi == int((st + float(m.get("aos", 0.3))) * FPS): sfx.append(("ping", t))
                    marker_draw(frame, (0, fy, W, fg.height), m, lt, cor)
            if title is not None:
                paste_center(frame, title, W / 2, TITLE_Y if fy - 40 > TITLE_Y + title.height / 2 else fy - title.height / 2 - 20,
                             scale=ease_back(t / 0.35) if t < 0.4 else 1.0)
            band = [(tipo, obj) for tipo, obj in built[si] if tipo != "numero"]
            total = sum(o.height for _, o in band) + 10 * max(0, len(band) - 1)
            sc_fit = min(1.0, (BAND_BOTTOM - BAND_TOP) / total) if total else 1.0
            y_cur = BAND_TOP + ((BAND_BOTTOM - BAND_TOP) - total * sc_fit) / 2
            for k, (tipo, obj) in enumerate(built[si]):
                delay = 0.15 + k * 0.4
                if tipo == "numero": cx, cy = 140, fy + 120
                else:
                    cx, cy = W / 2, y_cur + obj.height * sc_fit / 2; y_cur += obj.height * sc_fit + 10
                if lt < delay: continue
                if fi == int((st + delay) * FPS): sfx.append((SFX.get(tipo, "whoosh"), t))
                base = 1.0 if tipo == "numero" else sc_fit
                paste_center(frame, obj, cx, cy + 4 * math.sin(t * 2.5 + k), scale=base * ease_back((lt - delay) / 0.3))
            if credit is not None:
                paste_center(frame, credit, W / 2, H - 42)
            cur = next((w for w in words if w["start"] <= t < max(w["end"], w["start"] + 0.12) + 0.05), None)
            if cur:
                key = cur["text"]
                if key not in caps: caps[key] = caption_img(key, cap_color)
                paste_center(frame, caps[key], W / 2, CAPTION_Y, scale=0.88 + 0.12 * ease_back((t - cur["start"]) / 0.12))
            enc.stdin.write(frame.convert("RGB").tobytes()); fi += 1
    enc.stdin.close(); enc.wait()
    if minimal:
        audio_parts = [(REPO / sc["clipe"], float(sc.get("de", 0)), max(0.1, starts[i + 1] - starts[i]), bool(sc.get("mudo"))) for i, sc in enumerate(scenes)]
        sfx = []
    game_audio(audio_parts, folder / "_game.wav")
    make_sfx(sfx, dur, folder / "_sfx.wav")
    gv = float(ep.get("volume_jogo", 0.22))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp_video), "-i", str(audio), "-i", str(folder / "_game.wav"), "-i", str(folder / "_sfx.wav"),
                    "-filter_complex", f"[1:a]volume=1.0[v];[2:a]volume={gv}[g];[3:a]volume=0.45[s];[v][g][s]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.95[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(folder / "video.mp4")], check=True)
    for f in ("_video.mp4", "_game.wav", "_sfx.wav"): (folder / f).unlink(missing_ok=True)
    print(f"ok: {folder / 'video.mp4'} ({dur:.1f}s)")


def game_audio(parts, out):
    """Concatena o áudio original dos clipes, cena por cena (silêncio se o clipe não tiver áudio)."""
    args, filt = [], []
    for i, (clip, de, d, mudo) in enumerate(parts):
        has_audio = probe(clip)[3] and not mudo
        if has_audio: args += ["-ss", f"{de:.3f}", "-t", f"{d + 0.2:.3f}", "-i", str(clip)]
        else: args += ["-f", "lavfi", "-t", f"{d:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
        filt.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,apad,atrim=0:{d:.3f},asetpts=N/SR/TB[a{i}]")
    filt.append("".join(f"[a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[out]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args, "-filter_complex", ";".join(filt), "-map", "[out]", str(out)], check=True)


def synth(kind, sr, rnd):
    def tt(sec): return np.arange(int(sec * sr)) / sr
    if kind in ("pop", "pop2"):
        t = tt(0.09); f0 = 900 if kind == "pop" else 1300
        return np.sin(2 * np.pi * (f0 - 5000 * t) * t) * np.exp(-t * 45)
    if kind == "ding":
        t = tt(0.8); return (np.sin(2 * np.pi * 1318 * t) + .5 * np.sin(2 * np.pi * 2637 * t)) * np.exp(-t * 6) * .5
    if kind == "ping":
        t = tt(0.5); return np.sin(2 * np.pi * 1760 * t) * np.exp(-t * 9) * .45
    if kind == "buzz":
        t = tt(0.4); return (np.sign(np.sin(2 * np.pi * 110 * t)) + .6 * np.sign(np.sin(2 * np.pi * 116 * t))) * np.minimum(1, (0.4 - t) * 10) * .25
    if kind == "thump":
        t = tt(0.35); return (np.sin(2 * np.pi * (60 + 120 * np.exp(-t * 25)) * t) * np.exp(-t * 9) + rnd.standard_normal(len(t)) * np.exp(-t * 40) * .3) * .9
    if kind == "rise":
        t = tt(0.6); f = 300 + 1500 * (t / t[-1]) ** 2
        noise = np.convolve(rnd.standard_normal(len(t)), np.ones(10) / 10, "same")
        return (np.sin(2 * np.pi * np.cumsum(f) / sr) * .25 + noise * .6) * (t / t[-1]) * np.exp(-np.maximum(0, t - .5) * 40)
    t = tt(0.28); noise = np.convolve(rnd.standard_normal(len(t)), np.ones(18) / 18, "same")
    return noise * np.sin(np.pi * t / t[-1]) ** 2 * 0.8


def make_sfx(events, dur, path, sr=44100):
    buf = np.zeros(int((dur + 2) * sr)); rnd = np.random.default_rng(1)
    for kind, t in events:
        s = synth(kind, sr, rnd); i = int(t * sr); buf[i:i + len(s)] += s[: len(buf) - i]
    buf = np.clip(buf, -1, 1)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((buf * 32767 * 0.8).astype(np.int16).tobytes())


if __name__ == "__main__":
    main(sys.argv[1])
