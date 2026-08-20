#!/usr/bin/env bash
# unir.sh — Pega varios tramos ya renderizados en un solo archivo, sin recodificar.
#
#   clip/bin/unir.sh salida.mp4 gancho.mp4 cuerpo.mp4
#
# Solo funciona si todos los tramos salieron de render.sh con los mismos ajustes
# (misma resolución, mismos fps y mismo códec), que es el caso por defecto.

set -euo pipefail
[[ $# -ge 3 ]] || { echo "Uso: unir.sh salida.mp4 tramo1.mp4 tramo2.mp4 [...]" >&2; exit 1; }

SALIDA="$1"; shift
LISTA="$(mktemp)"; trap 'rm -f "$LISTA"' EXIT
for f in "$@"; do
  [[ -f "$f" ]] || { echo "No existe: $f" >&2; exit 1; }
  printf "file '%s'\n" "$(cd "$(dirname "$f")" && pwd)/$(basename "$f")" >> "$LISTA"
done

ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$LISTA" \
  -c copy -movflags +faststart "$SALIDA"

echo "Listo: $SALIDA"
ffprobe -v error -show_entries format=duration -show_entries stream=codec_name,width,height \
  -of default=noprint_wrappers=1 "$SALIDA"
