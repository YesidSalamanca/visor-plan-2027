#!/usr/bin/env python3
"""Convierte un .srt a .ass con estilo de subtítulo vertical tipo TikTok.

El .ass generado fija PlayResX/PlayResY en 1080x1920, así los tamaños y
márgenes se expresan en píxeles reales del clip y libass no los reescala.

Con --resaltado se imita el subtítulo de CapCut: el texto va en blanco y la
palabra que se está diciendo en ese instante se pinta de amarillo. Como el .srt
solo trae tiempos por frase, el reparto dentro de la frase se hace proporcional
al largo de cada palabra, que es lo bastante fiel al ritmo del habla.
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


def segundos(t):
    """h:mm:ss.cc -> segundos."""
    h, m, resto = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(resto)


def marca(seg):
    h, resto = divmod(seg, 3600)
    m, s = divmod(resto, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def escribir_resaltado(f, inicio, fin, lineas, hex_color):
    """Un evento por palabra: la que suena va en color, el resto en blanco.

    El tiempo de cada palabra se reparte proporcionalmente a su largo, más una
    unidad por el espacio, que es lo que aproxima mejor el ritmo al hablar.
    """
    ass_color = "&H%s%s%s&" % (hex_color[4:6], hex_color[2:4], hex_color[0:2])
    t0, t1 = segundos(inicio), segundos(fin)
    palabras = [(i, j, p) for i, l in enumerate(lineas) for j, p in enumerate(l.split())]
    pesos = [len(p) + 1 for _, _, p in palabras]
    total = sum(pesos) or 1
    partidas = [l.split() for l in lineas]

    acum, escritos = 0.0, 0
    for k, (i, j, _) in enumerate(palabras):
        a_t = t0 + (t1 - t0) * acum / total
        acum += pesos[k]
        b_t = t0 + (t1 - t0) * acum / total
        pintadas = []
        for li, ps in enumerate(partidas):
            trozos = [f"{{{chr(92)}c{ass_color}}}{p}{{{chr(92)}c&HFFFFFF&}}" if (li, pj) == (i, j) else p
                      for pj, p in enumerate(ps)]
            pintadas.append(" ".join(trozos))
        texto = "\\N".join(pintadas)
        f.write(f"Dialogue: 0,{marca(a_t)},{marca(b_t)},Clip,,0,0,0,,{texto}\n")
        escritos += 1
    return escritos


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
    p.add_argument("--resaltado", metavar="HEX",
                   help="resalta palabra por palabra en este color, p. ej. FCCB04")
    a = p.parse_args()

    bloques = leer_srt(a.entrada)
    if not bloques:
        sys.exit(f"No se encontró ningún subtítulo en {a.entrada}")

    with open(a.salida, "w", encoding="utf-8") as f:
        f.write(CABECERA.format(fuente=a.fuente, tam=a.tam, margen=a.margen,
                                contorno=a.contorno, sombra=a.sombra))
        eventos = 0
        for inicio, fin, cuerpo in bloques:
            if a.mayusculas:
                cuerpo = cuerpo.upper()
            lineas = textwrap.wrap(cuerpo, width=a.ancho) or [cuerpo]
            if a.resaltado:
                eventos += escribir_resaltado(f, inicio, fin, lineas, a.resaltado)
            else:
                texto = "\\N".join(lineas)
                f.write(f"Dialogue: 0,{inicio},{fin},Clip,,0,0,0,,{texto}\n")
                eventos += 1

    print(f"{a.salida} ({len(bloques)} subtítulos, {eventos} eventos)")


if __name__ == "__main__":
    main()
