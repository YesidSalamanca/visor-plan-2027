# Clip: el error de Abelardo con la urgencia manifiesta

**Fuente**: grabación del programa con Daniel Coronell, Yezid Daniel Baquero,
Carlos Carrillo y Catalina Suárez. Llegó partida en tres archivos de WhatsApp
(`WA0011` → `WA0012` → `WA0013`, ese orden confirmado por la continuidad de
imagen en los empalmes), 848×480, 3 min 44 s en total.

**Tramo usado**: `64.5 s → 143.6 s` del video unido (1 min 19 s).

**Gancho**: `99.9 s → 108.45 s` (8,5 s), la frase «este señor no tiene ni idea de
cómo funciona el Sistema Nacional de Gestión del Riesgo y en este momento está
conduciendo el peor desastre que hemos tenido en lo que va del siglo». Va al
principio en blanco y negro y vuelve a aparecer, ya en color, dentro del cuerpo.
Total: 1 min 28 s.

**Encuadre**: la fuente es una cuadrícula de Zoom de 2×2; el clip aísla el
recuadro de Carrillo, que es el inferior izquierdo (`--precrop 398:226:17:245`).

## Comando

```bash
COMUN=(--src completo.mp4 --precrop "398:226:17:245" --layout blur
       --fuente clip/fuentes/Roboto-700.ttf)

clip/bin/render.sh "${COMUN[@]}" --inicio 99.90 --fin 108.45 --bn si  --grano si \
  --subs clip/salida/gancho_urgencia_manifiesta.srt --salida gancho.mp4

clip/bin/render.sh "${COMUN[@]}" --inicio 64.5  --fin 143.6  --bn no --grano no \
  --subs clip/salida/clip_urgencia_manifiesta.srt --salida cuerpo.mp4

clip/bin/unir.sh clip_urgencia_manifiesta.mp4 gancho.mp4 cuerpo.mp4
```

Para rehacer `completo.mp4`:

```bash
printf "file '%s'\n" WA0011.mp4 WA0012.mp4 WA0013.mp4 > lista.txt
ffmpeg -f concat -safe 0 -i lista.txt -c copy completo.mp4
```

## Lo que dice en el clip

> Y aquí vemos exactamente lo mismo. Hay una acusación y yo la voy a citar.
> Dicen: la UNGRD pagó 856 mil millones de pesos sin urgencia manifiesta.
> Silencio, ¿cierto? Música de suspenso.
>
> Y yo realmente quedé muy impactado cuando escuché al presidente decir eso,
> porque yo dije: este señor no tiene ni idea de cómo funciona la 1523, cómo
> funciona el Sistema Nacional de Gestión del Riesgo. Este señor no tiene ni
> idea de cómo funciona el Sistema Nacional de Gestión del Riesgo, y en este
> momento está conduciendo el peor desastre que hemos tenido en lo que va del
> siglo.
>
> Yo realmente quedé impactado porque la UNGRD no contrata por urgencia
> manifiesta. La urgencia manifiesta es una figura de la Ley 80, pero el
> artículo 66 de la Ley 1523 le da a la UNGRD unas facultades excepcionales de
> contratación, un régimen especialísimo que funciona entre privados. La UNGRD
> contrata entre privados. Entonces, ya solamente con eso, no necesita apelar a
> la urgencia manifiesta para contratar.

## Nota sobre la transcripción

La sacó Whisper-small y quedó revisada a mano contra ventanas de audio sueltas.
Las correcciones fueron: `UNRD` / `UNHRD` / `UNGD` → **UNGRD**, `la 15 23` →
**la 1523**, `de Sastre` → **de Desastres** y `Avelar a` → **apelar a**. Los
tiempos de los subtítulos se repartieron sobre los tramos con voz detectados por
`silencedetect`, no sobre la duración total, para que no se desfasen en las
pausas.
