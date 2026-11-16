"""Corta uma gameplay longa em clipes de 30 s e gera uma ficha (mosaico com tempos) de cada clipe para catalogar.

Uso: python fabrica/preparar_gameplay.py <video_gameplay.mp4> <valorant|fortnite> [prefixo]
Gera: gameplay/<jogo>/<prefixo>_NNN.mp4  (1080p no máximo, 30 fps, com áudio)
      gameplay/<jogo>/fichas/<prefixo>_NNN.jpg  (8 quadros com o tempo de cada um)
Depois, descreva cada clipe em gameplay/catalogo.json (veja fabrica/README.md).
"""
import subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FONT = REPO / "fabrica" / "fontes" / "Inter-ExtraBold.otf"
SEG = 30


def main(src, jogo, prefixo=None):
    src = Path(src); jogo = jogo.lower()
    out = REPO / "gameplay" / jogo; fichas = out / "fichas"; fichas.mkdir(parents=True, exist_ok=True)
    prefixo = prefixo or ("v" if jogo == "valorant" else "f") + src.stem[:12].replace(" ", "_")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src),
                    "-vf", "scale=-2:'min(1080,ih)',fps=30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
                    "-c:a", "aac", "-b:a", "128k", "-ac", "2",
                    "-f", "segment", "-segment_time", str(SEG), "-reset_timestamps", "1",
                    "-force_key_frames", f"expr:gte(t,n_forced*{SEG})", str(out / f"{prefixo}_%03d.mp4")], check=True)
    for clip in sorted(out.glob(f"{prefixo}_*.mp4")):
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(clip)]))
        if dur < 4:
            clip.unlink(); continue
        step = max(dur / 8, 0.5)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(clip),
                        "-vf", f"fps=1/{step:.3f},scale=480:-2,drawtext=fontfile={FONT}:text='%{{pts\\:hms}}':x=12:y=12:fontsize=34:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=4x2",
                        "-frames:v", "1", "-q:v", "4", str(fichas / f"{clip.stem}.jpg")], check=True)
        print(f"{clip.relative_to(REPO)}  {dur:.1f}s")


if __name__ == "__main__":
    main(*sys.argv[1:4])
