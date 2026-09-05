"""User-scoped desktop integration."""
from pathlib import Path
import os
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
APP_ID = 'io.github.btd700linux.Control'


def desktop_entry(*, background=False):
    appdir = os.environ.get('APPDIR')
    appimage = os.environ.get('APPIMAGE') if appdir else None
    checkout = (ROOT / 'run.sh').is_file()
    path = appimage or (str(Path(appdir) / 'AppRun') if appdir else None) or (str(ROOT / 'run.sh') if checkout else sys.executable)
    module_args = '' if appdir or checkout else ' -m btd700'
    # The pinned type2 runtime removes its CLI flag before launching AppRun;
    # its extraction directory also identifies subsequent launches in this mode.
    if appimage and ('APPIMAGE_EXTRACT_AND_RUN' in os.environ or Path(appdir).name.startswith('appimage_extracted_')):
        module_args = ' --appimage-extract-and-run'
    icon = (str(installed_icon()) if appimage else str(Path(appdir) / 'btd700-control.svg') if appdir
            else str(ROOT / 'packaging/btd700-control.svg') if checkout else 'audio-headphones')
    # Desktop Entry Exec quoting is not shell quoting.
    escaped = path.replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%')
    return ('[Desktop Entry]\nType=Application\nName=BTD 700 Control\n'
            'Comment=Linux controls for the Sennheiser BTD 700\n'
            'Comment[de]=Linux-Steuerung für den Sennheiser BTD 700\n'
            f'Exec="{escaped}"{module_args}' + (' --background' if background else '') + '\n'
            f'Icon={icon}\nTerminal=false\n'
            'Categories=AudioVideo;Audio;\n'
            'Keywords=Sennheiser;Bluetooth;aptX;Auracast;Dongle;\n'
            f'StartupWMClass={APP_ID}\n')


def autostart_path():
    base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    return base / 'autostart' / f'{APP_ID}.desktop'


def installed_icon():
    base = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    return base / 'icons/hicolor/scalable/apps' / f'{APP_ID}.svg'


def install_appimage_icon():
    if os.environ.get('APPIMAGE') and os.environ.get('APPDIR'):
        path = installed_icon()
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(os.environ['APPDIR']) / 'btd700-control.svg', path)


def set_autostart(enabled):
    path = autostart_path()
    if enabled:
        install_appimage_icon()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(desktop_entry(background=True))
    else:
        path.unlink(missing_ok=True)
