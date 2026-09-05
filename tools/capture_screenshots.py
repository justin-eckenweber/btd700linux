#!/usr/bin/env python3
"""Capture the actual GTK application with fictional demo data, without USB access."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from btd700.app import Application
from gi.repository import GLib, Gtk

output = Path(__file__).resolve().parents[1] / 'docs/screenshots'
output.mkdir(parents=True, exist_ok=True)
app = Application(demo=True, language='en')
phase = 0
attempts = 0
success = False


def capture(name):
    window = app.window
    snapshot = Gtk.Snapshot.new()
    Gtk.WidgetPaintable.new(window).snapshot(snapshot, window.get_width(), window.get_height())
    node = snapshot.to_node()
    if node is None:
        return False
    texture = window.get_renderer().render_texture(node, None)
    if not texture.save_to_png(str(output / name)):
        raise RuntimeError('Could not save screenshot')
    print(f'{name}: {window.get_width()} × {window.get_height()}', flush=True)
    return True


def tick():
    global phase, attempts, success
    attempts += 1
    try:
        if attempts > 40:
            raise TimeoutError('Screenshot window did not become ready')
        if not app.status or app.busy:
            return True
        if phase == 0:
            app.window.set_default_size(620, 880)
            phase = 1
        elif phase == 1:
            if capture('main-window.png'):
                adjustment = app.scroll.get_vadjustment()
                adjustment.set_value(adjustment.get_upper() - adjustment.get_page_size())
                phase = 2
        elif phase == 2:
            if capture('auracast-settings.png'):
                success = True
                app.quit()
                return False
    except Exception as exc:
        print(f'Capture failed: {exc}', file=sys.stderr)
        app.quit()
        return False
    return True

GLib.timeout_add(500, tick)
app.run(['btd700-screenshots'])
raise SystemExit(0 if success else 1)
