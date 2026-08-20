#!/usr/bin/env python3
"""Busca frases dentro de un .srt y muestra en qué minuto están.

    clip/bin/buscar.py clip/fuente/video.srt "urgencia manifiesta" "abelardo"

Imprime cada coincidencia con su timestamp y el contexto de alrededor, para
ubicar rápido el tramo que se va a recortar.
"""
import argparse
import re
import sys
import unicodedata

TIEMPO = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})"
)


def normalizar(t):
    """Minúsculas y sin tildes, para que 'urgencia' encuentre 'Urgéncia'."""
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def leer(ruta):
    texto = open(ruta, encoding="utf-8-sig").read().replace("\r\n", "\n")
    fuera = []
    for bruto in re.split(r"\n\s*\n", texto.strip()):
        lineas = [l for l in bruto.split("\n") if l.strip()]
        if lineas and lineas[0].strip().isdigit():
            lineas = lineas[1:]
        if not lineas:
            continue
        t = TIEMPO.search(lineas[0])
        if not t:
            continue
        inicio = f"{int(t.group(1)):02d}:{t.group(2)}:{t.group(3)}"
        cuerpo = re.sub(r"<[^>]+>", "", " ".join(l.strip() for l in lineas[1:]))
        if cuerpo.strip():
            fuera.append((inicio, cuerpo.strip()))
    return fuera


def main():
    p = argparse.ArgumentParser()
    p.add_argument("srt")
    p.add_argument("frases", nargs="+")
    p.add_argument("--contexto", type=int, default=2,
                   help="cuántos subtítulos mostrar antes y después")
    a = p.parse_args()

    bloques = leer(a.srt)
    if not bloques:
        sys.exit(f"No pude leer subtítulos de {a.srt}")

    frases = [normalizar(f) for f in a.frases]
    encontrados = 0
    for i, (inicio, cuerpo) in enumerate(bloques):
        plano = normalizar(cuerpo)
        if not any(f in plano for f in frases):
            continue
        encontrados += 1
        print(f"\n=== {inicio} " + "=" * 50)
        for j in range(max(0, i - a.contexto), min(len(bloques), i + a.contexto + 1)):
            marca = ">>" if j == i else "  "
            print(f"{marca} [{bloques[j][0]}] {bloques[j][1]}")

    print(f"\n{encontrados} coincidencia(s) sobre {len(bloques)} subtítulos.")


if __name__ == "__main__":
    main()
