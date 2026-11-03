"""Monta o vídeo vertical (1080x1920) de um episódio a partir de episodio.json + narracao.mp3 + palavras.json.

Uso: python fabrica/montar.py episodios/<pasta>   -> gera <pasta>/video.mp4
Veja fabrica/README.md para o formato do episodio.json e os tipos de elementos.
"""
import json, math, random, subprocess, sys, unicodedata, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
ROOT = Path(__file__).resolve().parent
ASSETS, FONTS = ROOT / "assets", ROOT / "fontes"
F_BLACK, F_BOLD, F_MONO = str(FONTS / "Inter-Black.otf"), str(FONTS / "Inter-ExtraBold.otf"), str(FONTS / "DejaVuSansMono.ttf")
YELLOW = (255, 212, 0)
EXPRESSOES = ["confiante", "pensando", "rindo", "bravo", "oculos", "surpreso"]
TINTS = [(18, 22, 40), (40, 14, 30), (14, 34, 30), (34, 28, 10), (16, 24, 44)]
_fc = {}


def font(path, size):
    k = (path, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]


def hexrgb(h, default=(254, 44, 85)):
    if not h: return default
    if isinstance(h, (list, tuple)): return tuple(h)
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------------- fundo de código desfocado ----------------
CODE = """function iniciarProjeto(nome) {
  const site = criarSite(nome);
  if (site.pronto) { publicar(site); }
for (let i = 0; i < paginas.length; i++) {
  renderizar(paginas[i]);
return resultado;
let clientes = buscarClientes();
clientes.forEach(c => enviarProposta(c));
const estilo = { cor: '#3FB27F', fonte: 'Inter' };
<header class="topo"><h1>Meu site</h1></header>
.botao:hover { transform: scale(1.05); }
while (aprendendo) { praticar(); }
console.log("Hello, mundo!");
def soma(a, b): return a + b
print(f"Olá, {nome}!")
SELECT * FROM clientes WHERE ativo = 1;
git commit -m "primeiro commit"
import React, { useState } from 'react';
""".splitlines()


def code_background(tint, seed):
    img = Image.new("RGB", (W, H * 2), (14, 16, 22))
    d = ImageDraw.Draw(img); f = font(F_MONO, 54)
    colors = [(255, 121, 198), (139, 233, 253), (80, 250, 123), (241, 250, 140), (189, 147, 249), (230, 230, 230)]
    rnd = random.Random(seed); y = -20
    while y < H * 2:
        x = -40 + rnd.randint(0, 60)
        for tok in rnd.choice(CODE).split(" "):
            d.text((x, y), tok, font=f, fill=rnd.choice(colors)); x += d.textlength(tok + " ", font=f)
        y += 78
    img = img.filter(ImageFilter.GaussianBlur(7))
    return Image.blend(img, Image.new("RGB", img.size, tint), 0.55)


# ---------------- elementos ----------------
def rounded(d, box, r, fill, outline=None, width=0): d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def text_center(d, cx, cy, txt, f, fill):
    bb = d.textbbox((0, 0), txt, font=f)
    d.text((cx - (bb[2] + bb[0]) / 2, cy - (bb[3] + bb[1]) / 2), txt, font=f, fill=fill)


def fit_font(path, txt, max_w, start, minimum=28):
    s = start
    while s > minimum and ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(txt, font=font(path, s)) > max_w: s -= 4
    return font(path, s)


def sticker_frame(img, border=14):
    pad = border + 20
    big = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0)); big.paste(img, (pad, pad), img)
    m = big.split()[3].filter(ImageFilter.MaxFilter(border * 2 + 1))
    out = Image.new("RGBA", big.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", big.size, (0, 0, 0, 255)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * .5)))
    out.alpha_composite(sh, (10, 16))
    wl = Image.new("RGBA", big.size, (255, 255, 255, 255)); wl.putalpha(m)
    out.alpha_composite(wl); out.alpha_composite(big)
    return out


def card(w, h, fn):
    im = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0)); fn(ImageDraw.Draw(im), im); return sticker_frame(im)


def p_numero(p):
    return p_selo({"texto": str(p.get("texto", "1")), "cor": p.get("cor", "#FE2C55"), "tamanho": 230})


def p_selo(p):
    size = int(p.get("tamanho", 230)); txt = str(p.get("texto", "JS"))
    bg, fg = hexrgb(p.get("cor"), (254, 44, 85)), hexrgb(p.get("cor_texto"), (255, 255, 255))
    f = fit_font(F_BLACK, txt, size - 40, int(size * 0.48))
    return card(size, size, lambda d, im: (rounded(d, (0, 0, size, size), 34, bg), text_center(d, size / 2, size / 2, txt, f, fg)))


