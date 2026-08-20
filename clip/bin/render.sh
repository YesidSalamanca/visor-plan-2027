#!/usr/bin/env bash
# render.sh — Renderiza un clip vertical 9:16 en blanco y negro con hook inicial
# y subtítulos quemados, al estilo de los clips de TikTok.
#
# Uso:
#   clip/bin/render.sh --src video.mp4 --inicio 00:12:34 --fin 00:13:10 \
#     --hook "EL ERROR DE ABELARDO\nCON LA URGENCIA MANIFIESTA" \
#     --subs clip/salida/clip.srt --salida clip/salida/clip.mp4
#
# Ver clip/README.md para todas las opciones.

set -euo pipefail

SRC=""; INICIO=""; FIN=""; DURACION=""
HOOK=""; HOOK_DUR="4"
CREDITO=""
SUBS=""
LAYOUT="blur"        # blur | cover
OFFSET_X="0"         # corrimiento horizontal del encuadre en layout cover
PRECROP=""           # recorte previo "ancho:alto:x:y" (p. ej. un recuadro de Zoom)
REALCE="si"          # realce de nitidez, útil cuando hay que ampliar mucho la fuente
GRANO="si"           # si | no
BN_MODO="si"         # si = blanco y negro (gancho) | no = color (cuerpo del clip)
SUBS_TAM="68"        # tamaño de los subtítulos en píxeles
SUBS_MARGEN=""       # distancia al borde inferior; por defecto según layout
SUBS_MAYUS="no"      # subtítulos en mayúsculas
SUBS_RESALTADO="FCCB04"  # color de la palabra que se está diciendo; vacío lo desactiva
SUBS_ANCHO="28"      # caracteres por línea de subtítulo
SUBS_CONTORNO="4"    # grosor del contorno negro
HOOK_Y="150"         # distancia del hook al borde superior
SALIDA="clip/salida/clip.mp4"
FUENTE_TTF=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --src)       SRC="$2"; shift 2 ;;
    --inicio)    INICIO="$2"; shift 2 ;;
    --fin)       FIN="$2"; shift 2 ;;
    --duracion)  DURACION="$2"; shift 2 ;;
    --hook)      HOOK="$2"; shift 2 ;;
    --hook-dur)  HOOK_DUR="$2"; shift 2 ;;
    --hook-y)    HOOK_Y="$2"; shift 2 ;;
    --credito)   CREDITO="$2"; shift 2 ;;
    --subs)      SUBS="$2"; shift 2 ;;
    --layout)    LAYOUT="$2"; shift 2 ;;
    --offset-x)  OFFSET_X="$2"; shift 2 ;;
    --precrop)   PRECROP="$2"; shift 2 ;;
    --realce)    REALCE="$2"; shift 2 ;;
    --grano)     GRANO="$2"; shift 2 ;;
    --bn)        BN_MODO="$2"; shift 2 ;;
    --subs-tam)  SUBS_TAM="$2"; shift 2 ;;
    --subs-margen) SUBS_MARGEN="$2"; shift 2 ;;
    --subs-mayus)  SUBS_MAYUS="$2"; shift 2 ;;
    --subs-resaltado) SUBS_RESALTADO="$2"; shift 2 ;;
    --subs-ancho)  SUBS_ANCHO="$2"; shift 2 ;;
    --subs-contorno) SUBS_CONTORNO="$2"; shift 2 ;;
    --salida)    SALIDA="$2"; shift 2 ;;
    --fuente)    FUENTE_TTF="$2"; shift 2 ;;
    -h|--help)   sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "Opción desconocida: $1" >&2; exit 1 ;;
  esac
done

[[ -n "$SRC" ]] || { echo "Falta --src" >&2; exit 1; }
[[ -f "$SRC" ]] || { echo "No existe el archivo fuente: $SRC" >&2; exit 1; }
[[ -n "$INICIO" ]] || { echo "Falta --inicio" >&2; exit 1; }
[[ -n "$FIN" || -n "$DURACION" ]] || { echo "Falta --fin o --duracion" >&2; exit 1; }

# --- Fuente tipográfica -------------------------------------------------------
if [[ -z "$FUENTE_TTF" ]]; then
  for f in \
    /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf \
    /usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf \
    /usr/share/fonts/truetype/freefont/FreeSansBold.ttf \
    /System/Library/Fonts/Helvetica.ttc \
    /Library/Fonts/Arial\ Bold.ttf ; do
    [[ -f "$f" ]] && { FUENTE_TTF="$f"; break; }
  done
