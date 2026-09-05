# Validation — 5 September 2026

This document separates observed hardware behavior from simulated tests.
The project was developed using AI (OpenAI Codex); these results are not a warranty.

## Environment

Bazzite / GNOME, Python 3.14, GTK 4.22, libadwaita 1.9.
Connected BTD 700: USB `3542:3001`, firmware 3.11.0.

## Observed on the real device

- Correct control-interface discovery and opening without detaching audio drivers.
- Successful state, mode, codec, quality, transport, Auracast configuration/name
  and firmware-version reads. See [PROTOCOL.md](PROTOCOL.md) for response bytes.
- Reported live state: Gaming, aptX Adaptive, 24-bit / 48 kHz, audio playing.
- Native GTK window and registered GNOME tray item with a live status tooltip.
- A second USB client is rejected with a clear message while the app owns the device.
- The device owner subsequently confirmed that the app works. The individual
  functions exercised by the owner were not enumerated.

## Automated verification

- Protocol/controller/transport tests: command allowlist, malformed frames, response
  correlation, event acknowledgements, readback, capability checks, input validation,
  reset confirmation and password handling using a simulated device.
- Localization tests: English/German detection, explicit CLI override, message
  placeholders, localized status/errors and unchanged numeric protocol data.
- Desktop integration tests: isolated installation/uninstallation and autostart
  behavior without changing the real user's launchers.
- `tools/check_gui.py` exercised English and German windows and actual D-Bus menu
  events against a demo device: modes, codec, transport, connection, broadcast
  discovery/quality, name/password saving, encryption, closing/reopening and
  preserving/discarding unsaved edits.
- Window layouts rendered and inspected at 620 × 800 and 420 × 600 pixels.
- README screenshots captured from the real English GTK window at 620 × 880 with
  fictional demo data. No real USB access or generated mockups were used.
- Extraction helper output matched the SHA256 of the original assembly used for
  protocol research. No vendor binaries were added to the distribution.

The CI workflow runs the unit tests on Python 3.10 and 3.14, in both languages.
It does not run real hardware tests or claim that a particular receiver works.

## Not yet systematically verified

- Hardware writes across different firmware revisions and all individual commands.
- Real Auracast receiver compatibility, audio quality and reconnect behavior.
- Other distributions/desktops beyond the tested Bazzite/GNOME setup.

`tools/check_hardware.py --run` has not been executed. It deliberately interrupts
audio, changes settings including the broadcast password, and attempts to restore
the original values. It does not perform a factory reset and cannot perform
firmware updates. Unplugging midway can prevent restoration.