def chip(label, bg):
    fnt = fit_font(F_BLACK, label, 860, 72)
    w = int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(label, font=fnt)) + 90
    return card(w, 130, lambda d, im: (rounded(d, (0, 0, w, 130), 65, bg), text_center(d, w / 2, 65, label, fnt, (255, 255, 255))))


CHIP_COLORS = [(63, 140, 220), (230, 120, 40), (150, 80, 220), (39, 160, 90), (254, 44, 85)]


def p_chips(p): return [chip(t, CHIP_COLORS[i % len(CHIP_COLORS)]) for i, t in enumerate(p.get("itens", [])[:5])]


def p_riscado(p):
    txt = str(p.get("texto", "Errado"))
    lines = wrap(txt, F_BLACK, 80, 660)
    h = 90 + 100 * len(lines)
    def f(d, im):
        rounded(d, (0, 0, 760, h), 40, (245, 245, 245))
        for i, ln in enumerate(lines): text_center(d, 380, 70 + i * 100, ln, font(F_BLACK, 80), (30, 30, 30))
        d.line((60, 40, 700, h - 40), fill=(230, 40, 50), width=26); d.line((60, h - 40, 700, 40), fill=(230, 40, 50), width=26)
    return card(760, h, f)


def wrap(txt, fpath, size, max_w):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1))); f = font(fpath, size); lines, cur = [], ""
    for w in txt.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= max_w: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines[:4]


def p_carimbo(p):
    txt = str(p.get("texto", "OK")); bg = hexrgb(p.get("cor"), (63, 178, 127))
    f = fit_font(F_BLACK, txt, 760, 100)
    return card(840, 220, lambda d, im: (rounded(d, (0, 0, 840, 220), 30, bg), text_center(d, 420, 110, txt, f, (255, 255, 255)))).rotate(-4, expand=True, resample=Image.BICUBIC)


def p_navegador(p):
    w, h = 820, 560; titulo = str(p.get("titulo", "Meu primeiro site")); url = str(p.get("url", "meusite.com.br"))
    cor = hexrgb(p.get("cor"), (63, 178, 127)); botao = p.get("botao")
    def f(d, im):
        rounded(d, (0, 0, w, h), 34, (250, 250, 250))
        rounded(d, (0, 0, w, 74), 34, (225, 228, 235)); d.rectangle((0, 40, w, 74), fill=(225, 228, 235))
        for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]): d.ellipse((30 + i * 40, 24, 56 + i * 40, 50), fill=c)
        rounded(d, (170, 20, w - 30, 56), 18, (255, 255, 255)); d.text((196, 24), url[:34], font=font(F_BOLD, 28), fill=(120, 120, 130))
        rounded(d, (30, 100, w - 30, 320), 24, cor)
        for i, ln in enumerate(wrap(titulo, F_BLACK, 64, w - 140)[:2]): d.text((70, 135 + i * 78), ln, font=font(F_BLACK, 64), fill=(255, 255, 255))
        if botao:
            rounded(d, (70, 350, 400, 430), 40, (30, 30, 30)); text_center(d, 235, 390, str(botao)[:16], font(F_BLACK, 36), (255, 255, 255)); y0 = 460
        else: y0 = 350
        for i in range(3 if y0 == 350 else 1): rounded(d, (30, y0 + i * 70, w - 30 - i * 140, y0 + 45 + i * 70), 14, (230, 232, 238))
    return card(w, h, f)


def p_codigo(p):
    lines = [str(l) for l in p.get("linhas", ["console.log('oi')"])][:8]
    f = font(F_MONO, 48); lh = 66; w = 940; h = 110 + lh * len(lines)
    pal = {"kw": (255, 121, 198), "str": (241, 250, 140), "num": (189, 147, 249), "fn": (80, 250, 123), "tx": (235, 235, 240)}
    kws = {"if", "else", "for", "while", "return", "let", "const", "var", "function", "def", "print", "import", "from", "class", "in", "and", "or", "not", "True", "False", "true", "false"}
    def f2(d, im):
        rounded(d, (0, 0, w, h), 30, (24, 26, 36))
        for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]): d.ellipse((28 + i * 34, 24, 50 + i * 34, 46), fill=c)
        for i, ln in enumerate(lines):
            x, y = 40, 80 + i * lh
            for tok in __import__("re").split(r"(\s+|[(){}\[\];,.:=<>+\-*/'\"])", ln):
                if not tok: continue
                col = pal["kw"] if tok in kws else pal["num"] if tok.isdigit() else pal["str"] if tok in "'\"" else pal["fn"] if tok.isidentifier() and ln[ln.find(tok) + len(tok):ln.find(tok) + len(tok) + 1] == "(" else pal["tx"]
                d.text((x, y), tok, font=f, fill=col); x += d.textlength(tok, font=f)
    return card(w, h, f2)