fi
[[ -f "$FUENTE_TTF" ]] || { echo "No encontré una fuente TTF en negrita; pasa --fuente /ruta/Fuente.ttf" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# --- Texto del hook -----------------------------------------------------------
# drawtext lee el texto desde archivo para no pelear con tildes ni comillas.
HOOK_FILE="$TMP/hook.txt"
if [[ -n "$HOOK" ]]; then
  # Si el hook viene en una sola línea larga, lo partimos solo en espacios.
  printf '%b' "${HOOK//\\n/$'\n'}" \
    | python3 -c '
import sys, textwrap
lineas = []
for l in sys.stdin.read().rstrip("\n").split("\n"):
    lineas.extend(textwrap.wrap(l, width=20) or [""])
sys.stdout.write("\n".join(lineas))
' > "$HOOK_FILE"
  HOOK_LINEAS=$(awk 'END { print NR }' "$HOOK_FILE")
  LARGO_MAX=$(awk '{ if (length($0) > m) m = length($0) } END { print m+0 }' "$HOOK_FILE")
  # Ancho útil de 900px sobre 1080; en negrita cada glifo avanza ~0.68 del cuerpo.
  HOOK_SIZE=$(awk -v l="$LARGO_MAX" 'BEGIN {
    s = int(900 / (0.68 * (l > 0 ? l : 1)));
    if (s > 92) s = 92; if (s < 38) s = 38; print s }')
fi

# --- Recorte temporal ---------------------------------------------------------
RECORTE=(-ss "$INICIO")
if [[ -n "$FIN" ]]; then RECORTE+=(-to "$FIN"); else RECORTE+=(-t "$DURACION"); fi

# --- Cadena de filtros --------------------------------------------------------
# Preprocesado: aísla un recuadro de la fuente (Zoom, split screen) y, si toca
# ampliarlo mucho, limpia el ruido de compresión antes de escalar.
PRE=""
REALCE_POST=""
[[ -n "$PRECROP" ]] && PRE="crop=${PRECROP},"
if [[ "$REALCE" == "si" ]]; then
  PRE="${PRE}hqdn3d=2:1.5:3:3,"
  REALCE_POST=",unsharp=5:5:0.9:5:5:0.0"
fi

# 1) Blanco y negro con contraste levantado (look editorial, no gris plano).
if [[ "$BN_MODO" == "si" ]]; then
  BN="hue=s=0,eq=contrast=1.14:brightness=0.015:gamma=0.98,curves=all='0/0 0.25/0.20 0.5/0.52 0.75/0.82 1/1'"
else
  # En color solo levantamos un poco el contraste, sin tocar la saturación.
  BN="eq=contrast=1.06:brightness=0.01:saturation=1.05"
fi

case "$LAYOUT" in
  blur)
    # Fondo: el mismo cuadro ampliado, desenfocado y oscurecido.
    # Frente: el cuadro completo a todo el ancho, centrado en el tercio medio.
    LAYOUT_FILTER="\
[0:v]fps=30,setpts=PTS-STARTPTS,${PRE}split=2[bg][fg];
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.16:contrast=0.95[bgb];
[fg]scale=1080:-2:flags=lanczos${REALCE_POST}[fgs];
[bgb][fgs]overlay=x=0:y=(H-h)/2+40:shortest=1[comp]"
    ;;
  cover)
    # Encuadre cerrado a pantalla completa; --offset-x mueve el recorte.
    LAYOUT_FILTER="\
[0:v]fps=30,setpts=PTS-STARTPTS,${PRE}scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,\
crop=1080:1920:(iw-1080)/2+${OFFSET_X}:(ih-1920)/2[comp]"
    ;;
  *) echo "--layout debe ser blur o cover" >&2; exit 1 ;;
esac

FILTROS="$LAYOUT_FILTER;[comp]${BN}[bn]"

if [[ "$GRANO" == "si" ]]; then
  FILTROS="${FILTROS};[bn]noise=alls=7:allf=t+u[gr]"
  ULTIMO="gr"
else
  ULTIMO="bn"
fi

# 2) Hook: banda superior + titular, visible los primeros segundos.
#    Cada línea se dibuja por separado para que quede centrada de verdad
#    (drawtext alinea el bloque completo, no las líneas dentro del bloque).
if [[ -n "$HOOK" ]]; then
  PAD=45
  INTERLINEA=$(( HOOK_SIZE + 22 ))
  ALTO_BANDA=$(( HOOK_LINEAS * INTERLINEA + 2 * PAD ))
  CADENA="drawbox=x=0:y=${HOOK_Y}:w=1080:h=${ALTO_BANDA}:color=black@0.62:t=fill:enable='lt(t\,${HOOK_DUR})'"
  i=0
  while IFS= read -r linea; do
    printf '%s' "$linea" > "$TMP/hook_${i}.txt"
    Y=$(( HOOK_Y + PAD + i * INTERLINEA ))
    CADENA="${CADENA},drawtext=fontfile='${FUENTE_TTF}':textfile='${TMP}/hook_${i}.txt':\
fontcolor=white:fontsize=${HOOK_SIZE}:borderw=6:bordercolor=black@0.9:\
x=(w-text_w)/2:y=${Y}:enable='lt(t\,${HOOK_DUR})'"
    i=$(( i + 1 ))
  done < <(cat "$HOOK_FILE"; echo)
  FILTROS="${FILTROS};[${ULTIMO}]${CADENA}[hk]"
  ULTIMO="hk"
