#!/usr/bin/env bash
# Run in the builder with: dbus-run-session -- xvfb-run -a bash packaging/appimage/check.sh
set -euo pipefail
repo_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
appimages=("$repo_dir"/dist/*-x86_64.AppImage)
[[ ${#appimages[@]} == 1 ]] || { echo 'Expected exactly one AppImage in dist/' >&2; exit 1; }
test_dir=$(mktemp -d)
trap 'rm -rf -- "$test_dir"' EXIT
export XDG_CONFIG_HOME="$test_dir/config" XDG_DATA_HOME="$test_dir/data"
appimage=${appimages[0]}
# No accessibility service runs inside this private headless test session.
export GTK_A11Y=none
APPIMAGE_EXTRACT_AND_RUN=1 "$appimage" --language en --demo status
APPIMAGE_EXTRACT_AND_RUN=1 "$appimage" --install-desktop
desktop-file-validate "$XDG_DATA_HOME/applications/io.github.btd700linux.Control.desktop"
APPIMAGE_EXTRACT_AND_RUN=1 "$appimage" --remove-desktop
test ! -e "$XDG_DATA_HOME/applications/io.github.btd700linux.Control.desktop"
cd "$test_dir"
"$appimage" --appimage-extract > /dev/null
export APPDIR="$test_dir/squashfs-root"
. "$APPDIR/usr/share/btd700-control/appimage-environment.sh"
"$APPDIR/usr/bin/python3.12" - <<'PY'
import os, sys, gi
from pathlib import Path
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf
root = Path(os.environ['APPDIR'])
assert Path(sys.prefix).is_relative_to(root)
assert Path(gi.__file__).is_relative_to(root)
icon = GdkPixbuf.Pixbuf.new_from_file(str(root / 'btd700-control.svg'))
assert icon.get_width() == 128
print('PASS: bundled Python, PyGObject, SVG loader and MIME recognition')
PY
export BTD700_TEST_INSTALLED=1 BTD700_TEST_TRAY_HOST=1
for language in en de; do
    BTD700_LANGUAGE=$language "$APPDIR/usr/bin/python3.12" "$repo_dir/tools/check_gui.py"
done
# Also exercise the actual runtime/extraction entry point into the GUI.
"$APPDIR/usr/bin/python3.12" "$repo_dir/tools/tray_test_host.py" > "$test_dir/tray.log" &
tray_pid=$!
trap 'kill "$tray_pid" 2>/dev/null || true; rm -rf -- "$test_dir"' EXIT
for attempt in {1..50}; do
    if [[ $(cat "$test_dir/tray.log") == TEST_TRAY_READY ]]; then break; fi
    sleep 0.1
done
APPIMAGE_EXTRACT_AND_RUN=1 "$appimage" --demo --smoke-seconds 3