def p_grafico(p):
    w, h = 760, 460; rotulo = str(p.get("texto", "R$")); vals = p.get("valores", [60, 90, 80, 150, 190, 260, 340])
    mx = max(vals) or 1
    def f(d, im):
        rounded(d, (0, 0, w, h), 36, (20, 26, 34))
        n = len(vals); bw = (w - 120) / n
        for i, v in enumerate(vals):
            x = 60 + i * bw; bh = (h - 170) * v / mx
            rounded(d, (x, h - 50 - bh, x + bw * 0.68, h - 50), 10, YELLOW if i == n - 1 else (63, 178, 127))
        d.text((50, 30), rotulo[:14], font=fit_font(F_BLACK, rotulo, 600, 90), fill=YELLOW)
    return card(w, h, f)


def p_versus(p):
    a, b = str(p.get("a", "A")), str(p.get("b", "B")); ca, cb = hexrgb(p.get("cor_a"), (55, 118, 171)), hexrgb(p.get("cor_b"), (240, 140, 30))
    w, h = 900, 300
    def f(d, im):
        rounded(d, (0, 0, 400, h), 36, ca); rounded(d, (500, 0, w, h), 36, cb)
        text_center(d, 200, h / 2, a, fit_font(F_BLACK, a, 340, 84), (255, 255, 255))
        text_center(d, 700, h / 2, b, fit_font(F_BLACK, b, 340, 84), (255, 255, 255))
        d.ellipse((390, 90, 510, 210), fill=(20, 20, 20)); text_center(d, 450, 150, "VS", font(F_BLACK, 48), YELLOW)
    return card(w, h, f)


def p_lista(p):
    itens = [str(t) for t in p.get("itens", [])][:5]; w = 860; h = 70 + 110 * len(itens)
    check = p.get("marcar", "check")
    def f(d, im):
        rounded(d, (0, 0, w, h), 36, (250, 250, 250))
        for i, t in enumerate(itens):
            y = 40 + i * 110
            if check == "x":
                rounded(d, (40, y, 110, y + 70), 18, (230, 40, 50)); d.line((58, y + 18, 92, y + 52), fill=(255, 255, 255), width=10); d.line((58, y + 52, 92, y + 18), fill=(255, 255, 255), width=10)
            else:
                rounded(d, (40, y, 110, y + 70), 18, (39, 160, 90)); d.line((56, y + 36, 70, y + 52), fill=(255, 255, 255), width=10); d.line((70, y + 52, 96, y + 18), fill=(255, 255, 255), width=10)
            d.text((140, y + 6), t, font=fit_font(F_BLACK, t, w - 180, 56), fill=(30, 30, 30))
    return card(w, h, f)


def p_texto(p):
    txt = str(p.get("texto", "")); bg = hexrgb(p.get("cor"), (250, 250, 250)); fg = hexrgb(p.get("cor_texto"), (30, 30, 30))
    lines = wrap(txt, F_BLACK, 76, 760); h = 80 + 96 * len(lines)
    def f(d, im):
        rounded(d, (0, 0, 860, h), 40, bg)
        for i, ln in enumerate(lines): text_center(d, 430, 70 + i * 96, ln, font(F_BLACK, 76), fg)
    return card(860, h, f)


def p_parte2(p):
    t, sub = str(p.get("texto", "PARTE 2")), str(p.get("sub", "segue pra não perder"))
    return card(720, 300, lambda d, im: (rounded(d, (0, 0, 720, 300), 40, hexrgb(p.get("cor"), (254, 44, 85))),
                                         text_center(d, 360, 110, t, fit_font(F_BLACK, t, 640, 120), (255, 255, 255)),
                                         text_center(d, 360, 225, sub, fit_font(F_BOLD, sub, 640, 50), (255, 255, 255))))


PROPS = {"numero": p_numero, "selo": p_selo, "chips": p_chips, "riscado": p_riscado, "carimbo": p_carimbo, "navegador": p_navegador,
         "codigo": p_codigo, "grafico": p_grafico, "versus": p_versus, "lista": p_lista, "texto": p_texto, "parte2": p_parte2}
SFX = {"numero": "ding", "riscado": "buzz", "carimbo": "thump", "grafico": "coins", "parte2": "rise", "selo": "sparkle",
       "navegador": "click", "codigo": "type", "versus": "thump", "lista": "pop2", "texto": "whoosh", "chips": "pop2"}


