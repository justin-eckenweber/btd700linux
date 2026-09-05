"""User-scoped desktop integration."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent.parent
APP_ID = 'io.github.btd700linux.Control'


def desktop_entry(*, background=False):
    checkout = (ROOT / 'run.sh').is_file()
    path = str(ROOT / 'run.sh') if checkout else sys.executable
    module_args = '' if checkout else ' -m btd700'
    icon = str(ROOT / 'packaging/btd700-control.svg') if checkout else 'audio-headphones'
    # Desktop Entry Exec quoting is not shell quoting.
    escaped = path.replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%')
    return ('[Desktop Entry]\nType=Application\nName=BTD 700 Control\n'
            'Comment=Linux-Steuerung für den Sennheiser BTD 700\n'
            f'Exec="{escaped}"{module_args}' + (' --background' if background else '') + '\n'
            f'Icon={icon}\nTerminal=false\n'
            'Categories=AudioVideo;Audio;\n'
            'Keywords=Sennheiser;Bluetooth;aptX;Auracast;Dongle;\n'
            f'StartupWMClass={APP_ID}\n')


def autostart_path():
    base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    return base / 'autostart' / f'{APP_ID}.desktop'


def set_autostart(enabled):
    path = autostart_path()
    if enabled:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(desktop_entry(background=True))
    else:
        path.unlink(missing_ok=True)
