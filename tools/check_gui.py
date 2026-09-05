#!/usr/bin/env python3
"""Exercise the GTK UI and real D-Bus menu against an isolated demo device."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from btd700.app import Application
from btd700.i18n import tr
from gi.repository import Gio, GLib, Gtk

app = Application(demo=True)
step = 0
wait_ticks = 0
passed = False
bus_pending = False


def menu_item(labels):
    root = app.tray.root
    for label in labels:
        root = next(item for item in root.get_children() if item.property_get('label') == tr(label))
    return root


def click_menu(*labels):
    global bus_pending
    item = menu_item(labels)
    assert item.property_get_bool('enabled'), labels
    bus_pending = True
    def complete(bus, result):
        global bus_pending
        try:
            bus.call_finish(result)
        except Exception:
            app.quit()
            raise
        bus_pending = False
    app.tray.bus.call(app.tray.bus.get_unique_name(), '/Menu', 'com.canonical.dbusmenu', 'Event',
        GLib.Variant('(isvu)', (item.get_id(), 'clicked', GLib.Variant('i', 0), 0)),
        None, Gio.DBusCallFlags.NONE, 2000, None, complete)


def screenshot(path):
    window = app.window
    paintable = Gtk.WidgetPaintable.new(window)
    snapshot = Gtk.Snapshot.new()
    paintable.snapshot(snapshot, window.get_width(), window.get_height())
    node = snapshot.to_node()
    if node is None:
        raise RuntimeError('Window snapshot is not ready')
    texture = window.get_renderer().render_texture(node, None)
    texture.save_to_png(path)


def tick():
    global step, passed, wait_ticks
    try:
        wait_ticks += 1
        if wait_ticks > 200:
            raise TimeoutError(f'GUI step {step} timed out')
        if not app.status or not app.tray or not app.tray.available or app.busy or bus_pending:
            return True
        assert not app.last_error, app.last_error
        if step == 0:
            assert app.status.mode == 0
            click_menu('Audiomodus', 'Gaming')
        elif step == 1:
            assert app.status.mode == 1
            assert not menu_item(('Codec', 'SBC')).property_get_bool('enabled')
            click_menu('Audiomodus', 'Standard')
        elif step == 2:
            assert app.status.mode == 0
            click_menu('Codec', 'SBC')
        elif step == 3:
            assert app.status.codec == 1
            click_menu('Bluetooth-Transport', 'Bluetooth Classic')
        elif step == 4:
            assert app.status.transport == 1
            click_menu('Kopfhörer trennen')
        elif step == 5:
            assert app.status.state == 1
            click_menu('Kopfhörer verbinden')
        elif step == 6:
            assert app.status.state == 2
            click_menu('Audiomodus', 'Auracast')
        elif step == 7:
            assert app.status.mode == 2
            click_menu('Auracast', 'Öffentlich auffindbar')
        elif step == 8:
            assert app.status.broadcast_public == 0
            click_menu('Auracast', 'Übertragungsqualität', 'Standard · 24 kHz')
        elif step == 9:
            assert app.status.broadcast_quality == 1
            click_menu('Auracast', 'Name und Passwort …')
        elif step == 10:
            assert app.window.get_visible()
            app.name_entry.set_text('Studio Linux')
            app.password_entry.set_text('DemoSecret123')
            app.save_button.emit('clicked')
        elif step == 11:
            assert app.status.broadcast_name == 'Studio Linux'
            assert app.status.broadcast_encrypted == 1
            assert not app.password_entry.get_text()
            assert not app.dirty
            click_menu('Auracast', 'Passwortschutz')
        elif step == 12:
            assert app.status.broadcast_encrypted == 0
            app.window.close()
            assert not app.window.get_visible()
            assert app.tray.available
            click_menu('Fenster öffnen')
        elif step == 13:
            assert app.window.get_visible()
            app.name_entry.set_text('Unsaved edit')
            app._on_status(app.status, '', False)
            assert app.name_entry.get_text() == 'Unsaved edit'
            app.discard_button.emit('clicked')
            assert app.name_entry.get_text() == 'Studio Linux'
            app.mode_buttons[0].emit('clicked') if app.mode_buttons[0].get_active() else app.mode_buttons[0].set_active(True)
            app.perform('set_mode', 0)
        elif step == 14:
            screenshot('/tmp/btd700-gui-test.png')
            adjustment = app.scroll.get_vadjustment()
            adjustment.set_value(adjustment.get_upper() - adjustment.get_page_size())
        elif step == 15:
            screenshot('/tmp/btd700-gui-test-bottom.png')
            app.window.set_default_size(420, 600)
        elif step == 16:
            screenshot('/tmp/btd700-gui-test-narrow.png')
            print('PASS: GTK form, all D-Bus tray control groups, encryption, close/reopen, dirty edits, screenshots', flush=True)
            passed = True
            app.quit()
            return False
        print('GUI step', step, 'passed', flush=True)
        step += 1
        wait_ticks = 0
    except Exception as exc:
        print('FAIL: GUI step', step, type(exc).__name__, str(exc), flush=True)
        app.quit()
        return False
    return True

GLib.timeout_add(250, tick)
app.run(['btd700-gui-test'])
raise SystemExit(0 if passed else 1)
