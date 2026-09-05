# Changelog

## 0.3.0 — 2026-09-05

- Downloadable x86-64 AppImage for glibc 2.39+ desktops, including Python, GTK,
  libadwaita and the tray library; no Python package installation needed.
- AppImage-aware application-menu installation and autostart using its permanent
  file path, including a persistent icon and support for extracted AppDirs.
- Container build and GitHub release workflow, checksums, bundled license notices
  and corresponding dependency source archives.
- English/German packaged GUI and D-Bus tray verification with simulated hardware.

## 0.2.0 — 2026-09-05

- English and German app, tray, CLI help and error messages, selected by system
  locale or `--language` / `BTD700_LANGUAGE`.
- English README with genuine app screenshots and a separate German guide.
- MIT license, AI-development disclosure and explicit no-warranty statement.
- Public installation, uninstall, contribution and compatibility documentation.
- Automated protocol/localization tests on GitHub; no hardware writes in CI.

## 0.1.0 — 2026-09-05

- Initial GTK 4 / libadwaita control app and StatusNotifier tray menu.
- Audio modes, codec/transport selection, connection and Auracast settings.
- Independent HID control protocol implementation; no firmware updater.
- Real-device status reads and demo-backed UI verification on Bazzite/GNOME.
