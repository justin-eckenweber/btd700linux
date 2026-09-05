#!/usr/bin/env python3
"""Install a launcher for this checkout, without root or system packages."""
from pathlib import Path
import os
from btd700.integration import APP_ID, desktop_entry

base = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
applications = base / 'applications'
applications.mkdir(parents=True, exist_ok=True)
destination = applications / f'{APP_ID}.desktop'
destination.write_text(desktop_entry())
print(f'Installiert: {destination}')
print('Im Anwendungsmenü „BTD 700 Control“ öffnen. Der Projektordner muss erhalten bleiben.')
