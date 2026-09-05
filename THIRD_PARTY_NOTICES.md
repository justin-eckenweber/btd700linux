# Third-party notices

The MIT license in this repository covers this project's own implementation,
documentation and artwork. It does not relicense third-party software or trademarks.

- When running from source, Python, PyGObject, GTK, libadwaita and libdbusmenu are
  provided by your system. The AppImage bundles these libraries and their runtime
  dependencies from Ubuntu 24.04. Their respective licenses continue to apply.
- AppImage license/copyright texts and the package manifest are included under
  `usr/share/doc/btd700-bundled/`; shared license texts are under
  `usr/share/common-licenses/`. Extract with `--appimage-extract` to inspect them.
  Exact corresponding Ubuntu source archives, package versions and build
  instructions are downloadable beside each AppImage as
  `*-dependency-sources.tar.gz`. These dependencies are not relicensed under MIT.
- The AppImage type2 runtime is MIT-licensed and statically includes musl (MIT),
  libfuse (LGPL 2.1), squashfuse (BSD), zstd (BSD) and zlib (zlib license).
  Runtime notices are included in the image; runtime sources, build scripts,
  libfuse sources/patches and squashfuse sources accompany the dependency archive.
  See [AppImage build documentation](docs/APPIMAGE.md) for replacing libraries and
  rebuilding the runtime or app.
- The control protocol was reconstructed by examining the official Windows
  Sennheiser Dongle Control 1.0.5 application. The vendor application, decompiled
  sources, firmware and vendor graphics are not included. Provenance and references
  are recorded in [docs/PROTOCOL.md](docs/PROTOCOL.md).
- The optional extraction helper reads the documented .NET bundle format. Its
  references are linked in the protocol documentation. Extracted assemblies are
  private analysis material, not part of this distribution.
- Sennheiser, Sonova, Qualcomm, BTD 700, aptX and Auracast names are used to describe
  compatibility and functionality. Their use does not imply endorsement.
- The app icon is original project artwork. README screenshots capture this app
  with demo data, using system-provided GTK/libadwaita styling and icons.

The project was developed using AI (OpenAI Codex). The source and tests are available
for review; passing tests does not guarantee operation with any particular device.
