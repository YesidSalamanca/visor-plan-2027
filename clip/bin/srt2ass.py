#!/usr/bin/env python3
"""Convierte un .srt a .ass con estilo de subtítulo vertical tipo TikTok.

El .ass generado fija PlayResX/PlayResY en 1080x1920, así los tamaños y
márgenes se expresan en píxeles reales del clip y libass no los reescala.
"""
import argparse
import re
import sys
import textwrap

CABECERA = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
WrapStyle: 0
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Clip,{fuente},{tam},&H00FFFFFF,&H00FFFFFF,&H00000000,&H60000000,-1,0,0,0,100,100,0,0,1,{contorno},{sombra},2,90,90,{margen},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

TIEMPO = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})"
)


def a_ass(h, m, s, ms):
    """Formato de tiempo de ASS: h:mm:ss.cc (centésimas)."""
    return f"{int(h)}:{int(m):02d}:{int(s):02d}.{int(str(ms).ljust(3, '0')[:3]) // 10:02d}"


def leer_srt(ruta):
    texto = open(ruta, encoding="utf-8-sig").read().replace("\r\n", "\n")
    bloques = []
    for bruto in re.split(r"\n\s*\n", texto.strip()):
        lineas = [l for l in bruto.split("\n") if l.strip()]
        if not lineas:
            continue
        if lineas[0].strip().isdigit():
            lineas = lineas[1:]
        if not lineas:
            continue
        t = TIEMPO.search(lineas[0])
        if not t:
            continue
        inicio = a_ass(*t.group(1, 2, 3, 4))
        fin = a_ass(*t.group(5, 6, 7, 8))
        cuerpo = " ".join(l.strip() for l in lineas[1:])
        cuerpo = re.sub(r"<[^>]+>", "", cuerpo).strip()
        if cuerpo:
            bloques.append((inicio, fin, cuerpo))
    return bloques


def main():
    p = argparse.ArgumentParser()
    p.add_argument("entrada")
    p.add_argument("salida")
    p.add_argument("--fuente", default="DejaVu Sans")
    p.add_argument("--tam", type=int, default=62)
    p.add_argument("--margen", type=int, default=420,
                   help="píxeles desde el borde inferior del clip de 1920px")
    p.add_argument("--contorno", type=int, default=5)
    p.add_argument("--sombra", type=int, default=2)
    p.add_argument("--ancho", type=int, default=24,
                   help="caracteres por línea antes de partir")
    p.add_argument("--mayusculas", action="store_true")
    a = p.parse_args()

    bloques = leer_srt(a.entrada)
    if not bloques:
        sys.exit(f"No se encontró ningún subtítulo en {a.entrada}")

    with open(a.salida, "w", encoding="utf-8") as f:
        f.write(CABECERA.format(fuente=a.fuente, tam=a.tam, margen=a.margen,
                                contorno=a.contorno, sombra=a.sombra))
        for inicio, fin, cuerpo in bloques:
            if a.mayusculas:
                cuerpo = cuerpo.upper()
            lineas = textwrap.wrap(cuerpo, width=a.ancho) or [cuerpo]
            texto = "\\N".join(lineas)
            f.write(f"Dialogue: 0,{inicio},{fin},Clip,,0,0,0,,{texto}\n")

    print(f"{a.salida} ({len(bloques)} subtítulos)")


if __name__ == "__main__":
    main()
