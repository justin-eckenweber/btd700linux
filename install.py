#!/usr/bin/env python3
"""Install/remove a launcher for this checkout, without root or system packages."""
import argparse
import os
from pathlib import Path
from btd700.i18n import tr
from btd700.integration import APP_ID, autostart_path, desktop_entry, install_appimage_icon, installed_icon


def main():
    parser = argparse.ArgumentParser(description='Add or remove the BTD 700 Control application-menu entry.')
    parser.add_argument('--uninstall', action='store_true', help='Remove the launcher and start-at-login entry')
    args = parser.parse_args()
    base = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    destination = base / 'applications' / f'{APP_ID}.desktop'
    if args.uninstall:
        destination.unlink(missing_ok=True)
        autostart_path().unlink(missing_ok=True)
        installed_icon().unlink(missing_ok=True)
        print(tr('Menüeintrag und Autostart entfernt. Die Programmdateien bleiben erhalten.'))
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    install_appimage_icon()
    destination.write_text(desktop_entry())
    print(tr('Installiert: {path}').format(path=destination))
    if os.environ.get('APPIMAGE') and os.environ.get('APPDIR'):
        print(tr('Im Anwendungsmenü „BTD 700 Control“ öffnen. Die AppImage-Datei muss an diesem Ort bleiben.'))
    else:
        print(tr('Im Anwendungsmenü „BTD 700 Control“ öffnen. Der Projektordner muss erhalten bleiben.'))


if __name__ == '__main__':
    main()