fi

# 3) Crédito discreto abajo (nombre del programa, fecha, @usuario).
if [[ -n "$CREDITO" ]]; then
  CREDITO_ESC=$(printf '%s' "$CREDITO" | sed -e "s/\\\\/\\\\\\\\/g" -e "s/:/\\\\:/g" -e "s/'/\\\\\\\\\\\\'/g")
  FILTROS="${FILTROS};[${ULTIMO}]drawtext=fontfile='${FUENTE_TTF}':text='${CREDITO_ESC}':\
fontcolor=white@0.75:fontsize=30:borderw=3:bordercolor=black@0.8:\
x=(w-text_w)/2:y=h-70[cr]"
  ULTIMO="cr"
fi

# 4) Subtítulos quemados (estilo TikTok: negrita, blanco, contorno negro grueso).
if [[ -n "$SUBS" ]]; then
  [[ -f "$SUBS" ]] || { echo "No existe el archivo de subtítulos: $SUBS" >&2; exit 1; }
  if [[ -z "$SUBS_MARGEN" ]]; then
    # En layout blur los subtítulos van justo debajo del bloque de video.
    [[ "$LAYOUT" == "blur" ]] && SUBS_MARGEN=420 || SUBS_MARGEN=260
  fi
  FUENTE_DIR="$(dirname "$FUENTE_TTF")"
  FUENTE_NOMBRE="$(fc-query -f '%{family[0]}' "$FUENTE_TTF" 2>/dev/null || echo 'DejaVu Sans')"
  ASS="$TMP/subs.ass"
  if [[ "$SUBS" == *.ass ]]; then
    cp "$SUBS" "$ASS"
  else
    EXTRA=(); [[ "$SUBS_MAYUS" == "si" ]] && EXTRA+=(--mayusculas)
    [[ -n "$SUBS_RESALTADO" ]] && EXTRA+=(--resaltado "$SUBS_RESALTADO")
    python3 "$(dirname "$0")/srt2ass.py" "$SUBS" "$ASS" \
      --fuente "$FUENTE_NOMBRE" --tam "$SUBS_TAM" --margen "$SUBS_MARGEN" \
      --ancho "$SUBS_ANCHO" --contorno "$SUBS_CONTORNO" "${EXTRA[@]}" >/dev/null
  fi
  SUBS_ESC=$(printf '%s' "$ASS" | sed -e 's/\\/\\\\/g' -e "s/'/\\\\'/g" -e 's/:/\\:/g')
  FILTROS="${FILTROS};[${ULTIMO}]subtitles='${SUBS_ESC}':fontsdir='${FUENTE_DIR}'[sb]"
  ULTIMO="sb"
fi

# 5) Fundidos de entrada y salida.
FILTROS="${FILTROS};[${ULTIMO}]fade=t=in:st=0:d=0.35,format=yuv420p[vout]"

mkdir -p "$(dirname "$SALIDA")"

# Solo normalizamos audio si el archivo fuente trae pista de audio.
AUDIO_OPTS=()
if ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of csv=p=0 "$SRC" | grep -q .; then
  AUDIO_OPTS=(-map 0:a:0
    -af "afade=t=in:st=0:d=0.2,loudnorm=I=-14:TP=-1.5:LRA=11"
    -c:a aac -b:a 192k -ar 48000 -ac 2)
else
  echo "Aviso: la fuente no tiene audio; el clip saldrá mudo." >&2
  AUDIO_OPTS=(-an)
fi

ffmpeg -hide_banner -loglevel error -stats -y \
  "${RECORTE[@]}" -i "$SRC" \
  -filter_complex "$(printf '%s' "$FILTROS" | tr -d '\n')" \
  -filter_complex_threads 4 \
  -map '[vout]' "${AUDIO_OPTS[@]}" \
  -c:v libx264 -preset slow -crf 19 -profile:v high -level 4.1 \
  -pix_fmt yuv420p -r 30 -g 60 \
  -movflags +faststart \
  "$SALIDA"

echo "Listo: $SALIDA"
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height \
  -of default=noprint_wrappers=1 "$SALIDA"
