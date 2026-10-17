#!/bin/sh
# Encode a raw clip (from _inbox or a local source folder) into the web
# profile used under assets/videos/: H.264, scaled so the short side is
# 720px, faststart, with audio kept by default (AAC 128k, loudness
# normalized). This replaces the old copy-pasted shell one-liner that
# had `-an` baked in unconditionally — that flag is what silently
# stripped audio from every video it touched, including ones that were
# never meant to be silent. A brief that says a <video> tag should be
# "muted" is about the HTML5 muted attribute (for autoplay), not about
# dropping the audio track during encoding — keep the two separate.
#
# Usage:
#   scripts/process_video.sh <source> <output-name> [options]
#
# Options:
#   --start SECONDS     Trim start offset (-ss). Default: 0.
#   --duration SECONDS  Trim length (-t). Default: full remaining clip.
#   --hdr                Source is HDR (e.g. iPhone HLG/BT.2020 footage)
#                        and needs tonemapping down to SDR bt709. Check
#                        with: ffprobe -show_streams <source> | grep -i
#                        "color_transfer\|color_space" — arib-std-b67 or
#                        bt2020 means pass this flag.
#   --mute               Opt-in only: drop audio on purpose (e.g. wind
#                        noise only, no usable sound). Document why in
#                        the commit message whenever this is used.
#   --poster-at SECONDS  Also (re)generate <output-name>_poster.webp from
#                        this timestamp. Omit to leave an existing poster
#                        untouched.
#
# Requires ffmpeg on PATH, and cwebp if --poster-at is used. Writes into
# assets/videos/ at the repo root.
set -eu

SRC=""
OUT=""
START=0
DURATION=""
HDR=0
MUTE=0
POSTER_AT=""

if [ $# -lt 2 ]; then
  echo "Usage: $0 <source> <output-name> [--start S] [--duration S] [--hdr] [--mute] [--poster-at S]" >&2
  exit 1
fi
SRC="$1"; shift
OUT="$1"; shift

while [ $# -gt 0 ]; do
  case "$1" in
    --start) START="$2"; shift 2 ;;
    --duration) DURATION="$2"; shift 2 ;;
    --hdr) HDR=1; shift ;;
    --mute) MUTE=1; shift ;;
    --poster-at) POSTER_AT="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

command -v ffmpeg >/dev/null 2>&1 || { echo "ffmpeg not found on PATH" >&2; exit 1; }

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST_DIR="$REPO_ROOT/assets/videos"
mkdir -p "$DEST_DIR"
DEST="$DEST_DIR/$OUT.mp4"

HDR_FILTER="zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,"
VF_PREFIX=""
[ "$HDR" = "1" ] && VF_PREFIX="$HDR_FILTER"
VF="${VF_PREFIX}fps=30,scale='if(gt(iw,ih),-2,720)':'if(gt(iw,ih),720,-2)':flags=lanczos,format=yuv420p"

DUR_ARGS=""
[ -n "$DURATION" ] && DUR_ARGS="-t $DURATION"

AUDIO_ARGS="-c:a aac -b:a 128k -ar 48000 -af loudnorm=I=-16:TP=-1.5:LRA=11"
[ "$MUTE" = "1" ] && AUDIO_ARGS="-an"

# shellcheck disable=SC2086
ffmpeg -v error -y -ss "$START" $DUR_ARGS -i "$SRC" \
  -vf "$VF" \
  -c:v libx264 -preset slow -crf 24 -maxrate 2400k -bufsize 4800k -profile:v high -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  $AUDIO_ARGS \
  -movflags +faststart -map_metadata -1 \
  "$DEST"

if [ "$MUTE" != "1" ]; then
  if ! ffmpeg -v error -i "$DEST" -map 0:a -c copy -f null - >/dev/null 2>&1; then
    echo "WARNING: $OUT.mp4 has no audio stream but --mute was not passed — check the source has sound." >&2
  fi
fi

SIZE_KB=$(( $(stat -f%z "$DEST") / 1024 ))
echo "$OUT.mp4: ${SIZE_KB}KB"
if [ "$SIZE_KB" -gt 5120 ]; then
  echo "WARNING: $OUT.mp4 is over 5MB (${SIZE_KB}KB) — consider a shorter trim or lower maxrate." >&2
fi

if [ -n "$POSTER_AT" ]; then
  command -v cwebp >/dev/null 2>&1 || { echo "cwebp not found on PATH, skipping poster" >&2; exit 1; }
  TMP_PNG="$(mktemp -t poster).png"
  ffmpeg -v error -y -ss "$POSTER_AT" -i "$DEST" -frames:v 1 "$TMP_PNG"
  cwebp -quiet -q 78 -metadata none "$TMP_PNG" -o "$DEST_DIR/${OUT}_poster.webp"
  rm -f "$TMP_PNG"
  echo "${OUT}_poster.webp written"
fi
