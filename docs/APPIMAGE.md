# AppImage packaging

The x86-64 AppImage bundles Python 3.12, PyGObject, GTK 4, libadwaita,
libdbusmenu, icons and fallback fonts from Ubuntu 24.04. It requires a Linux
host with **glibc 2.39 or newer** and a graphical Wayland or X11 session.
It does not bundle glibc, audio drivers or firmware. ARM and older glibc
distributions are not supported by this binary; running from source is another option.

## Download and use

Download the `.AppImage` from [GitHub Releases](https://github.com/justin-eckenweber/btd700linux/releases/latest),
make it executable, and open it. All regular CLI arguments also work.

```bash
chmod +x BTD_700_Control-*-x86_64.AppImage
./BTD_700_Control-0.3.1-x86_64.AppImage
./BTD_700_Control-0.3.1-x86_64.AppImage --demo
```

Put the file at its permanent location before adding a menu entry:

```bash
./BTD_700_Control-0.3.1-x86_64.AppImage --install-desktop
```

The menu entry and **Start at login** use the original AppImage path, not its
temporary mount. Moving or renaming the file requires installing the menu entry
again and toggling Start at login off/on. `--remove-desktop` removes this app's
menu entry, autostart entry and installed icon. It leaves the AppImage in place.

If FUSE is unavailable, use the runtime's extraction mode:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./BTD_700_Control-0.3.1-x86_64.AppImage
```

When installing a menu entry or enabling autostart from this mode, the launcher
preserves it using the runtime's `--appimage-extract-and-run` argument.

For a permanent launcher on such a system, extract once with `--appimage-extract`,
keep the resulting `squashfs-root` directory, and run its `AppRun`. The launcher
created from that extracted copy uses its `AppRun` wrapper. Remove its
desktop/autostart entries before deleting the directory.

GNOME still needs a working StatusNotifier/AppIndicator extension for a tray.
USB access uses the host's `/dev/hidraw` permissions. If access is denied, download
`70-btd700-control.rules` from the same release and install it as described in the
[README](../README.md#usb-permissions). The app never changes system permissions itself.

## Build

Run from the repository root using rootless Podman (Docker can also build the
same Containerfile):

```bash
podman build -t btd700-appimage-builder -f packaging/appimage/Containerfile .
podman run --rm -v "$PWD:/src:z" btd700-appimage-builder
```

Verify the resulting file on a minimal test host without Python, GTK, libadwaita
or libdbusmenu installed (CLI, menu installation/removal, both GUI languages,
real D-Bus tray events against a simulated device, and extraction-mode startup):

```bash
podman build -t btd700-appimage-test -f packaging/appimage/TestContainerfile .
podman run --rm -v "$PWD:/src:z" btd700-appimage-test
```

The output goes to `dist/`. Ubuntu source repositories are enabled in the builder.
`assemble.py` copies runtime files and follows their ELF dependencies, retaining
package versions and license texts. The build downloads the exact corresponding
Ubuntu source archives and publishes them in `*-dependency-sources.tar.gz`.
`*-packages.json` lists the binary and source versions. The container receives
current Ubuntu 24.04 security updates, so two builds at different times need not
be byte-identical. No host packages are installed by this process.

Appimagetool 1.9.1 and type2-runtime 20251108 are checksum-pinned. The dependency
source archive also includes the runtime source, its build scripts and patches,
and the libfuse 3.15.0 and squashfuse 0.5.2 sources used by that runtime. To rebuild
the runtime, follow `BUILD.md` and `scripts/docker/` in that source archive;
the Dockerfile uses Alpine 3.21 and installs its build dependencies. The GNU LGPL
libraries in the AppDir remain dynamically linked and replaceable after extracting
the image. Repack a modified AppDir using appimagetool with `--runtime-file`.
For Ubuntu libraries, unpack their `.dsc` files with `dpkg-source -x`, install
the package's build dependencies and build with `dpkg-buildpackage` in Ubuntu 24.04.
For app modifications, rebuild from this project's tagged source and Containerfile.

The release contains `SHA256SUMS` for the binary, dependency sources, package manifest
and USB rule. The project itself remains MIT-licensed; dependencies retain their
own licenses. See [third-party notices](../THIRD_PARTY_NOTICES.md).
