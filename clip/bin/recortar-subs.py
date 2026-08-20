#!/usr/bin/env python3
"""Recorta un .srt al tramo del clip y lo vuelve a poner en cero.

    clip/bin/recortar-subs.py entrada.srt salida.srt --inicio 01:10:24 --fin 01:10:58

Los tiempos aceptan HH:MM:SS, MM:SS o segundos sueltos, y deben ser los mismos
que se le pasan a render.sh.
"""
import argparse
import re

TIEMPO = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})"
)


def a_segundos(t):
    if re.fullmatch(r"\d+(\.\d+)?", t):
        return float(t)
    partes = [float(x) for x in t.replace(",", ".").split(":")]
    while len(partes) < 3:
        partes.insert(0, 0.0)
    return partes[0] * 3600 + partes[1] * 60 + partes[2]


def fmt(s):
    s = max(0.0, s)
    h, r = divmod(s, 3600)
    m, seg = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(seg):02d},{round((seg % 1) * 1000):03d}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("entrada")
    p.add_argument("salida")
    p.add_argument("--inicio", required=True)
    p.add_argument("--fin", required=True)
    a = p.parse_args()

    ini, fin = a_segundos(a.inicio), a_segundos(a.fin)
    if fin <= ini:
        raise SystemExit("--fin debe ser posterior a --inicio")

    texto = open(a.entrada, encoding="utf-8-sig").read().replace("\r\n", "\n")
    salida, n = [], 0
    for bruto in re.split(r"\n\s*\n", texto.strip()):
        lineas = [l for l in bruto.split("\n") if l.strip()]
        if lineas and lineas[0].strip().isdigit():
            lineas = lineas[1:]
        if not lineas:
            continue
        t = TIEMPO.search(lineas[0])
        if not t:
            continue
        g = [float(x) for x in t.groups()]
        s0 = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        s1 = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        # Nos quedamos con todo lo que se solape con la ventana del clip.
        if s1 <= ini or s0 >= fin:
            continue
        cuerpo = re.sub(r"<[^>]+>", "", " ".join(l.strip() for l in lineas[1:])).strip()
        if not cuerpo:
            continue
        n += 1
        salida.append(f"{n}\n{fmt(max(s0, ini) - ini)} --> {fmt(min(s1, fin) - ini)}\n{cuerpo}\n")

    if not n:
        raise SystemExit("Ningún subtítulo cae dentro de esa ventana.")
    open(a.salida, "w", encoding="utf-8").write("\n".join(salida) + "\n")
    print(f"{a.salida} ({n} subtítulos, ventana de {fin - ini:.1f}s)")


if __name__ == "__main__":
    main()
