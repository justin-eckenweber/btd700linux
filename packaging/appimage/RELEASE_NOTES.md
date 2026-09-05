Download **BTD_700_Control-0.3.0-x86_64.AppImage**, make it executable and open it.
Python, GTK, libadwaita and the tray library are included. Requires **x86-64 Linux
with glibc 2.39+** (such as Ubuntu 24.04 or newer). English and German are supported.

```bash
chmod +x BTD_700_Control-0.3.0-x86_64.AppImage
./BTD_700_Control-0.3.0-x86_64.AppImage
```

Optional `--install-desktop` adds an application-menu entry. Keep the file at that
location; enable Start at login in the app for tray autostart. `--remove-desktop`
removes both entries. If FUSE is unavailable, prefix the launch command with
`APPIMAGE_EXTRACT_AND_RUN=1`.

GNOME still needs a working AppIndicator/StatusNotifier extension. If USB access
is denied, install the attached udev rule following the README instructions.
SHA256SUMS covers the binary, package manifest, USB rule and dependency source archive.
The large `dependency-sources.tar.gz` is for reviewing/rebuilding libraries and is
not needed to run the app. GitHub's Source code archives contain the app itself.

**Independent, AI-developed (OpenAI Codex), experimental software. No warranty or
guarantee of compatibility.** Project code is MIT-licensed; bundled dependencies
retain their own licenses. Controls only: no firmware updates, downloads or update APIs.
