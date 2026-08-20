import re, json, sys

# Tramos verificados a oído-máquina (tiempos relativos al clip) con el texto ya corregido:
# la ASR escribe "UNRD/UNHRD/UNGD" y "la 15 23", que aquí quedan como UNGRD y 1523.
ANCLAS = [
 (0.27,  5.88, "Y aquí vemos exactamente lo mismo. Hay una acusación y yo la voy a citar."),
 (6.28, 18.00, "Dicen: la UNGRD pagó 856 mil millones de pesos sin urgencia manifiesta. "
               "Silencio, ¿cierto?"),
 (18.00,19.60, "Música de suspenso."),
 (19.60,28.38, "Y yo realmente quedé muy impactado cuando escuché al presidente decir eso, "
               "porque yo dije: este señor no tiene ni idea"),
 (28.78,35.39, "de cómo funciona la 1523, cómo funciona el Sistema Nacional de Gestión del Riesgo."),
 (35.79,44.30, "Este señor no tiene ni idea de cómo funciona el Sistema Nacional de Gestión del "
               "Riesgo, y en este momento está conduciendo el peor desastre que hemos tenido "
               "en lo que va del siglo."),
 (44.30,46.70, "Yo realmente quedé impactado"),
 (46.76,50.30, "porque la UNGRD no contrata por urgencia manifiesta."),
 (50.30,59.00, "La urgencia manifiesta es una figura de la Ley 80, pero el artículo 66 "
               "de la Ley 1523"),
 (59.00,66.88, "le da a la UNGRD unas facultades excepcionales de contratación, un régimen "
               "especialísimo que funciona entre privados."),
 (67.27,70.88, "La UNGRD contrata entre privados. Entonces, ya solamente con eso,"),
 (71.27,79.07, "no necesita apelar a la urgencia manifiesta para contratar."),
]

MAX_CARACTERES = 38   # por línea de subtítulo, dos líneas máximo

def tramos_de_habla(path, fin_total):
    """Convierte la salida de silencedetect en intervalos donde sí hay voz."""
    ini_sil, fin_sil = [], []
    for l in open(path):
        m = re.search(r"silence_start: ([\d.]+)", l)
        if m: ini_sil.append(float(m.group(1)))
        m = re.search(r"silence_end: ([\d.]+)", l)
        if m: fin_sil.append(float(m.group(1)))
    silencios = list(zip(ini_sil, fin_sil + [fin_total] * (len(ini_sil) - len(fin_sil))))
    habla, cursor = [], 0.0
    for a, b in silencios:
        if a > cursor: habla.append((cursor, a))
        cursor = b
    if cursor < fin_total: habla.append((cursor, fin_total))
    return habla

def partir(texto):
    """Parte un texto en líneas de subtítulo cortas, respetando la puntuación."""
    palabras, lineas, actual = texto.split(), [], ""
    for p in palabras:
        cand = (actual + " " + p).strip()
        if len(cand) > MAX_CARACTERES and actual:
            lineas.append(actual); actual = p
        else:
            actual = cand
            if p.endswith((".", "?", "!", ":")) and len(actual) > MAX_CARACTERES * 0.5:
                lineas.append(actual); actual = ""
    if actual: lineas.append(actual)
    return lineas

def hhmmss(t):
    h, r = divmod(max(t, 0), 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")

habla = tramos_de_habla(sys.argv[1], 79.5)
subs, n = [], 0

for ini, fin, texto in ANCLAS:
    # Tiempo con voz dentro del ancla: repartimos el texto sobre él, no sobre las pausas.
    trozos = [(max(a, ini), min(b, fin)) for a, b in habla if b > ini and a < fin]
    trozos = [(a, b) for a, b in trozos if b > a] or [(ini, fin)]
    total = sum(b - a for a, b in trozos)
    lineas = partir(texto)
    largo = sum(len(l) for l in lineas)
    acum = 0.0
    for l in lineas:
        # Posición de esta línea dentro del "tiempo de voz" del ancla...
        d = total * len(l) / largo
        a_voz, b_voz = acum, acum + d
        acum = b_voz
        # ...y de vuelta a tiempo real, saltando los silencios.
        def a_reloj(x):
            r = 0.0
            for a, b in trozos:
                dur = b - a
                if x <= r + dur: return a + (x - r)
                r += dur
            return trozos[-1][1]
        n += 1
        subs.append((n, a_reloj(a_voz), a_reloj(b_voz), l))

with open(sys.argv[2], "w") as f:
    for n, a, b, l in subs:
        f.write(f"{n}\n{hhmmss(a)} --> {hhmmss(max(b, a+0.5))}\n{l}\n\n")
print(f"{len(subs)} subtítulos -> {sys.argv[2]}")
