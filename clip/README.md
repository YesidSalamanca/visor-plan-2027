# Clips verticales con gancho

Herramientas para sacar clips de formato TikTok a partir de una grabación larga.

## El formato

El clip se arma en dos tramos pegados:

1. **El gancho.** La frase más fuerte de toda la intervención, sacada de donde
   caiga dentro del clip y puesta al principio, **en blanco y negro**. Dura lo
   que dure la frase, entre 5 y 10 segundos.
2. **El cuerpo.** El clip completo desde su inicio, **en color**, incluida otra
   vez la frase del gancho cuando le llega el turno.

El blanco y negro es lo que marca que ese arranque es el gancho, no un filtro
para todo el video. Los subtítulos van igual en los dos tramos.

Cada tramo se renderiza por separado con `bin/render.sh` (`--bn si` para el
gancho, `--bn no` para el cuerpo) y se pegan con `bin/unir.sh`, que no
recodifica.

## Requisitos

- `ffmpeg` con `libx264`, `libfreetype` (drawtext) y `libass` (subtitles).
- Para transcribir sin conexión: `pip install sherpa-onnx numpy`, más el modelo
  Whisper en ONNX y el VAD Silero (ver *Transcripción*).

## Render

```bash
# 1) El gancho, en blanco y negro
clip/bin/render.sh --src grabacion.mp4 --inicio 99.9 --fin 108.45 --bn si \
  --fuente clip/fuentes/Roboto-700.ttf --subs gancho.srt --salida gancho.mp4

# 2) El cuerpo, en color
clip/bin/render.sh --src grabacion.mp4 --inicio 64.5 --fin 143.6 --bn no \
  --fuente clip/fuentes/Roboto-700.ttf --subs clip.srt --salida cuerpo.mp4

# 3) Pegarlos
clip/bin/unir.sh clip.mp4 gancho.mp4 cuerpo.mp4
```

Para sacar el `.srt` del gancho a partir del `.srt` del clip completo:

```bash
clip/bin/recortar-subs.py clip.srt gancho.srt --inicio 35.40 --fin 43.95
```

| Opción | Para qué sirve |
|---|---|
| `--src` | Archivo fuente. |
| `--inicio` / `--fin` / `--duracion` | Recorte temporal (`00:01:04.5` o `64.5`). |
| `--bn` | `si` blanco y negro (para el gancho), `no` color (para el cuerpo). |
| `--hook` / `--hook-dur` | Titular sobreimpreso de apertura. El formato de referencia no lo usa —el gancho es el propio recorte en blanco y negro—, pero queda disponible. Usa `\n` para separar líneas; el tamaño se ajusta solo. |
| `--credito` | Línea discreta al pie: nombre, programa, fecha. |
| `--subs` | `.srt` o `.ass` que se quema en el video. |
| `--layout` | `blur` (cuadro completo sobre fondo desenfocado, el que menos recorta) o `cover` (encuadre cerrado a pantalla completa). |
| `--offset-x` | Corre el encuadre en `cover` si la persona no está centrada. |
| `--precrop` | `ancho:alto:x:y` para aislar un recuadro de la fuente — p. ej. una sola cámara de una cuadrícula de Zoom. |
| `--realce` | `si` (por defecto) limpia el ruido de compresión y afila tras ampliar. Ponlo en `no` si la fuente ya está en alta resolución. |
| `--grano` | `si` (por defecto) añade grano fino; disimula los artefactos del blanco y negro. |
| `--hook-y` | Sube o baja el titular si tapa algo del encuadre. |
| `--subs-tam` / `--subs-margen` | Tamaño de los subtítulos y separación desde el borde inferior. |
| `--subs-mayus` | `si` pone los subtítulos en mayúsculas. Por defecto `no`, que es como van en la referencia. |
| `--subs-resaltado` | Color en hexadecimal de la palabra que se está diciendo. Por defecto `FCCB04`, el amarillo del video de referencia. Vacío desactiva el resaltado. |
| `--subs-ancho` | Caracteres por línea antes de partir (24 por defecto, que deja una sola línea corta). |
| `--subs-contorno` | Grosor del contorno negro del subtítulo. |
| `--fuente` | Ruta a un `.ttf` en negrita si quieres otra tipografía. |

