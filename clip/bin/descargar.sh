#!/usr/bin/env bash
# descargar.sh — Baja el video fuente y, si existen, sus subtítulos automáticos.
#
#   clip/bin/descargar.sh "https://www.youtube.com/live/abq2sDpniuM"
#   clip/bin/descargar.sh "<url>" --seccion "*01:10:00-01:14:00"   # solo un tramo
#
# El tramo parcial (--seccion) baja muchísimo más rápido que la transmisión
# completa y es lo recomendable cuando ya sabes dónde está el momento.

set -euo pipefail

URL="${1:-}"
[[ -n "$URL" ]] || { echo "Uso: $0 <url> [--seccion '*HH:MM:SS-HH:MM:SS']" >&2; exit 1; }
shift

SECCION=""
DESTINO="clip/fuente"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --seccion) SECCION="$2"; shift 2 ;;
    --destino) DESTINO="$2"; shift 2 ;;
    *) echo "Opción desconocida: $1" >&2; exit 1 ;;
  esac
done

command -v yt-dlp >/dev/null || { echo "Falta yt-dlp (pip install -U yt-dlp)" >&2; exit 1; }
mkdir -p "$DESTINO"

ARGS=(
  --no-playlist
  --merge-output-format mp4
  -f "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height<=1080]+ba/b[height<=1080]/b"
  -o "${DESTINO}/%(id)s.%(ext)s"
  --write-auto-subs --write-subs --sub-langs "es.*,es" --sub-format "vtt"
  --convert-subs srt
)
[[ -n "$SECCION" ]] && ARGS+=(--download-sections "$SECCION" --force-keyframes-at-cuts)

yt-dlp "${ARGS[@]}" "$URL"

echo
echo "Archivos en ${DESTINO}:"
ls -la "$DESTINO"
