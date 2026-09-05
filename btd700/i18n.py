"""Small, dependency-free English/German catalog shared by GUI, tray and CLI."""
import os


def detect_language(environ=None):
    env = os.environ if environ is None else environ
    override = env.get('BTD700_LANGUAGE', '')
    if override in ('en', 'de'):
        return override
    language = (env.get('LANGUAGE') or env.get('LC_ALL') or env.get('LC_MESSAGES') or env.get('LANG') or 'en')
    return 'de' if language.split(':', 1)[0].lower().startswith('de') else 'en'


_language = detect_language()


def set_language(language):
    global _language
    if language not in ('en', 'de'):
        raise ValueError('Supported languages: en, de')
    _language = language


def get_language():
    return _language


def tr(message):
    return ENGLISH.get(message, message) if _language == 'en' else message


# German source messages are retained for compatibility with the first release.
# Keep placeholders identical in both languages; never translate protocol values.
ENGLISH = {
    'Menüeintrag und Autostart entfernt. Die Programmdateien bleiben erhalten.':
        'Removed the launcher and start-at-login entry. The application files are unchanged.',
    'Im Anwendungsmenü „BTD 700 Control“ öffnen. Die AppImage-Datei muss an diesem Ort bleiben.':
        'Open BTD 700 Control from the application menu. Keep the AppImage file at this location.',
    'Menüeintrag und Autostart entfernt. Der Projektordner bleibt erhalten.': 'Removed the launcher and start-at-login entry. The project folder is unchanged.',
    'Status aktualisieren': 'Refresh status',
    'App vollständig beenden': 'Quit application',
    'BTD 700 verbinden': 'Connect your BTD 700',
    'Suche nach deinem USB-Dongle …': 'Looking for your USB dongle…',
    'Audiomodus': 'Audio mode',
    'Der Modus wird direkt am Dongle umgeschaltet.': 'Switch the audio mode directly on your dongle.',
    'Kopfhörer': 'Headphones',
    'Bluetooth-Transport': 'Bluetooth transport',
    'Verbindung': 'Connection',
    'Verbinden': 'Connect',
    'Trennen': 'Disconnect',
    'Der Audiomodus „Auracast“ startet die Übertragung an mehrere Empfänger.': 'Choose Auracast mode to broadcast audio to multiple receivers.',
    'Name der Übertragung': 'Broadcast name',
    'Öffentlich auffindbar': 'Publicly discoverable',
    'Übertragung in der Auracast-Suche anzeigen': 'Show this broadcast in Auracast discovery',
    'Passwortschutz': 'Password protection',
    'Neues Passwort': 'New password',
    '4–16 Buchstaben oder Ziffern. Leer lassen behält das bisherige Passwort.': '4–16 letters or digits. Leave blank to keep the current password.',
    'Übertragungsqualität': 'Broadcast quality',
    'Standard · 16 kHz': 'Standard · 16 kHz',
    'Standard · 24 kHz': 'Standard · 24 kHz',
    'Hohe Qualität': 'High quality',
    'Verwerfen': 'Discard',
    'Speichern': 'Save',
    'Passwort leer lassen, um das bisherige zu behalten.': 'Leave the password blank to keep the current one.',
    'Im Infobereich weiterlaufen': 'Keep running in the system tray',
    'Infobereich wird verbunden …': 'Connecting to the system tray…',
    'Beim Anmelden starten': 'Start at login',
    'Startet unauffällig im Infobereich': 'Start quietly in the system tray',
    'Unabhängige Steuerungs-App · Keine Firmware-Updates': 'Independent control app · No firmware updates',
    'Dongle auf Werkseinstellungen zurücksetzen …': 'Reset dongle to factory settings…',
    'Beim Schließen bleibt das Symbol in der oberen Leiste.': 'Closing the window keeps the tray icon available.',
    'Kein Infobereich verfügbar; Schließen beendet die App.': 'No system tray available; closing the window quits the app.',
    'Vom Dongle bestätigt': 'Confirmed by the dongle',
    'Einstellung wird übernommen …': 'Applying setting…',
    'Auswahl im Standard-Modus': 'Available in Standard mode',
    'Vom Dongle angebotene Codecs': 'Codecs reported by the dongle',
    'Automatisch': 'Automatic',
    'Nicht verbunden': 'Disconnected',
    'Bereit': 'Ready',
    'Kopfhörer getrennt': 'Headphones disconnected',
    'Kopfhörer verbunden': 'Headphones connected',
    'Musikwiedergabe': 'Playing audio',
    'Sprachanruf': 'Voice call',
    'Unbekannt': 'Unknown',
    'Unbekannter Status': 'Unknown status',
    'Warte auf den USB-Dongle …': 'Waiting for the USB dongle…',
    'BTD 700 zurücksetzen?': 'Reset BTD 700?',
    'Alle Kopplungen und gespeicherten Einstellungen werden gelöscht. Danach musst du die Kopfhörer erneut koppeln.': 'This removes all pairings and saved settings. You will need to pair your headphones again.',
    'Abbrechen': 'Cancel',
    'Zurücksetzen': 'Reset',
    'Infobereich nicht verfügbar: {error}': 'System tray unavailable: {error}',
    'Autostart konnte nicht gespeichert werden: {error}': 'Could not save the start-at-login setting: {error}',
    'Firmware {version} · Unabhängige App · Keine Firmware-Updates': 'Firmware {version} · Independent app · No firmware updates',
    'BTD 700 anschließen': 'Connect a BTD 700',
    'Keine verbundenen Kopfhörer': 'No headphones connected',
    'Name und Passwort …': 'Name and password…',
    'Kopfhörer trennen': 'Disconnect headphones',
    'Kopfhörer verbinden': 'Connect headphones',
    'Werkseinstellungen …': 'Factory reset…',
    'Dongle nicht verbunden': 'Dongle disconnected',
    'USB-Zugriff prüfen – Fenster öffnen': 'Check USB access — open window',
    'Fehler anzeigen …': 'Show error…',
    'Fenster öffnen': 'Open window',
    'Beenden': 'Quit',
    '16 Bit': '16-bit',
    '24 Bit': '24-bit',
    '44,1 kHz': '44.1 kHz',
    'Unbekannt ({value})': 'Unknown ({value})',
    'Der Dongle hat die angeforderte Einstellung nicht bestätigt. Bitte den aktuellen Status prüfen.': 'The dongle did not confirm the requested setting. Please check its current status.',
    'Unbekannter Audiomodus.': 'Unknown audio mode.',
    'Gaming ist für die aktuelle Verbindung nicht verfügbar.': 'Gaming mode is unavailable for this connection.',
    'Unbekannter Bluetooth-Transport.': 'Unknown Bluetooth transport.',
    'Die Kopfhörer unterstützen diesen Transport nicht.': 'Your headphones do not support this transport.',
    'Codec-Auswahl benötigt verbundene Kopfhörer im Standard-Modus.': 'Codec selection requires connected headphones in Standard mode.',
    'Dieser Codec wird für die aktuelle Verbindung nicht angeboten.': 'This codec is not offered for the current connection.',
    'Verbindung wurde angefordert, aber noch nicht bestätigt. Sind die gekoppelten Kopfhörer eingeschaltet?': 'Connection requested but not yet confirmed. Are your paired headphones switched on?',
    'Auracast-Schalter benötigen einen booleschen Wert.': 'Auracast switches require a boolean value.',
    'Unbekannte Auracast-Qualität.': 'Unknown Auracast quality.',
    'Verschlüsselung benötigt ein Passwort mit 4–16 Zeichen.': 'Encryption requires a password of 4–16 characters.',
    'Bitte zuerst ein Passwort mit 4–16 Zeichen eingeben.': 'Enter a password of 4–16 characters first.',
    'Auracast wurde nur teilweise oder nicht übernommen. Aktuellen Namen und Passwortschutz prüfen.': 'Auracast settings were only partially applied or not applied. Check the current name and password protection.',
    'Zurücksetzen muss ausdrücklich bestätigt werden; alle Kopplungen werden gelöscht.': 'Reset requires explicit confirmation; all pairings will be removed.',
    'Passwort: 4–16 Buchstaben oder Ziffern.': 'Password: 4–16 letters or digits.',
    'Name: 4–16 Buchstaben, Ziffern oder innere Leerzeichen.': 'Name: 4–16 letters, digits or internal spaces.',
    'Unbekannter Steuerbefehl; kein Zugriff auf Update-Befehle.': 'Unknown control command; update commands are not accessible.',
    'Ungültige Antwort des Dongles.': 'Invalid response from the dongle.',
    'Ungültige Parameter für {command}.': 'Invalid parameters for {command}.',
    'Unbekannte Benachrichtigung: {event:#x}': 'Unknown notification: {event:#x}',
    'Gerätepfad gehört nicht mehr zum BTD 700.': 'The device path no longer belongs to a BTD 700.',
    'Der Dongle ist bereits in einer anderen Instanz geöffnet.': 'Another instance already has this dongle open.',
    'USB-Zugriff fehlt. Die mitgelieferte udev-Regel installieren und den Dongle neu einstecken.': 'USB access denied. Install the included udev rule and reconnect the dongle.',
    'Dongle ist nicht geöffnet.': 'The dongle is not open.',
    'USB-Schreibzugriff hat nicht geantwortet.': 'USB write timed out.',
    'Unvollständiger USB-Schreibvorgang.': 'Incomplete USB write.',
    'Dongle wurde entfernt.': 'The dongle was unplugged.',
    'Unvollständige Antwort auf {command}.': 'Incomplete response to {command}.',
    'Der Dongle antwortet nicht auf {command}.': 'The dongle did not respond to {command}.',
    'Kein BTD 700 gefunden. Bitte den Dongle einstecken.': 'No BTD 700 found. Please connect the dongle.',
    'Mehrere BTD 700 gefunden. Mit --device /dev/hidrawN auswählen.': 'Multiple BTD 700 dongles found. Select one with --device /dev/hidrawN.',
    'Nicht unterstützte Demo-Abfrage': 'Unsupported demo query',
    'Native Linux-Steuerung für den BTD 700; ohne Firmware-Updates.': 'Native Linux controls for the BTD 700; no firmware updates.',
    'Steuergerät aus dem Befehl devices, z. B. /dev/hidraw6': 'Control device listed by devices, e.g. /dev/hidraw6',
    'Nur im Infobereich starten': 'Start in the system tray only',
    'Vorführmodus ohne USB-Zugriff': 'Demo mode without USB access',
    'BTD-700-Steuerschnittstellen auflisten': 'List BTD 700 control interfaces',
    'Aktuellen Status als JSON ausgeben (ohne Passwort)': 'Print current status as JSON (without passwords)',
    'Audiomodus wählen': 'Select an audio mode',
    'Codec im Standard-Modus wählen': 'Select a codec in Standard mode',
    'Gekoppelte Kopfhörer verbinden': 'Connect paired headphones',
    'Auracast-Einstellungen speichern': 'Save Auracast settings',
    'Neues Passwort verdeckt abfragen': 'Prompt for a new password without echoing it',
    'Alle Kopplungen und Einstellungen löschen': 'Remove all pairings and settings',
    'Kein eindeutiger BTD 700 gefunden. devices ausführen; bei mehreren Dongles --device angeben.': 'No unique BTD 700 found. Run devices; use --device if multiple dongles are connected.',
    'GTK-Oberfläche nicht verfügbar: {error}\nAbhängigkeiten: siehe README.md. CLI: ./run.sh status': 'GTK interface unavailable: {error}\nDependencies: see README.md. CLI: ./run.sh status',
    'Neues Auracast-Passwort: ': 'New Auracast password: ',
    'Zurücksetzen angefordert. Kopfhörer danach neu koppeln.': 'Reset requested. Pair your headphones again afterwards.',
    'Fehler: {error}': 'Error: {error}',
    'Installiert: {path}': 'Installed: {path}',
    'Im Anwendungsmenü „BTD 700 Control“ öffnen. Der Projektordner muss erhalten bleiben.': 'Open “BTD 700 Control” from your application menu. Keep the project folder in place.',
    'Sprache der App (Standard: Systemsprache)': 'App language (default: system language)',
}
