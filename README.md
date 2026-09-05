<p align="center">
  <img src="packaging/btd700-control.svg" width="80" alt="BTD 700 Control icon">
</p>

<h1 align="center">BTD 700 Control for Linux</h1>

<p align="center">Your dongle. Your codecs. A native Linux app and system tray menu.</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/platform-Linux-informational" alt="Linux">
  <img src="https://img.shields.io/badge/UI-English%20%2F%20Deutsch-green" alt="English and German interface">
  <a href="https://github.com/justin-eckenweber/btd700linux/actions/workflows/tests.yml"><img src="https://github.com/justin-eckenweber/btd700linux/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
</p>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="https://github.com/justin-eckenweber/btd700linux/archive/refs/tags/v0.2.0.zip">Download source v0.2.0</a> ·
  <a href="README.de.md">Deutsche Anleitung</a> ·
  <a href="https://github.com/justin-eckenweber/btd700linux/issues">Report an issue</a>
</p>

An independent, open-source control app for the **Sennheiser BTD 700** USB Bluetooth
transmitter. Choose audio modes and codecs, manage the headphone connection, and
configure Auracast without Windows or Wine. Built with Python, GTK 4 and libadwaita.

**Controls only. No firmware updates, firmware downloads or update mode.** Once
installed, the app works offline and does not send telemetry.

> **AI-developed · Experimental · No warranty**
>
> This project was developed with AI (OpenAI Codex), including protocol research,
> implementation, documentation and tests. It is an independent community project,
> not official Sennheiser software. **There is no guarantee that it will work with
> your hardware, firmware or Linux setup.** It is provided as is, without warranty,
> under the [MIT license](LICENSE). Use it at your own risk.

## Screenshots

Actual application windows on Linux, using **fictional demo data**. No mockups or
AI-generated images. The app follows your desktop's light/dark appearance.

<p align="center">
  <img src="docs/screenshots/main-window.png" width="46%" alt="English app: active codec, audio mode and headphone connection">
  <img src="docs/screenshots/auracast-settings.png" width="46%" alt="English app: Auracast name, password protection, broadcast quality and startup settings">
</p>

## What you can control

| Feature | Window | System tray |
|---|:---:|:---:|
| Standard, Gaming and Auracast modes | ✓ | ✓ |
| Active codec, audio format and connection status | ✓ | ✓ |
| Codec selection supported by the current connection | ✓ | ✓ |
| Bluetooth Classic, LE Audio or automatic transport | ✓ | ✓ |
| Connect / disconnect previously paired headphones | ✓ | ✓ |
| Auracast discovery, quality and password protection | ✓ | ✓ |
| Auracast name and password | ✓ | Opens the editor |
| Factory reset, with confirmation | ✓ | Opens confirmation |

The tray menu stays available when you close the window. On GNOME, it uses the
same StatusNotifier/AppIndicator mechanism as apps such as Discord and JetBrains
Toolbox. Use **Quit** to close the app completely. Without a tray host, closing the
window quits the app instead.

## Install

Version **0.2.0** is distributed as source. You do not need to compile the app or
install Python packages with pip. There is currently no AppImage, Flatpak or
self-contained binary download.

### 1. Install the system libraries

Requirements: **Python 3.10+**, PyGObject, **GTK 4.10+**, **libadwaita 1.5+** and
libdbusmenu with GObject introspection. A graphical desktop session is needed for
the window and tray; the CLI only needs Python's standard library.

**Ubuntu 24.04+ / Debian with sufficiently recent GTK and libadwaita:**

```bash
sudo apt install git python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-dbusmenu-glib-0.4
```

**Fedora Workstation:**

```bash
sudo dnf install git python3 python3-gobject gtk4 libadwaita libdbusmenu
```

**Bazzite / other immutable desktops:** try running the app first. The tested
Bazzite system already included every required library. The Fedora command above
is for a mutable Fedora installation, not an instruction to layer packages on Bazzite.

