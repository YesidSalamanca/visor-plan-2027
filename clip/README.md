# Clips verticales en blanco y negro con hook

Herramientas para sacar un clip de una transmisión larga y dejarlo listo para
TikTok / Reels / Shorts: vertical 9:16, imagen en blanco y negro con contraste
levantado, un **hook** de texto en los primeros segundos y subtítulos quemados.

Todo corre con `ffmpeg` y `yt-dlp`; no hay que abrir un editor.

## Requisitos

```bash
pip install -U yt-dlp
sudo apt-get install -y ffmpeg          # macOS: brew install ffmpeg
pip install -U faster-whisper           # opcional, solo si hay que transcribir
```

## Flujo completo

### 1. Bajar el tramo del video

Bajar la transmisión entera de varias horas es lento y casi nunca hace falta.
Si ya sabes más o menos dónde está el momento, baja solo esa ventana con un
margen generoso:

```bash
clip/bin/descargar.sh "https://www.youtube.com/live/abq2sDpniuM" \
  --seccion "*01:05:00-01:20:00"
```

Sin `--seccion` baja la transmisión completa. En ambos casos intenta traerse
también los subtítulos automáticos en español y los convierte a `.srt`.

Los archivos quedan en `clip/fuente/`.

### 2. Ubicar el momento exacto

```bash
clip/bin/buscar.py clip/fuente/abq2sDpniuM.es.srt "urgencia manifiesta" "abelardo"
```

Muestra cada coincidencia con su timestamp y el contexto alrededor. De ahí
salen el `--inicio` y el `--fin` del clip.

Si el video no trajo subtítulos automáticos:

```bash
clip/bin/transcribir.sh clip/fuente/abq2sDpniuM.mp4 medium
```

### 3. Recortar los subtítulos a la ventana del clip

Los tiempos del `.srt` original están en la escala de la transmisión completa;
hay que llevarlos a cero:

```bash
clip/bin/recortar-subs.py clip/fuente/abq2sDpniuM.es.srt clip/salida/clip.srt \
  --inicio 01:10:22 --fin 01:10:58
```

Vale la pena abrir el `.srt` resultante y limpiarlo a mano: los subtítulos
automáticos de YouTube se equivocan con nombres propios y con términos como
*urgencia manifiesta*, y en un clip corto cada error se nota.

### 4. Renderizar

```bash
clip/bin/render.sh \
  --src clip/fuente/abq2sDpniuM.mp4 \
  --inicio 01:10:22 --fin 01:10:58 \
  --hook "EL ERROR DE ABELARDO CON LA URGENCIA MANIFIESTA" \
  --hook-dur 4 \
  --credito "Carlos Carrillo · en vivo" \
  --subs clip/salida/clip.srt \
  --salida clip/salida/urgencia-manifiesta.mp4
```

> Ojo: si bajaste el video con `--seccion`, el archivo empieza en el segundo 0
> de esa ventana, así que `--inicio` y `--fin` van relativos a ese recorte, no
> a la transmisión completa.

## Opciones de `render.sh`

| Opción | Por defecto | Para qué sirve |
|---|---|---|
| `--src` | — | Video fuente (obligatorio) |
| `--inicio` / `--fin` | — | Ventana del clip; `--duracion` reemplaza a `--fin` |
| `--hook` | — | Titular inicial. Se parte solo cada 20 caracteres; `\n` fuerza el salto |
| `--hook-dur` | `4` | Segundos que dura el hook en pantalla |
| `--hook-y` | `150` | Distancia del hook al borde superior |
| `--credito` | — | Línea pequeña al pie (programa, fecha, @usuario) |
| `--subs` | — | `.srt` o `.ass` a quemar |
| `--subs-tam` | `62` | Tamaño de los subtítulos en píxeles |
| `--subs-margen` | `420` / `260` | Distancia al borde inferior según el layout |
| `--subs-mayus` | `si` | Subtítulos en mayúsculas |
| `--layout` | `blur` | `blur`: cuadro completo sobre fondo desenfocado. `cover`: encuadre cerrado a pantalla completa |
| `--offset-x` | `0` | Mueve el encuadre en `cover` (útil si el orador no está centrado) |
| `--grano` | `si` | Grano ligero, para que el blanco y negro no quede plano |
| `--fuente` | DejaVu Sans Bold | Ruta a un `.ttf` en negrita |
| `--salida` | `clip/salida/clip.mp4` | Archivo final |

## Qué produce

H.264 alto perfil, 1080×1920, 30 fps, CRF 19, `+faststart`, audio AAC 192k
normalizado a −14 LUFS (el estándar de loudness de estas plataformas).

## Cómo se ve

El armado en `--layout blur` de arriba abajo: banda del hook, el cuadro del
video a todo el ancho en el tercio medio, los subtítulos justo debajo y el
crédito al pie. El fondo que queda a los lados es el mismo cuadro ampliado,
desenfocado y oscurecido, así que el clip nunca muestra barras negras muertas.

Con `--layout cover` el video llena toda la pantalla y el hook y los
subtítulos van encima; sirve para primeros planos, pero recorta mucho: de un
16:9 solo sobrevive la franja central.

## Escribir el hook

Los primeros dos segundos deciden si alguien se queda. Sirve como referencia:

- El hook nombra el conflicto, no el tema. «EL ERROR DE ABELARDO CON LA
  URGENCIA MANIFIESTA» funciona; «CARLOS CARRILLO HABLA DE CONTRATACIÓN», no.
- Tres líneas cortas leen mejor que dos largas.
- Que el hook no repita literalmente lo primero que se dice en el audio.
- Mayúsculas, sin punto final.