def mascot(name, height=900):
    if name not in EXPRESSOES: name = "confiante"
    im = Image.open(ASSETS / f"onca_{name}.png").convert("RGBA"); s = height / im.height
    return im.resize((int(im.width * s), height), Image.LANCZOS)


# ---------------- animação ----------------
def norm(t): return unicodedata.normalize("NFC", t.strip(".,:;!?…\"'()").lower())


def scene_starts(scenes, words):
    starts, wi = [], 0
    for k, sc in enumerate(scenes):
        key = sc.get("inicio", "")
        if k == 0: starts.append(0.0); continue
        j = wi
        while j < len(words) and norm(words[j]["text"]) != norm(key): j += 1
        if j < len(words): starts.append(words[j]["start"]); wi = j + 1
        else: starts.append(starts[-1] + 2.5); print(f"aviso: palavra de início '{key}' não encontrada", file=sys.stderr)
    return starts


def ease_back(t):
    t = max(0, min(1, t)); c = 1.7
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def paste_center(canvas, im, cx, cy, scale=1.0):
    if scale <= 0.01: return
    if abs(scale - 1) > 1e-3: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def caption_img(word):
    word = word.strip().strip(".,:;!?…\"'()").upper()
    f = font(F_BLACK, 132); tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    bb = tmp.textbbox((0, 0), word, font=f, stroke_width=14)
    while bb[2] - bb[0] > W - 80 and f.size > 40:
        f = font(F_BLACK, f.size - 8); bb = tmp.textbbox((0, 0), word, font=f, stroke_width=14)
    im = Image.new("RGBA", (max(1, bb[2] - bb[0] + 40), bb[3] - bb[1] + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((20 - bb[0], 20 - bb[1]), word, font=f, fill=YELLOW, stroke_width=14, stroke_fill=(0, 0, 0))
    return im


def layout(n, k, obj):
    if n == 1: return W / 2, 430 + obj.height / 2 * 0.15
    if n == 2: return ((190, 290) if k == 0 else (W / 2 + 80, 540))
    return [(170, 290), (W / 2 - 60, 560), (W / 2 + 280, 560)][k]


def main(folder):
    folder = Path(folder)
    ep = json.loads((folder / "episodio.json").read_text(encoding="utf-8"))
    words = [w for w in json.loads((folder / "palavras.json").read_text(encoding="utf-8")) if w["text"].strip() and not w["text"].startswith("[")]
    audio = str(folder / "narracao.mp3")
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio]).strip()) + 0.6
    scenes = ep["cenas"]; starts = scene_starts(scenes, words)
    seed = sum(map(ord, folder.name))
    bgs = [code_background(t, seed + i) for i, t in enumerate(TINTS)]
    built = []
    for sc in scenes:
        items = []
        for p in sc.get("elementos", [])[:3]:
            fn = PROPS.get(p.get("tipo"))
            if fn: items.append((p["tipo"], fn(p)))
            else: print(f"aviso: tipo desconhecido {p.get('tipo')}", file=sys.stderr)
        built.append(items)
    mcache, caps, sfx = {}, {}, []
    tmp_video = folder / "_video.mp4"
    proc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(tmp_video)], stdin=subprocess.PIPE)
    for fi in range(int(dur * FPS)):
        t = fi / FPS
        si = max(i for i, s in enumerate(starts) if s <= t + 1e-6); st = starts[si]; lt = t - st
        sc = scenes[si]
        if fi == int(st * FPS): sfx.append(("pop", st))
        bg = bgs[int(sc.get("fundo", si)) % len(bgs)]
        off = int((t * 60) % H)
        frame = bg.crop((0, off, W, off + H)).convert("RGBA")
        expr = sc.get("expressao", "confiante")
        if expr not in mcache: mcache[expr] = mascot(expr)
        items = built[si]
        sc_m = ease_back(lt / 0.28) * (1 + 0.012 * math.sin(t * 4))
        paste_center(frame, mcache[expr], W / 2, (1180 if items else 1000) + 8 * math.sin(t * 3), scale=sc_m * (0.82 if items else 1.0))
        for k, (tipo, obj) in enumerate(items):
            delay = 0.12 + k * 0.35
            if lt < delay: continue
            if fi == int((st + delay) * FPS): sfx.append((SFX.get(tipo, "whoosh"), st + delay))
            if tipo == "chips":
                for j, c in enumerate(obj):
                    pj = ease_back((lt - delay - j * 0.45) / 0.25)
                    if pj > 0:
                        if fi == int((st + delay + j * 0.45) * FPS): sfx.append(("pop2", st + delay + j * 0.45))
                        paste_center(frame, c, W / 2 + (j - 1) * 30, 240 + j * 160, scale=pj)
                continue
            cx, cy = layout(len(items), k, obj)
            paste_center(frame, obj, cx, cy + 6 * math.sin(t * 2.5 + k), scale=ease_back((lt - delay) / 0.3))
        cur = next((w for w in words if w["start"] <= t < max(w["end"], w["start"] + 0.12) + 0.05), None)
        if cur:
            if cur["text"] not in caps: caps[cur["text"]] = caption_img(cur["text"])
            paste_center(frame, caps[cur["text"]], W / 2, 1640, scale=0.86 + 0.14 * ease_back((t - cur["start"]) / 0.12))
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close(); proc.wait()
    make_sfx(sfx, dur, folder / "_sfx.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp_video), "-i", audio, "-i", str(folder / "_sfx.wav"),
                    "-filter_complex", "[1:a]volume=1.0[v];[2:a]volume=0.5[s];[v][s]amix=inputs=2:duration=first:normalize=0[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(folder / "video.mp4")], check=True)
    tmp_video.unlink(); (folder / "_sfx.wav").unlink()
    print(f"ok: {folder / 'video.mp4'} ({dur:.1f}s)")


# ---------------- efeitos sonoros sintetizados ----------------
def synth(kind, sr, rnd):
    def tt(sec): return np.arange(int(sec * sr)) / sr
    if kind in ("pop", "pop2"):
        t = tt(0.09); f0 = 900 if kind == "pop" else 1300
        return np.sin(2 * np.pi * (f0 - 5000 * t) * t) * np.exp(-t * 45)
    if kind == "ding":
        t = tt(0.9); return (np.sin(2 * np.pi * 1318 * t) + .5 * np.sin(2 * np.pi * 2637 * t) + .25 * np.sin(2 * np.pi * 3951 * t)) * np.exp(-t * 6) * .55
    if kind == "buzz":
        t = tt(0.45); return (np.sign(np.sin(2 * np.pi * 110 * t)) + .6 * np.sign(np.sin(2 * np.pi * 116 * t))) * np.minimum(1, (0.45 - t) * 10) * .28
    if kind == "thump":
        t = tt(0.35); return (np.sin(2 * np.pi * (60 + 120 * np.exp(-t * 25)) * t) * np.exp(-t * 9) + rnd.standard_normal(len(t)) * np.exp(-t * 40) * .3) * .9
    if kind in ("coins", "sparkle", "type"):
        out = np.zeros(int(0.9 * sr))
        notes = {"coins": [(2093, 0), (2637, .07), (3136, .14), (4186, .21), (3136, .32), (4186, .4)],
                 "sparkle": [(2500 + rnd.random() * 2500, k * .06) for k in range(7)],
                 "type": [(0, k * .07 + rnd.random() * .03) for k in range(9)]}[kind]
        for f, d0 in notes:
            t = tt(0.3)
            s = (rnd.standard_normal(len(t)) * np.exp(-t * 120) * .5) if kind == "type" else np.sin(2 * np.pi * f * t) * np.exp(-t * (14 if kind == "coins" else 25)) * .3
            i = int(d0 * sr); out[i:i + len(s)] += s[: len(out) - i]
        return out
    if kind == "rise":
        t = tt(0.6); f = 300 + 1500 * (t / t[-1]) ** 2
        noise = np.convolve(rnd.standard_normal(len(t)), np.ones(10) / 10, "same")
        return (np.sin(2 * np.pi * np.cumsum(f) / sr) * .25 + noise * .6) * (t / t[-1]) * np.exp(-np.maximum(0, t - .5) * 40)
    if kind == "click":
        t = tt(0.05); return rnd.standard_normal(len(t)) * np.exp(-t * 150) * .7
    t = tt(0.3); noise = np.convolve(rnd.standard_normal(len(t)), np.ones(18) / 18, "same")
    return noise * np.sin(np.pi * t / t[-1]) ** 2 * 0.9


def make_sfx(events, dur, path, sr=44100):
    buf = np.zeros(int((dur + 2) * sr)); rnd = np.random.default_rng(1)
    for kind, t in events:
        s = synth(kind, sr, rnd); i = int(t * sr); buf[i:i + len(s)] += s[: len(buf) - i]
    buf = np.clip(buf, -1, 1)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((buf * 32767 * 0.8).astype(np.int16).tobytes())


if __name__ == "__main__":
    main(sys.argv[1])
