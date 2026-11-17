"""Gera os carrosséis de foto do @klutchbr (1080x1920)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

HERE = Path(__file__).parent
BG = HERE / "fundos"
OUT = HERE / "saida"
FD = Path("/usr/share/fonts/opentype/inter")
W, H = 1080, 1920
ROXO = (124, 58, 237)
AMARELO = (255, 214, 0)
BRANCO = (255, 255, 255)
CINZA = (205, 205, 215)
TOP, BOTTOM = 200, 1560
Y0 = [TOP + 40]  # área segura (TikTok cobre topo e rodapé)
M = 90  # margem lateral


def f(peso, tam):
    return ImageFont.truetype(str(FD / f"Inter-{peso}.otf"), tam)


def fundo(nome, escurecer=0.32):
    blur = 34 if nome.startswith("ret") else 14
    im = Image.open(BG / f"{nome}.png").convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = (im.width - W) // 2
    im = im.crop((x, 0, x + W, H)).filter(ImageFilter.GaussianBlur(blur))
    im = ImageEnhance.Brightness(im).enhance(escurecer)
    # véu roxo bem leve
    veu = Image.new("RGB", (W, H), (30, 12, 60))
    return Image.blend(im, veu, 0.35).convert("RGBA")


def quebra(d, txt, fonte, larg):
    linhas = []
    for par in txt.split("\n"):
        cur = ""
        for w in par.split():
            t = (cur + " " + w).strip()
            if d.textlength(t, font=fonte) <= larg:
                cur = t
            else:
                if cur:
                    linhas.append(cur)
                cur = w
        linhas.append(cur)
    return linhas


def texto(d, xy, txt, fonte, cor=BRANCO, larg=W - 2 * M, esp=1.22, centro=False):
    x, y = xy
    lh = int(fonte.size * esp)
    for ln in quebra(d, txt, fonte, larg):
        if centro:
            d.text((W / 2 - d.textlength(ln, font=fonte) / 2, y), ln, font=fonte, fill=cor)
        else:
            d.text((x, y), ln, font=fonte, fill=cor)
        y += lh
    return y


def selo(d, x, y, txt, cor=ROXO, cor_txt=BRANCO, tam=34):
    fo = f("Bold", tam)
    lw = d.textlength(txt, font=fo)
    d.rounded_rectangle((x, y, x + lw + 44, y + tam + 30), 14, fill=cor)
    d.text((x + 22, y + 13), txt, font=fo, fill=cor_txt)
    return y + tam + 30


def marca(d, pagina, total):
    fo = f("Bold", 30)
    d.text((M, BOTTOM + 40), "@klutchbr", font=fo, fill=CINZA)
    t = f"{pagina}/{total}"
    d.text((W - M - d.textlength(t, font=fo), BOTTOM + 40), t, font=fo, fill=CINZA)


def cartao(im, box, alpha=150):
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle(box, 28, fill=(12, 8, 22, alpha))
    im.alpha_composite(ov)


# ---------------- tipos de slide ----------------

def s_capa(s, d, im):
    y = 430
    y = selo(d, M, y, s["serie"], ROXO) + 50
    y = texto(d, (M, y), s["titulo"], f("Black", 108), BRANCO, esp=1.08) + 30
    if s.get("sub"):
        y = texto(d, (M, y), s["sub"], f("SemiBold", 46), AMARELO) + 20
    if s.get("rodape"):
        texto(d, (M, BOTTOM - 140), s["rodape"], f("Medium", 36), CINZA)


def s_topicos(s, d, im):
    y = Y0[0]
    if s.get("selo"):
        y = selo(d, M, y, s["selo"]) + 40
    y = texto(d, (M, y), s["titulo"], f("Black", 90), BRANCO, esp=1.08) + 30
    if s.get("intro"):
        y = texto(d, (M, y), s["intro"], f("Medium", 46), CINZA) + 36
    for it in s["itens"]:
        cab, corpo = (it if isinstance(it, (list, tuple)) else (it, ""))
        d.ellipse((M, y + 20, M + 24, y + 44), fill=AMARELO)
        y = texto(d, (M + 50, y), cab, f("Bold", 54), BRANCO, larg=W - 2 * M - 50)
        if corpo:
            y = texto(d, (M + 50, y + 4), corpo, f("Regular", 44), CINZA, larg=W - 2 * M - 50)
        y += 42
    if not s.get("nota"):
        return y
    if s.get("nota"):
        y += 10
        cartao(im, (M - 20, y - 20, W - M + 20, y + 20 + 52 * len(quebra(d, s["nota"], f("SemiBold", 44), W - 2 * M - 20))))
        d2 = ImageDraw.Draw(im)
        y = texto(d2, (M, y), s["nota"], f("SemiBold", 44), AMARELO, larg=W - 2 * M - 20, esp=1.3) + 20
    return y


def s_classe(s, d, im):
    y = Y0[0]
    y = selo(d, M, y, s["selo"]) + 36
    y = texto(d, (M, y), s["titulo"], f("Black", 104), BRANCO) + 14
    y = texto(d, (M, y), s["funcao"], f("Medium", 46), CINZA) + 50
    # agentes
    d.text((M, y), "AGENTES", font=f("Bold", 32), fill=AMARELO); y += 56
    x0 = M
    fo = f("SemiBold", 44)
    for ag in s["agentes"]:
        lw = d.textlength(ag, font=fo) + 44
        if x0 + lw > W - M:
            x0 = M; y += 92
        d.rounded_rectangle((x0, y, x0 + lw, y + 74), 37, outline=(255, 255, 255, 120), width=3)
        d.text((x0 + 22, y + 10), ag, font=fo, fill=BRANCO)
        x0 += lw + 16
    y += 120
    d.text((M, y), "PRA COMEÇAR", font=f("Bold", 32), fill=AMARELO); y += 56
    y = texto(d, (M, y), s["comeco"], f("Bold", 58), BRANCO) + 40
    d.text((M, y), "COMBINA COM VOCÊ SE", font=f("Bold", 32), fill=AMARELO); y += 56
    return texto(d, (M, y), s["perfil"], f("Regular", 46), CINZA)


def desenha_mira(cfg, escala=9):
    """Desenha a mira a partir dos parâmetros do código (pixels do jogo x escala)."""
    tam = 640
    im = Image.new("RGBA", (tam, tam), (0, 0, 0, 0))
    c = tam / 2
    cor = tuple(cfg["cor"])
    rects = []
    for ln in cfg.get("linhas", []):
        t = ln.get("t", 2) * escala
        o = ln.get("o", 0) * escala
        lh, lv = ln.get("lh", 0) * escala, ln.get("lv", 0) * escala
        if lv:
            rects += [(c - t / 2, c - o - lv, c + t / 2, c - o), (c - t / 2, c + o, c + t / 2, c + o + lv)]
        if lh:
            rects += [(c - o - lh, c - t / 2, c - o, c + t / 2), (c + o, c - t / 2, c + o + lh, c + t / 2)]
    if cfg.get("dot"):
        z = cfg.get("z", 2) * escala
        rects.append((c - z / 2, c - z / 2, c + z / 2, c + z / 2))
    if cfg.get("contorno"):
        ow = cfg.get("ow", 1) * escala
        oa = int(255 * cfg.get("oa", 0.5))
        lay = Image.new("RGBA", (tam, tam), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        for r in rects:
            dl.rectangle((r[0] - ow, r[1] - ow, r[2] + ow, r[3] + ow), fill=(0, 0, 0, oa))
        im.alpha_composite(lay)
    d = ImageDraw.Draw(im)
    for r in rects:
        d.rectangle(r, fill=cor)
    return im


def s_mira(s, d, im):
    y = Y0[0]
    y = selo(d, M, y, s["selo"]) + 36
    y = texto(d, (M, y), s["titulo"], f("Black", 84), BRANCO) + 30
    # prévia sobre a gameplay
    bx = (M, y, W - M, y + 420)
    prev = Image.open(BG / f"{s['fundo_mira']}.png").convert("RGB")
    zf = s.get("zoom_fundo", 1.6)
    s2 = max((bx[2] - bx[0]) / prev.width * zf, (bx[3] - bx[1]) / prev.height * zf)
    prev = prev.resize((int(prev.width * s2), int(prev.height * s2)), Image.LANCZOS)
    cx, cy = prev.width // 2, prev.height // 2
    bw, bh = bx[2] - bx[0], bx[3] - bx[1]
    prev = prev.filter(ImageFilter.GaussianBlur(2))
    prev = prev.crop((cx - bw // 2, cy - bh // 2, cx - bw // 2 + bw, cy - bh // 2 + bh)).convert("RGBA")
    mira = desenha_mira(s["mira"], escala=13)
    prev.alpha_composite(mira, (bw // 2 - mira.width // 2, bh // 2 - mira.height // 2))
    mask = Image.new("L", (bw, bh), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw, bh), 28, fill=255)
    im.paste(prev, (bx[0], bx[1]), mask)
    d = ImageDraw.Draw(im)
    d.text((bx[0] + 20, bx[3] - 50), "prévia ampliada", font=f("Medium", 26), fill=(255, 255, 255, 200))
    y = bx[3] + 36
    d.text((M, y), "USE PARA", font=f("Bold", 32), fill=AMARELO); y += 52
    y = texto(d, (M, y), s["uso"], f("SemiBold", 50), BRANCO) + 22
    y = texto(d, (M, y), s["porque"], f("Regular", 43), CINZA) + 32
    # código
    fo = f("Bold", 30)
    fm = ImageFont.truetype("/home/claude/lp-webdev-videos/fabrica/fontes/DejaVuSansMono.ttf", 40)
    linhas, cur = [], ""
    for tk in s["codigo"].split(";"):
        t = (cur + ";" + tk) if cur else tk
        if d.textlength(t + ";", font=fm) > W - 2 * M - 60:
            linhas.append(cur + ";"); cur = tk
        else:
            cur = t
    linhas.append(cur)
    hbox = 76 + 54 * len(linhas)
    d.rounded_rectangle((M, y, W - M, y + hbox), 22, fill=(255, 214, 0))
    d.text((M + 30, y + 16), "CÓDIGO DA MIRA", font=fo, fill=(20, 14, 30))
    yy = y + 58
    for ln in linhas:
        d.text((M + 30, yy), ln, font=ImageFont.truetype("/home/claude/lp-webdev-videos/fabrica/fontes/DejaVuSansMono.ttf", 40), fill=(20, 14, 30)); yy += 54
    return y + hbox


def s_final(s, d, im):
    y = 560
    y = texto(d, (M, y), s["titulo"], f("Black", 96), BRANCO, esp=1.08) + 40
    y = texto(d, (M, y), s["texto"], f("SemiBold", 46), AMARELO) + 50
    if s.get("prox"):
        cartao(im, (M - 20, y, W - M + 20, y + 190))
        d2 = ImageDraw.Draw(im)
        d2.text((M + 10, y + 30), "PRÓXIMA PARTE", font=f("Bold", 32), fill=AMARELO)
        texto(d2, (M + 10, y + 80), s["prox"], f("Bold", 46), BRANCO, larg=W - 2 * M - 20)


def s_arma(s, d, im):
    y = Y0[0]
    y = selo(d, M, y, s["selo"]) + 36
    d.text((M, y), s["categoria"], font=f("Bold", 44), fill=AMARELO); y += 70
    y = texto(d, (M, y), s["titulo"], f("Black", 100), BRANCO, esp=1.06) + 40
    for cab, corpo in s["itens"]:
        y = texto(d, (M, y), cab, f("Bold", 54), BRANCO)
        y = texto(d, (M, y + 4), corpo, f("Regular", 44), CINZA) + 40
    if not s.get("alternativa"):
        return y
    if s.get("alternativa"):
        nl = len(quebra(d, s["alternativa"], f("SemiBold", 46), W - 2 * M - 20))
        cartao(im, (M - 20, y, W - M + 20, y + 110 + 58 * nl))
        d2 = ImageDraw.Draw(im)
        d2.text((M + 10, y + 28), "SE NÃO ACHAR", font=f("Bold", 30), fill=AMARELO)
        texto(d2, (M + 10, y + 74), s["alternativa"], f("SemiBold", 46), BRANCO, larg=W - 2 * M - 20)
        y += 110 + 58 * nl
    return y


TIPOS = {"capa": s_capa, "topicos": s_topicos, "classe": s_classe, "mira": s_mira, "final": s_final, "arma": s_arma}


def gerar(nome, slides):
    out = OUT / nome
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()
    for i, s in enumerate(slides, 1):
        Y0[0] = TOP + 40
        im = fundo(s["fundo"])
        if s["tipo"] in ("topicos", "classe", "mira", "arma"):
            teste = im.copy()
            fim = TIPOS[s["tipo"]](s, ImageDraw.Draw(teste), teste) or (TOP + 40)
            Y0[0] = TOP + 40 + max(0, int((BOTTOM - 40 - fim) / 2))
        d = ImageDraw.Draw(im)
        TIPOS[s["tipo"]](s, d, im)
        marca(ImageDraw.Draw(im), i, len(slides))
        im.convert("RGB").save(out / f"{i:02d}.png", optimize=True)
    return out


if __name__ == "__main__":
    import json
    for nome in sys.argv[1:]:
        cfg = json.load(open(HERE / "conteudo" / f"{nome}.json"))
        print(gerar(nome, cfg))
