# Validierung am 5. September 2026

Getestetes System: Bazzite, GNOME, Python 3.14, GTK 4.22, libadwaita 1.9.
Angeschlossener BTD 700: USB `3542:3001`, Firmware 3.11.0.

- 21 Tests mit `python3 -m unittest discover -s tests -q`: bestanden.
- Fenster-/Infobereich-Test `python3 tools/check_gui.py`: bestanden, ausschließlich
  mit einem simulierten Dongle. Aktionen wurden über `com.canonical.dbusmenu.Event`
  ausgelöst, nicht nur direkt gegen Controller-Methoden.
- Geprüfte Demo-Abläufe: Standard/Gaming/Auracast, Codec, Transport, Trennen/Verbinden,
  öffentliche Auffindbarkeit, Broadcastqualität, Name/Passwort speichern,
  Passwortschutz ausschalten, Fenster schließen/aus Menü wieder öffnen,
  ungespeicherte Eingaben bei Statusabfragen erhalten und verwerfen.
- Eigene Fensterbilder bei 620 × 800 und 420 × 600 Pixeln gerendert und visuell
  geprüft. Oberfläche scrollbar, Bedienelemente erreichbar. Die zuvor überlange
  Passwortbeschriftung wurde gekürzt und um einen sichtbaren Hinweis ergänzt.
- Echte Hardwareabfragen: erfolgreich, siehe PROTOCOL.md. Anzeige:
  Gaming / aptX Adaptive / 24 Bit / 48 kHz / laufende Musikwiedergabe.
- Live-Symbol exportiert StatusNotifierItem mit aktuellem Tooltip und einem
  D-Bus-Menü. GNOME-StatusNotifierWatcher nimmt die Registrierung an.
- App über persönlichen Desktop-Eintrag installierbar; Desktop-Datei validiert.
  Dauerhafter Start in der Benutzersitzung mit transienter Unit
  `btd700-control.service`; kein Systemdienst und kein aktivierter Autostart.
- Zweiter USB-Zugriff während laufender App: korrekt mit verständlicher Meldung
  abgelehnt, ohne die laufende Instanz zu beeinträchtigen.
- Extraktionsskript gegen die offizielle Windows-EXE geprüft; SHA256 der
  extrahierten Assembly entspricht der bei der Analyse verwendeten Datei.

Der Nutzer hat anschließend bestätigt, dass die App am eigenen Dongle funktioniert.
Welche einzelnen Funktionen dabei getestet wurden, wurde nicht näher aufgeschlüsselt.

**Noch offen:** automatisierte Hardware-Schreibtests sowie eine systematische
Prüfung mit Audio-/Auracast-Empfängern. `tools/check_hardware.py --run` wurde bisher
nicht ausgeführt. Dieser Test unterbricht kurz Audio und verändert vorübergehend
Auracast-Einstellungen einschließlich des Passworts; anschließend versucht er,
die ursprünglichen Werte wiederherzustellen. Ein Werksreset wird dabei nicht
ausgeführt; Firmware-Updates sind nicht implementiert.
