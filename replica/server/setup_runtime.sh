#!/usr/bin/env bash
# One-time setup on minerva: Blender 4.5.10 linux + static ffmpeg (with libass) under the runtime dir.
set -Eeuo pipefail
RT=/data/users/zhichaoz/blender-render/runtime
mkdir -p "$RT" && cd "$RT"
if [[ ! -x blender-4.5.10-linux-x64/blender ]]; then
    curl -L -o blender.tar.xz https://download.blender.org/release/Blender4.5/blender-4.5.10-linux-x64.tar.xz
    tar -xf blender.tar.xz && rm blender.tar.xz
fi
if [[ ! -x ffmpeg/ffmpeg ]]; then
    curl -L -o ffmpeg.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
    mkdir -p ffmpeg && tar -xf ffmpeg.tar.xz --strip-components=1 -C ffmpeg && rm ffmpeg.tar.xz
fi
echo "== blender"; blender-4.5.10-linux-x64/blender --version | head -2
echo "== missing libs"; ldd blender-4.5.10-linux-x64/blender | grep "not found" || echo "none"
echo "== ffmpeg"; ffmpeg/ffmpeg -version | head -1; ffmpeg/ffmpeg -filters 2>/dev/null | grep -c -E " subtitles | xfade | maskedmerge | gblur "
