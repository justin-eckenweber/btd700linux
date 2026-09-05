# Contributing

This is an experimental, AI-developed project. Independent review and real-world
compatibility reports are particularly useful. English and German contributions
are welcome.

## Report a problem

Open a [GitHub issue](https://github.com/justin-eckenweber/btd700linux/issues) with:

- Distribution, desktop environment and application version/commit.
- BTD 700 firmware version and headphone model/firmware, if known.
- The steps you took, what you expected, and what actually happened.
- Whether the issue also occurs in `./run.sh --demo`.
- Relevant terminal output after removing private information.

Do not post broadcast passwords, Bluetooth/device identifiers, original vendor
executables or firmware images. `devices` includes a serial number: redact it.
The regular `status` output excludes passwords, but its broadcast name can still
contain personal information. Never say a hardware write is tested if it was
only simulated.

## Make a change

1. Fork the repository and create a focused branch.
2. Keep firmware download, update and bootloader functionality out of scope.
3. Preserve the control-report allowlist and validate input before writing to USB.
4. Keep blocking USB operations off the GTK main loop.
5. Add a meaningful regression test for protocol or behavior changes.
6. Run the checks below and explain what was tested in your pull request.

```bash
BTD700_LANGUAGE=en python3 -m unittest discover -s tests -v
BTD700_LANGUAGE=de python3 -m unittest discover -s tests -v

# Optional, with GTK libraries and a working desktop tray:
BTD700_LANGUAGE=en python3 tools/check_gui.py
BTD700_LANGUAGE=de python3 tools/check_gui.py
```

The GUI test uses a simulated device and D-Bus menu events, not the real USB dongle.
Hardware tests must be deliberate: the optional `tools/check_hardware.py --run`
changes settings and can interrupt audio. Do not add it to unattended CI.

## Translations and screenshots

`btd700/i18n.py` contains the English/German catalog. German source strings are
retained from the first version. Use `tr()` for user-facing messages; preserve
format placeholders and keep numeric protocol values independent of translation.
The CLI accepts `--language en|de`; `BTD700_LANGUAGE` also controls test runs.

Regenerate genuine English screenshots with `python3 tools/capture_screenshots.py`.
The helper uses demo data and writes to `docs/screenshots/`. Inspect the resulting
images before committing them. Do not substitute generated mockups for screenshots.

## Licensing and AI disclosure

Contributions are accepted under this project's MIT license. Do not submit code
or assets you are not permitted to share. Explain any AI-generated portions of
substantial contributions and review them before submission. The project's
AI-development and no-warranty notices remain part of its public documentation.
