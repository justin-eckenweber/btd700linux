# Rekonstruiertes BTD-700-Steuerprotokoll

Stand der Untersuchung: 5. September 2026. Zweck: unabhängige Linux-Steuerung des
eigenen USB-Dongles. Die Windows-Anwendung wurde statisch untersucht, nicht ausgeführt.

## Herkunft und Reproduzierbarkeit

- [Offizielle Produktseite](https://uk.sennheiser-hearing.com/products/btd-700)
- [Offizieller Dongle-Control-Download](https://uk.sennheiser-hearing.com/pages/sennheiser-dongle-control)
- [Dort verlinktes Windows-ZIP](https://eu-central-1-akqa.graphassets.com/AGz66yvUcQ42Ggm7CrXdgz/cmgrvi8excrci07uu3ivz166x)
- Archiv: `windows-signed-v1.0.5/Sennheiser Dongle Control.exe`, Version 1.0.5.0,
  ProductVersion `1.0.5+eac62d73c43c8572999e7e68cbaec6e4536a1318`.
- SHA256 ZIP: `1d1057b7eb64ab08e41d76723c343c691196f0affe1d5fc9168f01f9908a8cc7`
- SHA256 EXE: `e176f1ab7d4aae40308c152b0bd95227ac5a16fedb99efef7e9229345d8014c0`
- SHA256 eingebettete App-Assembly:
  `2e8c89ea0333b0a9dd5bb0e851cd685810edaa6e32caee7645511d646ee970b4`

Die EXE ist ein .NET-Single-File-Bundle, Manifestversion 6 mit 451 Einträgen.
Die benötigte Assembly kann mit `tools/extract_control_assembly.py` aus einer
lokalen Original-EXE extrahiert werden. Das Bundleformat wurde mit den
[Manifest](https://github.com/dotnet/runtime/blob/main/src/installer/managed/Microsoft.NET.HostModel/Bundle/Manifest.cs)-
und [FileEntry](https://github.com/dotnet/runtime/blob/main/src/installer/managed/Microsoft.NET.HostModel/Bundle/FileEntry.cs)-
Definitionen des .NET-Runtimes abgeglichen.

Analysewerkzeug: ILSpy CLI 11.0.0.9375. Relevante Typen:
`BTDTool.BTD700Tool`, `_BTD700_HOSTCMD`, `_BTD700_DONGLECMD`, `_BTD700_*`-Enums,
`BTD700Context`, `HidDeviceExt.sendGenericCommand`,
`ViewModels.MainAppWindowViewModel`, `Views.AppBtd700Features`.

Die neue Implementierung enthält nur rekonstruierte Protokollfakten und eigenen
Code. Original-Binaries, dekompilierte Originalquellen und Ressourcen gehören
nicht zum Projekt. Die Herstellerlizenz der Originalsoftware bleibt davon getrennt.

## USB und Framing

VID `0x3542`, PID `0x3001`, USB-HID-Interface 0. Die Steuersammlung verwendet
Vendor Usage Page `0xFFA2`, Report ID **0x34**. Auf dem Testsystem liegt sie unter
`/dev/hidraw6`; die Nummer wird dynamisch ermittelt. Interface 1 ist für diese
Steuer-App nicht erforderlich und wird nicht geöffnet.

64-Byte-Output-Report, ungenutzte Bytes mit Null gefüllt:

| Byte | Bedeutung |
|---|---|
| 0 | Report-ID `34` |
| 1 | `FE` Host-Befehl; `FF` Dongle-Antwort; `FC` Dongle-Ereignis; `FD` Ereignisbestätigung |
| 2 | Befehls- oder Ereignisnummer |
| 3 | Nutzdatenlänge, maximal 60 |
| 4… | Nutzdaten |

Host-Abfrage Beispiel: `34 FE 06 00` + 60 Nullbytes.
Antwort Beispiel: `34 FF 06 01 03` (Audio läuft).
Bestätigung des Ereignisses 15: `34 FD 0F 00` + 60 Nullbytes.

Ereignisse 2/3/4/15/16/17/22/23 werden bestätigt. Andere Reports können von
Medientasten auf derselben Schnittstelle stammen und werden ignoriert. Antworten
werden nach Richtung und Befehlsnummer zugeordnet; Längen werden geprüft.
Nur eine Anfrage ist gleichzeitig aktiv. Schreibbefehle werden nicht blind
wiederholt; für Einstellungen wird anschließend der Wert erneut abgefragt.
Es gibt keine Transaktions-ID und keine garantierte Atomizität mehrerer Einstellungen.

## Befehle

Alle Nummern hexadezimal. Bei Lesezugriffen ist die Anfrage-Nutzlast leer.
Die nachfolgende Nutzlast beschreibt bei `GET` die Antwort, bei `SET` die Anfrage.

| ID | Operation | Nutzlast |
|---|---|---|
| 01 | GET Modus/Transport | Modus, konfigurierter Transport, optional aktuell verbundener Transport |
| 02 | SET Modus/Transport | Modus, Transport |
| 03 | GET verfügbare Codecs | Codec-Bitmaske |
| 04 | SET Codec | Einzelnes Codec-Bit, nicht Bitindex |
| 05 | GET aktiver Codec | Codec-Bitmaske |
| 06 | GET Dongle-Zustand | Zustand |
| 07 | GET LE-Audio-Zustand | LE-Zustand |
| 08 | GET Audioqualität | Auflösung, Frequenz |
| 09 | GET Auracast-Konfiguration | öffentlich, Qualität, Verschlüsselung |
| 0A | SET Auracast-Konfiguration | öffentlich, Qualität, Verschlüsselung |
| 0B | GET Auracast-Schlüssel | Zeichenbytes; nur bei expliziter Passwort-Operation gelesen |
| 0C | SET Auracast-Schlüssel | 0–16 Bytes; UI beschränkt auf leer oder 4–16 ASCII-Zeichen |
| 0D | GET Auracast-Name | Zeichenbytes; am Gerät 32 Bytes, mit Null aufgefüllt |
| 0E | SET Auracast-Name | bis 16 Zeichenbytes; leer setzt Gerätenamen zurück |
| 12 | GET Firmwareversion | drei Versionsbytes, nur Anzeige |
| 13 | Werksreset | leer; nur nach Nutzerbestätigung |
| 14 | Bluetooth verbinden/trennen | 1 / 0 |
| 15 | GET Kopfhörer-Transportmöglichkeiten | Bitmaske |
| 17 | GET Gaming-Verfügbarkeit | im Original definiert; Firmware 3.11 antwortet nicht, daher nicht regelmäßig abgefragt |

Modus: 0 Standard, 1 Gaming, 2 Auracast.
Transport: 0 getrennt, 1 BR/EDR, 2 LE Audio, 3 Dual/automatisch. Setzen von 0 wird
in der neuen App nicht angeboten; Trennen hat einen eigenen Befehl.

Codec-Bits: `01` SBC, `02` aptX Classic, `04` aptX Adaptive/Low Latency,
`08` aptX Lossless, `10` aptX Lite/QMAP, `20` LC3. Nur die vom Dongle angebotenen
Bits werden im Menü angezeigt. Die Firmware kann die Liste abhängig vom Modus ändern.

Dongle-Zustand: 0 keiner/bereit, 1 getrennt, 2 verbunden, 3 Audio, 4 Sprache.
LE-Zustand: 0 keiner, 1 getrennt, 2 verbunden, 3 Unicast, 4 Broadcast.
Auflösung: 1 = 16 Bit, 2 = 24 Bit.
Frequenz: 1 = 44,1 kHz, 2 = 48 kHz, 3 = 96 kHz.
Auracast: öffentlich 0/1; Qualität 0 = SQ 16 kHz, 1 = SQ 24 kHz, 2 = HQ;
Verschlüsselung 0/1. „Öffentlich“ bezeichnet die Ankündigung/Auffindbarkeit,
nicht das Aktivieren des Audiomodus.

Gaming-Verfügbarkeit fällt wie in der Original-App auf den Verbindungsstatus,
aptX-Adaptive-Bit und LE-Transport zurück, solange kein Ereignis 23 eingetroffen ist.

## Tatsächlich gelesene Antworten (Firmware 3.11.0)

| Anfrage | Antwort ohne Null-Padding | Interpretation |
|---|---|---|
| 06 | `34 FF 06 01 03` | Audio läuft |
| 01 | `34 FF 01 03 01 03 01` | Gaming, automatisch, verbunden per Classic |
| 03 | `34 FF 03 01 04` | aktuell aptX Adaptive angeboten |
| 05 | `34 FF 05 01 04` | aptX Adaptive aktiv |
| 07 | `34 FF 07 01 01` | LE getrennt |
| 08 | `34 FF 08 02 02 02` | 24 Bit / 48 kHz |
| 09 | `34 FF 09 03 01 02 00` | öffentlich, HQ, unverschlüsselt konfiguriert |
| 12 | `34 FF 12 03 03 0B 00` | Firmware 3.11.0 |
| 15 | `34 FF 15 01 01` | Kopfhörer unterstützt Classic |

Auch der Auracast-Name wurde erfolgreich gelesen. Private Kennungen/Schlüssel
werden hier nicht dokumentiert. Die verfügbare Audiokonfiguration belegt nicht,
dass Audio mit diesem Profil bitgenau übertragen wird.

## Getrennte Update-Funktion und Grenzen

Die App implementiert ausschließlich Report `0x34` auf der Kontrollschnittstelle.
Sie enthält keine DFU-/Upgrade-Kommandos, Firmwaredateien, Firmwareparser,
Firmware-Download-URLs oder Umschaltung in einen Update-Modus.
Die Firmwareversion wird nur über den Kontrollbefehl `0x12` gelesen.

Der Nutzer hat die Funktion der App am eigenen Dongle bestätigt. Der automatisierte
Hardware-Umschalttest wurde noch nicht ausgeführt; die Rückmeldung belegt keine
vollständige Prüfung jedes Schreibbefehls. Insbesondere Wiederverbindung, echte
Auracast-Empfänger und Firmwareunterschiede benötigen weitere systematische Tests.

Infobereich: `org.kde.StatusNotifierItem` plus `com.canonical.dbusmenu` über
libdbusmenu. Grundlage ist die
[StatusNotifier-Spezifikation](https://specifications.freedesktop.org/status-notifier-item/latest-single/).
GNOME-Registrierung und D-Bus-Menüaktionen wurden lokal geprüft. Name/Passwort
verwenden fokussierte GTK-Eingaben, da D-Bus-Menüs keine Texteingabefelder vorsehen.
