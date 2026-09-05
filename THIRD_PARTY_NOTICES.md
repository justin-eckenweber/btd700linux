# Third-party notices

The MIT license in this repository covers this project's own implementation,
documentation and artwork. It does not relicense third-party software or trademarks.

- Python, PyGObject, GTK, libadwaita and libdbusmenu are provided by your system,
  not bundled here. Their respective licenses continue to apply.
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