On **GNOME**, enable a StatusNotifier/AppIndicator extension if you do not already
have a working tray, for example
[AppIndicator and KStatusNotifierItem Support](https://extensions.gnome.org/extension/615/appindicator-support/).
KDE Plasma provides a tray host. Other desktops may work but have not been tested.

Package references: [Fedora libdbusmenu](https://packages.fedoraproject.org/pkgs/libdbusmenu/libdbusmenu/),
[Ubuntu introspection package](https://packages.ubuntu.com/noble/gir1.2-dbusmenu-glib-0.4).

### 2. Download and run

```bash
git clone https://github.com/justin-eckenweber/btd700linux.git
cd btd700linux
./run.sh
```

Or [download the v0.2.0 source ZIP](https://github.com/justin-eckenweber/btd700linux/archive/refs/tags/v0.2.0.zip),
extract it, and run `bash run.sh` inside the extracted folder.

Want to explore without touching any hardware?

```bash
./run.sh --demo
```

### 3. Add it to your application menu

```bash
python3 install.py
```

Open **BTD 700 Control** from the application menu. Keep the downloaded project
folder in place: the launcher points to it. Enable **Start at login** inside the
app if you want it to start quietly in the tray. Autostart is off by default.

```bash
./run.sh --background       # Start directly in the tray
python3 install.py --uninstall  # Remove launcher and autostart entry
```

### USB permissions

If the app reports that USB access is denied:

```bash
sudo install -m 0644 packaging/70-btd700-control.rules /etc/udev/rules.d/70-btd700-control.rules
sudo udevadm control --reload-rules
```

Unplug and reconnect the dongle afterwards. The rule grants the active local user
access to the **control interface** of USB device `3542:3001`; it excludes the second
interface used for updates. Run the app as your normal user, not with `sudo`.
No audio driver is detached or replaced.

## English and German

The app, tray, CLI help and application error messages follow the system language:
German for German locales, English otherwise. You can override this explicitly:

```bash
./run.sh --language en
./run.sh --language de
BTD700_LANGUAGE=en ./run.sh --background
```

Quit an already running instance before changing the language; launching it again
normally brings the existing window to the front.

## Using the controls

- **Codecs:** the dongle reports the choices available for the current connection.
  Select a codec in Standard mode; Gaming mode manages its own codec. A codec
  supported in principle is not necessarily offered with every pair of headphones.
- **Audio format:** bit depth and sample rate are read from the dongle. Set the USB
  output sample rate in your audio system, such as PipeWire; this app does not
  force 96 kHz or claim bit-perfect or lossless transmission.
- **Pairing:** use the physical dongle button to pair headphones. **Connect** reuses
  an existing pairing.
- **Auracast:** select Auracast mode to start broadcasting. **Publicly discoverable**
  controls advertising/discovery, not whether audio is transmitted.
- **Name and password:** 4–16 ASCII letters/digits; names may contain internal
  spaces. An empty name restores the device's default name. Leave the password
  field blank to keep the current password; turn off Password protection to
  broadcast without it. Passwords are not stored on disk or included in status output.
- **Factory reset:** deletes saved settings and pairings. It always requires
  confirmation in the UI.

## Command line

Quit the tray app before using the CLI: one instance owns the dongle at a time.

```bash
./run.sh devices
./run.sh status
./run.sh mode standard
./run.sh mode gaming
./run.sh mode standard --transport auto
./run.sh codec adaptive
./run.sh disconnect
./run.sh connect
./run.sh auracast --name 'Living Room' --quality high --public on
./run.sh auracast --password --encryption on  # Hidden password prompt
./run.sh mode auracast
```

`status` prints JSON without reading a password. With multiple dongles, place
`--device /dev/hidrawN` before the subcommand; use the path reported by `devices`.
The numeric fields in JSON retain their protocol meanings across languages.

## Compatibility and limitations

Developed and tested on **Bazzite / GNOME with a BTD 700 running firmware 3.11.0**.
The owner confirmed that the app works with their dongle. That is not a complete
compatibility matrix or a guarantee for other firmware and receivers.

- Real hardware: device discovery, state/configuration reads, native window and
  tray integration verified.
- Automated tests: protocol parsing, allowed commands, readback, input validation,
  localization and demo-backed GTK/D-Bus menu interactions.
- Still needed: systematic hardware write tests, more receivers/firmware versions,
  other desktops, and independent testing by more users.
- BTD 600 and other Sennheiser devices are **not supported** by this driver.
- Reconfiguring modes or broadcasts can interrupt audio. Multi-step settings are
  not atomic; unplugging the dongle midway can leave partially applied changes.

[Validation notes](docs/VALIDATION.md) · [Protocol and research sources](docs/PROTOCOL.md)

## Contribute

Bug reports, compatibility reports, translations and reviewed patches are welcome.
See [CONTRIBUTING.md](CONTRIBUTING.md) for what to include and how to run tests.
Please do not attach broadcast passwords, device serial numbers, original vendor
executables or firmware images.

```bash
python3 -m unittest discover -s tests -v
BTD700_LANGUAGE=en python3 tools/check_gui.py  # Desktop session; simulated dongle
BTD700_LANGUAGE=de python3 tools/check_gui.py
python3 tools/capture_screenshots.py          # Regenerate the README screenshots
```

The separate `tools/check_hardware.py --run` is an opt-in hardware test that changes
settings, including the broadcast password, and attempts to restore the originals.
It is never run by CI or the demo tests. Read it before deliberately using it.

## License and independence

The project's own code and documentation are licensed under **[MIT](LICENSE)**.
The AI-development and no-warranty notice above is intentional; please keep it
visible when describing this project.

Sennheiser, BTD 700, aptX and Auracast names identify the compatible product and
technologies. This project is not affiliated with, endorsed by or supported by
Sennheiser, Sonova or Qualcomm. No vendor code, firmware or logos are included.
System libraries and original vendor software retain their own licenses;
see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
