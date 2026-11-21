#!/usr/bin/env bash
# Package the release build for Windows (.zip) or Linux (.tar.gz); macOS uses
# bundle-macos.sh. Run after `cargo build --release -p clipperstudio_app` and
# scripts/stage-tools.sh.
#
#   scripts/bundle.sh <windows|linux>
#
# Layout (what bundle_resources() in crates/app/src/main.rs looks for):
#   ClipperStudio/clipperstudio[.exe]
#   ClipperStudio/resources/engine-bin/      ffmpeg, ffprobe, yt-dlp and their notices
#   ClipperStudio/resources/assets/{fonts,models}/
#   ClipperStudio/LICENSE, THIRD_PARTY_NOTICES.md
set -euo pipefail

os="${1:?usage: bundle.sh <windows|linux>}"
root="$(cd "$(dirname "$0")/.." && pwd)"
target_dir="${CARGO_TARGET_DIR:-$root/target}"
exe=""
[[ "$os" == windows ]] && exe=.exe

version="$(awk '
  /^\[/ { in_package = ($0 == "[package]") }
  in_package && /^version[[:space:]]*=/ { gsub(/.*=[[:space:]]*"|".*/, ""); print; exit }
' "$root/crates/app/Cargo.toml")"
arch="$(uname -m)"
[[ "$arch" == x86_64 || "$arch" == amd64 ]] && arch=x64
[[ "$arch" == arm64 ]] && arch=aarch64

for tool in "ffmpeg$exe" "ffprobe$exe" "yt-dlp$exe"; do
  [[ -f "$root/engine-bin/$tool" ]] || { echo "engine-bin/$tool is missing (scripts/stage-tools.sh $os)" >&2; exit 1; }
done

out="$target_dir/bundle"
app="$out/ClipperStudio"
rm -rf "$app"
mkdir -p "$app/resources/assets"
cp "$target_dir/release/clipperstudio-app$exe" "$app/clipperstudio$exe"
cp -R "$root/engine-bin" "$app/resources/engine-bin"
cp -R "$root/crates/engine/assets/fonts" "$root/crates/engine/assets/models" "$app/resources/assets/"
cp "$root/LICENSE" "$root/THIRD_PARTY_NOTICES.md" "$app/"

name="ClipperStudio_${version}_${os}_${arch}"
cd "$out"
if [[ "$os" == windows ]]; then
  rm -f "$name.zip"
  7z a -tzip -bso0 "$name.zip" ClipperStudio
  echo "==> $out/$name.zip"
else
  tar czf "$name.tar.gz" ClipperStudio
  echo "==> $out/$name.tar.gz"
fi