## Aislar un recuadro de una cuadrícula de Zoom

Saca un fotograma, mide dónde están las separaciones negras y pásalas a
`--precrop`:

```bash
ffmpeg -ss 20 -i grabacion.mp4 -frames:v 1 muestra.png
python3 - <<'PY'
from PIL import Image; import numpy as np
im = np.array(Image.open('muestra.png').convert('L')).astype(int)
col, row = im.mean(axis=0), im.mean(axis=1)
print([i for i,v in enumerate(col) if v < 45])   # separaciones verticales
print([i for i,v in enumerate(row) if v < 45])   # separaciones horizontales
PY
```

## Transcripción sin conexión

Cuando no hay salida a YouTube ni a los CDN de modelos, `sherpa-onnx` sirve
porque se instala desde PyPI y sus modelos están publicados como *release
assets* de GitHub:

```bash
pip install sherpa-onnx numpy
mkdir -p /opt/asr && cd /opt/asr
BASE=https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models
curl -L -o w.tar.bz2 $BASE/sherpa-onnx-whisper-small.tar.bz2 && tar xf w.tar.bz2
curl -L -o silero_vad.onnx $BASE/silero_vad.onnx
```

`bin/transcribir.py` corta el audio con el VAD y pasa cada tramo por Whisper,
devolviendo un JSON con tiempos y texto. Requiere audio mono a 16 kHz:

```bash
ffmpeg -i grabacion.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le audio16k.wav
python3 clip/bin/transcribir.py audio16k.wav transcripcion.json
```

## Subtítulos sincronizados

`bin/hacer_srt.py` reparte un texto ya corregido a mano sobre los tramos donde
sí hay voz, tomándolos de `silencedetect`. Así los subtítulos no se desfasan en
las pausas largas:

```bash
ffmpeg -i audio16k.wav -af "silencedetect=noise=-32dB:d=0.16" -f null - 2>&1 \
  | grep -E "silence_(start|end)" > silencios.txt
python3 clip/bin/hacer_srt.py silencios.txt clip.srt
```

Las anclas (tiempo de inicio, tiempo de fin, texto) se editan dentro del script.
Conviene verificar los bordes de cada ancla transcribiendo ventanas sueltas con
`bin/ventana.py`, porque Whisper corrige nombres propios y siglas de forma
inconsistente (`UNGRD` sale como *UNRD*, *UNHRD* o *UNGD*; `1523` como *15 23*).

## Tipografía

En `clip/fuentes/` quedan descargadas de Google Fonts las candidatas para los
subtítulos. La que usa el video de referencia es **Roboto Bold**
(`Roboto-700.ttf`), que además es la que trae CapCut por defecto. Para cambiarla
basta pasar otra con `--fuente`.

## Otros scripts

| Script | Para qué |
|---|---|
| `bin/unir.sh` | Pega los tramos ya renderizados sin recodificar. Todos tienen que venir de `render.sh` con los mismos ajustes. |
| `bin/descargar.sh` | Baja el video (y sus subtítulos automáticos) con `yt-dlp`. Acepta `--seccion "*01:10:00-01:14:00"` para traer solo un tramo. Necesita salida a YouTube, así que hay que correrlo en una máquina local. |
| `bin/transcribir.sh` | Genera un `.srt` con Whisper cuando no hay subtítulos automáticos. También pide descargar el modelo. |
| `bin/buscar.py` | Busca frases dentro de un `.srt` y dice en qué minuto están. Útil para ubicar el tramo antes de cortar. |
| `bin/ventana.py` | Transcribe ventanas sueltas (`ventana.py audio.wav 46-53 52-59`) para verificar dónde empieza y termina una frase. |
| `bin/recortar-subs.py` | Recorta un `.srt` largo al tramo del clip y lo vuelve a poner en cero. |
| `bin/srt2ass.py` | Convierte un `.srt` a `.ass` con el estilo vertical, si quieres retocar el subtítulo a mano. |
