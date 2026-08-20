#!/usr/bin/env bash
# transcribir.sh — Genera un .srt con Whisper cuando YouTube no trae subtítulos
# automáticos, o cuando los automáticos vienen demasiado sucios.
#
#   clip/bin/transcribir.sh clip/fuente/abq2sDpniuM.mp4
#
# Requiere: pip install -U faster-whisper   (descarga el modelo la primera vez)

set -euo pipefail
SRC="${1:-}"
MODELO="${2:-medium}"
[[ -f "$SRC" ]] || { echo "Uso: $0 <video-o-audio> [modelo]" >&2; exit 1; }

SALIDA="${SRC%.*}.srt"
python3 - "$SRC" "$SALIDA" "$MODELO" <<'PY'
import sys
from faster_whisper import WhisperModel

src, salida, modelo = sys.argv[1:4]
m = WhisperModel(modelo, device="cpu", compute_type="int8")
segmentos, info = m.transcribe(src, language="es", vad_filter=True,
                               word_timestamps=False)

def t(s):
    h, r = divmod(s, 3600)
    mnt, seg = divmod(r, 60)
    return f"{int(h):02d}:{int(mnt):02d}:{int(seg):02d},{int((seg % 1) * 1000):03d}"

with open(salida, "w", encoding="utf-8") as f:
    for i, s in enumerate(segmentos, 1):
        f.write(f"{i}\n{t(s.start)} --> {t(s.end)}\n{s.text.strip()}\n\n")
print(f"Transcripción escrita en {salida}")
PY
