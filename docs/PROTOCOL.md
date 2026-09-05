# Reconstructed BTD 700 control protocol

Investigation date: 5 September 2026. Purpose: independently control a user's
USB dongle on Linux. The official Windows application was examined statically;
it was not executed. Research and implementation were carried out with AI
(OpenAI Codex). This is a working protocol reconstruction, not a vendor specification.

## Provenance and reproducibility

- [Official product page](https://uk.sennheiser-hearing.com/products/btd-700)
- [Official Dongle Control download page](https://uk.sennheiser-hearing.com/pages/sennheiser-dongle-control)
- [Windows ZIP linked from that page](https://eu-central-1-akqa.graphassets.com/AGz66yvUcQ42Ggm7CrXdgz/cmgrvi8excrci07uu3ivz166x)
- Archive entry: `windows-signed-v1.0.5/Sennheiser Dongle Control.exe`, version 1.0.5.0,
  ProductVersion `1.0.5+eac62d73c43c8572999e7e68cbaec6e4536a1318`.
- ZIP SHA256: `1d1057b7eb64ab08e41d76723c343c691196f0affe1d5fc9168f01f9908a8cc7`
- EXE SHA256: `e176f1ab7d4aae40308c152b0bd95227ac5a16fedb99efef7e9229345d8014c0`
- Embedded application assembly SHA256:
  `2e8c89ea0333b0a9dd5bb0e851cd685810edaa6e32caee7645511d646ee970b4`

The executable is a .NET single-file bundle, manifest version 6, with 451 entries.
`tools/extract_control_assembly.py` can extract only the application assembly from
a locally supplied original EXE. Its format was checked against the .NET runtime's
[Manifest](https://github.com/dotnet/runtime/blob/main/src/installer/managed/Microsoft.NET.HostModel/Bundle/Manifest.cs)
and [FileEntry](https://github.com/dotnet/runtime/blob/main/src/installer/managed/Microsoft.NET.HostModel/Bundle/FileEntry.cs)
definitions.

Analysis tool: ILSpy CLI 11.0.0.9375. Relevant original types:
`BTDTool.BTD700Tool`, `_BTD700_HOSTCMD`, `_BTD700_DONGLECMD`, the `_BTD700_*` enums,
`BTD700Context`, `HidDeviceExt.sendGenericCommand`,
`ViewModels.MainAppWindowViewModel` and `Views.AppBtd700Features`.

This repository contains protocol facts and an independent implementation.
Original executables, decompiled original sources and vendor resources are not
included. The original software retains its own license. Extracted assemblies
are not required to run this app and should not be added to the repository.

## USB interface and framing

VID `0x3542`, PID `0x3001`, USB HID interface 0. The control collection uses vendor
usage page `0xFFA2` and report ID **0x34**. It appeared as `/dev/hidraw6` on the test
system; the application discovers the path dynamically from its descriptor.
Interface 1 is not opened by this control app.

Output reports are 64 bytes, with unused bytes padded with zero:

| Byte | Meaning |
|---|---|
| 0 | Report ID `34` |
| 1 | `FE`: host command; `FF`: dongle response; `FC`: dongle event; `FD`: event acknowledgement |
| 2 | Command or event number |
| 3 | Payload length, at most 60 |
| 4… | Payload |

Example query: `34 FE 06 00` followed by 60 zero bytes.
Example reply: `34 FF 06 01 03` (audio is playing).
Acknowledgement for event 15: `34 FD 0F 00` followed by 60 zero bytes.

Events 2/3/4/15/16/17/22/23 are acknowledged. Other report IDs can carry media keys
on the same interface and are ignored. Replies are matched by direction and
command number, with length validation. Only one request is outstanding at a time.
Setters are not blindly retried; settings are queried again for confirmation.
There is no transaction ID or guarantee of atomic multi-setting updates.

## Commands

IDs below are hexadecimal. GET requests have an empty payload. The payload column
means the response for GET operations and the request for SET operations.

| ID | Operation | Payload |
|---|---|---|
| 01 | GET mode/transport | Mode, configured transport, optional connected transport |
| 02 | SET mode/transport | Mode, transport |
| 03 | GET available codecs | Codec bitmask |
| 04 | SET codec | One codec bit, not its bit index |
| 05 | GET active codec | Codec bitmask |
| 06 | GET dongle state | State |
| 07 | GET LE Audio state | LE state |
| 08 | GET audio quality | Resolution, frequency |
| 09 | GET Auracast configuration | Public discovery, quality, encryption |
| 0A | SET Auracast configuration | Public discovery, quality, encryption |
| 0B | GET Auracast key | Character bytes; only read by explicit password operations |
| 0C | SET Auracast key | 0–16 bytes; UI accepts empty or 4–16 ASCII characters |
| 0D | GET Auracast name | Character bytes; 32 bytes with zero padding on the tested device |
| 0E | SET Auracast name | Up to 16 character bytes; empty restores the device default |
| 12 | GET firmware version | Three version bytes, display only |
| 13 | Factory reset | Empty; requires user confirmation |
| 14 | Bluetooth connect/disconnect | 1 / 0 |
| 15 | GET supported headphone transports | Bitmask |
| 17 | GET Gaming availability | Defined by the original app; firmware 3.11 did not reply, so not polled |

Mode: 0 Standard, 1 Gaming, 2 Auracast.
Transport: 0 disconnected, 1 BR/EDR, 2 LE Audio, 3 dual/automatic. The app does not
set transport 0; disconnection has a separate command.

Codec bits: `01` SBC, `02` aptX Classic, `04` aptX Adaptive/Low Latency,
`08` aptX Lossless, `10` aptX Lite/QMAP, `20` LC3. Only offered bits appear as
choices. Firmware can change the available list depending on the current mode.

Dongle state: 0 none/ready, 1 disconnected, 2 connected, 3 audio, 4 voice.
LE state: 0 none, 1 disconnected, 2 connected, 3 unicast, 4 broadcast.
Resolution: 1 = 16-bit, 2 = 24-bit.
Frequency: 1 = 44.1 kHz, 2 = 48 kHz, 3 = 96 kHz.
Auracast: public discovery 0/1; quality 0 = SQ 16 kHz, 1 = SQ 24 kHz, 2 = HQ;
encryption 0/1. Public discovery advertises the broadcast; it does not select
the audio mode or start/stop audio by itself.

Gaming availability falls back to the current connection, aptX Adaptive bit and
LE transport, following the original app, unless event 23 has supplied a value.
Display strings may be translated; command IDs and numeric values never are.

## Observed hardware responses: firmware 3.11.0

| Query | Response without padding | Interpretation |
|---|---|---|
| 06 | `34 FF 06 01 03` | Audio playing |
| 01 | `34 FF 01 03 01 03 01` | Gaming, automatic, connected using Classic |
| 03 | `34 FF 03 01 04` | aptX Adaptive currently offered |
| 05 | `34 FF 05 01 04` | aptX Adaptive active |
| 07 | `34 FF 07 01 01` | LE disconnected |
| 08 | `34 FF 08 02 02 02` | 24-bit / 48 kHz |
| 09 | `34 FF 09 03 01 02 00` | Public discovery, HQ, no encryption configured |
| 12 | `34 FF 12 03 03 0B 00` | Firmware 3.11.0 |
| 15 | `34 FF 15 01 01` | Headphones support Classic |

The broadcast name was also read successfully. Private device identifiers and keys
are omitted. The reported audio configuration does not prove bit-perfect playback.

## Update exclusion and remaining limitations

Only control report `0x34` is implemented. The runtime has no DFU/upgrade commands,
firmware files, firmware parser, firmware-download endpoints or update-mode switch.
Firmware version is read using control command `0x12` solely for display.

The device owner reported that the app works. The automated hardware mutation test
has not been run, and that feedback is not a complete verification of every setter.
Reconnection, real Auracast receivers and differing firmware require more systematic
testing. The original app and simulator are not substitutes for device validation.

## Desktop tray

`org.kde.StatusNotifierItem` with `com.canonical.dbusmenu`, exported using libdbusmenu,
following the [StatusNotifier specification](https://specifications.freedesktop.org/status-notifier-item/latest-single/).
Registration with GNOME and menu actions over D-Bus were tested locally in English
and German. Name/password actions focus the GTK editor because the menu protocol
does not provide text-entry fields.
