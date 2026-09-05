#!/usr/bin/env bash
# Run inside the Ubuntu 24.04 builder (see docs/APPIMAGE.md).
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
repo_dir=$PWD
version=$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')
build_dir="$repo_dir/build/appimage"
sources_dir="$build_dir/dependency-sources"
mkdir -p "$build_dir/downloads" "$sources_dir" dist

download() {
    local url=$1 name=$2 checksum=$3
    if [[ ! -f "$build_dir/downloads/$name" ]]; then
        curl --fail --location --retry 3 "$url" -o "$build_dir/downloads/$name"
    fi
    echo "$checksum  $build_dir/downloads/$name" | sha256sum --check
}
download https://github.com/AppImage/appimagetool/releases/download/1.9.1/appimagetool-x86_64.AppImage appimagetool \
    ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0
download https://github.com/AppImage/type2-runtime/releases/download/20251108/runtime-x86_64 runtime-x86_64 \
    2fca8b443c92510f1483a883f60061ad09b46b978b2631c807cd873a47ec260d
chmod +x "$build_dir/downloads/appimagetool"
python3 packaging/appimage/assemble.py

# Keep the exact corresponding Ubuntu sources alongside the downloadable binary.
# apt checks the archives against the signed repository's source index.
cd "$sources_dir"
while IFS= read -r package; do
    apt-get source --download-only "$package"
done < "$build_dir/sources.txt"
curl --fail --location --retry 3 https://github.com/AppImage/type2-runtime/archive/refs/tags/20251108.tar.gz -o type2-runtime-20251108.tar.gz
download https://github.com/libfuse/libfuse/releases/download/fuse-3.15.0/fuse-3.15.0.tar.xz fuse-3.15.0.tar.xz \
    70589cfd5e1cff7ccd6ac91c86c01be340b227285c5e200baa284e401eea2ca0
download https://github.com/vasi/squashfuse/archive/0.5.2.tar.gz squashfuse-0.5.2.tar.gz \
    db0238c5981dabbd80ee09ae15387f390091668ca060a7bc38047912491443d3
cp "$build_dir/downloads/fuse-3.15.0.tar.xz" "$build_dir/downloads/squashfuse-0.5.2.tar.gz" .
cp "$build_dir/packages.json" "$build_dir/sources.txt" .
rm -rf -- "$sources_dir/build-instructions"
cp -r "$repo_dir/packaging/appimage" build-instructions
cp "$repo_dir/docs/APPIMAGE.md" README.md
tar -xOf type2-runtime-20251108.tar.gz type2-runtime-20251108/LICENSE > "$build_dir/BTD_700_Control.AppDir/usr/share/doc/btd700-bundled/AppImage-runtime.LICENSE"
tar -xOf fuse-3.15.0.tar.xz fuse-3.15.0/LGPL2.txt > "$build_dir/BTD_700_Control.AppDir/usr/share/doc/btd700-bundled/libfuse.LICENSE"
tar -xOf squashfuse-0.5.2.tar.gz squashfuse-0.5.2/LICENSE > "$build_dir/BTD_700_Control.AppDir/usr/share/doc/btd700-bundled/squashfuse.LICENSE"
# Permissive runtime dependency notices (the upstream runtime LICENSE links these).
curl -fsSL --retry 3 https://git.musl-libc.org/cgit/musl/plain/COPYRIGHT?h=v1.2.5 -o "$build_dir/BTD_700_Control.AppDir/usr/share/doc/btd700-bundled/musl.COPYRIGHT"
curl -fsSL --retry 3 https://raw.githubusercontent.com/facebook/zstd/v1.5.6/LICENSE -o "$build_dir/BTD_700_Control.AppDir/usr/share/doc/btd700-bundled/zstd.LICENSE"
curl -fsSL --retry 3 https://raw.githubusercontent.com/madler/zlib/v1.3.1/LICENSE -o "$build_dir/BTD_700_Control.AppDir/usr/share/doc/btd700-bundled/zlib.LICENSE"
cd "$repo_dir"
archive="BTD_700_Control-$version-dependency-sources.tar.gz"
tar --exclude='__pycache__' -czf "dist/$archive" -C "$build_dir" dependency-sources
ARCH=x86_64 VERSION="$version" APPIMAGE_EXTRACT_AND_RUN=1 "$build_dir/downloads/appimagetool" \
    --no-appstream --mksquashfs-opt -processors --mksquashfs-opt 2 \
    --runtime-file "$build_dir/downloads/runtime-x86_64" \
    "$build_dir/BTD_700_Control.AppDir" "dist/BTD_700_Control-$version-x86_64.AppImage"
cp "$build_dir/packages.json" "dist/BTD_700_Control-$version-packages.json"
cp packaging/70-btd700-control.rules dist/
cd dist
sha256sum "BTD_700_Control-$version-x86_64.AppImage" "$archive" \
    "BTD_700_Control-$version-packages.json" 70-btd700-control.rules > SHA256SUMS
