"""Native GTK 4 / libadwaita controls and a persistent notification-area menu."""
import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gio, GLib, Gtk
from .integration import APP_ID, autostart_path, set_autostart
from .protocol import CODECS, MODES, STATES
from .worker import Worker


class Application(Adw.Application):
    def __init__(self, *, background=False, demo=False, device=None, smoke_seconds=0):
        super().__init__(application_id=APP_ID + ('.Demo' if demo else ''), flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.background = background
        self.demo = demo
        self.device = device
        self.smoke_seconds = smoke_seconds
        self.status = None
        self.window = None
        self.tray = None
        self.worker = None
        self.busy = False
        self.updating = False
        self.dirty = False
        self.form_submitted = False
        self.last_error = ''
        self.codec_values = []
        self.transport_values = []
        self.received_status = False
        self.smoke_ok = False

    def do_startup(self):
        Adw.Application.do_startup(self)
        self.hold()
        self._build_window()
        try:
            from .tray import Tray
            self.tray = Tray(self)
        except (ImportError, ValueError, GLib.Error) as exc:
            self.last_error = f'Infobereich nicht verfügbar: {exc}'
        self.worker = Worker(self._on_status, demo=self.demo, device_path=self.device)
        self.worker.start()
        self.worker.commands.put(None)
        if self.smoke_seconds:
            GLib.timeout_add_seconds(self.smoke_seconds, self._finish_smoke)

    def do_activate(self):
        if not self.background or not self.window:
            self.show_window()
        self.background = False  # A second launch opens the existing window.
        GLib.timeout_add_seconds(4, self._ensure_accessible)

    def do_shutdown(self):
        if self.worker:
            self.worker.stop()
            self.worker.join(timeout=12)
        if self.tray:
            self.tray.close()
        Adw.Application.do_shutdown(self)

    def _ensure_accessible(self):
        if not self.tray or not self.tray.available:
            self.show_window()
        return False

    def _finish_smoke(self):
        self.smoke_ok = self.received_status and bool(self.tray and self.tray.available)
        print(f'GUI_SMOKE status={self.received_status} tray={bool(self.tray and self.tray.available)}', flush=True)
        self.quit()
        return False

    def _build_window(self):
        self.window = Adw.ApplicationWindow(application=self, title='BTD 700 Control',
                                           default_width=620, default_height=800)
        self.window.set_size_request(420, 420)
        self.window.connect('close-request', self._close_window)
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title='BTD 700', subtitle='Linux Control' + (' · DEMO' if self.demo else '')))
        refresh = Gtk.Button(icon_name='view-refresh-symbolic', tooltip_text='Status aktualisieren')
        refresh.connect('clicked', lambda *_: self.worker.commands.put(None))
        header.pack_start(refresh)
        self.refresh_button = refresh
        quit_button = Gtk.Button(icon_name='application-exit-symbolic', tooltip_text='App vollständig beenden')
        quit_button.connect('clicked', lambda *_: self.quit())
        header.pack_end(quit_button)
        toolbar.add_top_bar(header)
        self.toast = Adw.ToastOverlay()
        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        clamp = Adw.Clamp(maximum_size=600, tightening_threshold=500)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=22,
                          margin_top=24, margin_bottom=28, margin_start=20, margin_end=20)
        clamp.set_child(content)
        scroll.set_child(clamp)
        self.toast.set_child(scroll)
        toolbar.set_content(self.toast)
        self.window.set_content(toolbar)
        self.scroll = scroll

        heading = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        icon = Gtk.Image(icon_name='audio-headphones-symbolic', pixel_size=48)
        heading.append(icon)
        self.codec_label = Gtk.Label(label='BTD 700 verbinden')
        self.codec_label.add_css_class('title-1')
        heading.append(self.codec_label)
        self.state_label = Gtk.Label(label='Suche nach deinem USB-Dongle …', wrap=True)
        self.state_label.add_css_class('dim-label')
        heading.append(self.state_label)
        self.quality_label = Gtk.Label(label='')
        self.quality_label.add_css_class('caption')
        heading.append(self.quality_label)
        content.append(heading)

        self.error_label = Gtk.Label(wrap=True, xalign=0)
        self.error_label.add_css_class('error')
        self.error_label.set_visible(False)
        content.append(self.error_label)
        self.device_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=22, sensitive=False)
        content.append(self.device_box)

        mode_group = Adw.PreferencesGroup(title='Audiomodus', description='Der Modus wird direkt am Dongle umgeschaltet.')
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0, homogeneous=True)
        mode_box.add_css_class('linked')
        self.mode_buttons = []
        for mode, label in MODES.items():
            button = Gtk.ToggleButton(label=label)
            if self.mode_buttons:
                button.set_group(self.mode_buttons[0])
            button.connect('clicked', lambda b, v=mode: self._mode_clicked(b, v))
            mode_box.append(button)
            self.mode_buttons.append(button)
        mode_group.add(mode_box)
        self.device_box.append(mode_group)

        audio = Adw.PreferencesGroup(title='Kopfhörer')
        self.codec_row = Adw.ComboRow(title='Codec')
        self.codec_row.connect('notify::selected', self._codec_selected)
        audio.add(self.codec_row)
        self.transport_row = Adw.ComboRow(title='Bluetooth-Transport')
        self.transport_row.connect('notify::selected', self._transport_selected)
        audio.add(self.transport_row)
        self.connection_row = Adw.ActionRow(title='Verbindung')
        self.connection_button = Gtk.Button(label='Verbinden', valign=Gtk.Align.CENTER)
        self.connection_button.connect('clicked', lambda *_: self.perform('set_connection', self.status.state < 2) if self.status else None)
        self.connection_row.add_suffix(self.connection_button)
        audio.add(self.connection_row)
        self.device_box.append(audio)

        self.auracast_group = Adw.PreferencesGroup(title='Auracast',
            description='Der Audiomodus „Auracast“ startet die Übertragung an mehrere Empfänger.')
        self.name_entry = Adw.EntryRow(title='Name der Übertragung')
        self.name_entry.connect('changed', self._form_changed)
        self.auracast_group.add(self.name_entry)
        self.public_row = Adw.SwitchRow(title='Öffentlich auffindbar',
            subtitle='Übertragung in der Auracast-Suche anzeigen')
        self.public_row.connect('notify::active', self._form_changed)
        self.auracast_group.add(self.public_row)
        self.encryption_row = Adw.SwitchRow(title='Passwortschutz')
        self.encryption_row.connect('notify::active', self._form_changed)
        self.auracast_group.add(self.encryption_row)
        self.password_entry = Adw.PasswordEntryRow(title='Neues Passwort')
        self.password_entry.set_tooltip_text('4–16 Buchstaben oder Ziffern. Leer lassen behält das bisherige Passwort.')
        self.password_entry.connect('changed', self._password_changed)
        self.auracast_group.add(self.password_entry)
        self.broadcast_quality = Adw.ComboRow(title='Übertragungsqualität',
            model=Gtk.StringList.new(['Standard · 16 kHz', 'Standard · 24 kHz', 'Hohe Qualität']))
        self.broadcast_quality.connect('notify::selected', self._form_changed)
        self.auracast_group.add(self.broadcast_quality)
        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, halign=Gtk.Align.END, margin_top=12)
        self.discard_button = Gtk.Button(label='Verwerfen', sensitive=False)
        self.discard_button.connect('clicked', self._discard)
        self.save_button = Gtk.Button(label='Speichern', sensitive=False)
        self.save_button.add_css_class('suggested-action')
        self.save_button.connect('clicked', self._save_broadcast)
        actions.append(self.discard_button)
        actions.append(self.save_button)
        self.auracast_group.add(actions)
        hint = Gtk.Label(label='Passwort leer lassen, um das bisherige zu behalten.',
                         wrap=True, xalign=0, margin_top=8)
        hint.add_css_class('caption')
        hint.add_css_class('dim-label')
        self.auracast_group.add(hint)
        self.device_box.append(self.auracast_group)

        integration = Adw.PreferencesGroup(title='App')
        self.tray_row = Adw.ActionRow(title='Im Infobereich weiterlaufen', subtitle='Infobereich wird verbunden …')
        integration.add(self.tray_row)
        autostart = Adw.SwitchRow(title='Beim Anmelden starten', subtitle='Startet unauffällig im Infobereich',
                                 active=autostart_path().exists())
        autostart.set_sensitive(not self.demo)
        autostart.connect('notify::active', self._autostart_changed)
        integration.add(autostart)
        content.append(integration)
        self.firmware_label = Gtk.Label(label='Unabhängige Steuerungs-App · Keine Firmware-Updates', wrap=True)
        self.firmware_label.add_css_class('caption')
        self.firmware_label.add_css_class('dim-label')
        content.append(self.firmware_label)
        reset = Gtk.Button(label='Dongle auf Werkseinstellungen zurücksetzen …', halign=Gtk.Align.CENTER)
        reset.add_css_class('flat')
        reset.connect('clicked', lambda *_: self.confirm_reset())
        self.reset_button = reset
        content.append(reset)

    def show_window(self, section=None):
        self.window.present()
        if section == 'auracast':
            self.name_entry.grab_focus()
        elif section == 'password':
            self.password_entry.grab_focus()

    def _close_window(self, *_):
        if self.tray and self.tray.available:
            self.window.set_focus(None)
            self.window.set_visible(False)
        else:
            self.quit()
        return True

    def tray_changed(self):
        available = bool(self.tray and self.tray.available)
        self.tray_row.set_subtitle('Beim Schließen bleibt das Symbol in der oberen Leiste.' if available else
                                  'Kein Infobereich verfügbar; Schließen beendet die App.')

    def perform(self, method, *args, **kwargs):
        if self.busy or not self.status:
            return
        self.refresh_button.grab_focus()
        self.busy = True
        self.last_error = ''
        self.worker.submit(method, args, kwargs)
        self._render()

    def _on_status(self, status, error, completed):
        self.status = status
        self.received_status |= status is not None
        if completed:
            self.busy = False
            self.last_error = error
            if self.form_submitted:
                if not error:
                    self.dirty = False
                    self.updating = True
                    self.password_entry.set_text('')
                    self.updating = False
                self.form_submitted = False
            self.toast.add_toast(Adw.Toast.new(error or 'Vom Dongle bestätigt'))
        elif not status:
            self.last_error = error
        elif self.last_error.startswith(('Kein BTD 700', 'USB-Zugriff fehlt', '[Errno')):
            self.last_error = ''
        self._render()
        return False

    def _render(self):
        self.updating = True
        s = self.status
        self.device_box.set_sensitive(s is not None and not self.busy)
        self.reset_button.set_sensitive(s is not None and not self.busy)
        self.error_label.set_label(self.last_error)
        self.error_label.set_visible(bool(self.last_error))
        if s:
            self.codec_label.set_label('Auracast' if s.mode == 2 else s.codec_name)
            self.state_label.set_label('Einstellung wird übernommen …' if self.busy else STATES.get(s.state, f'Status {s.state}'))
            self.quality_label.set_label(s.quality)
            for mode, button in enumerate(self.mode_buttons):
                button.set_active(mode == s.mode)
                button.set_sensitive(mode != 1 or s.gaming_allowed)
            values = [v for v in CODECS if v & s.codecs]
            if values != self.codec_values:
                self.codec_values = values
                self.codec_row.set_model(Gtk.StringList.new([CODECS[v] for v in values]))
            self.codec_row.set_selected(next((i for i, v in enumerate(values) if v & s.codec), Gtk.INVALID_LIST_POSITION))
            self.codec_row.set_sensitive(s.mode == 0 and s.state >= 2 and len(values) > 1)
            self.codec_row.set_subtitle('Auswahl im Standard-Modus' if s.mode != 0 else 'Vom Dongle angebotene Codecs')
            values = [3] + [v for v in (1, 2) if s.transports & v]
            if s.transport in (1, 2) and s.transport not in values:
                values.append(s.transport)
            if values != self.transport_values:
                self.transport_values = values
                names = {3: 'Automatisch', 1: 'Bluetooth Classic', 2: 'LE Audio'}
                self.transport_row.set_model(Gtk.StringList.new([names[v] for v in values]))
            self.transport_row.set_selected(values.index(s.transport) if s.transport in values else Gtk.INVALID_LIST_POSITION)
            self.transport_row.set_sensitive(s.mode == 0)
            self.connection_row.set_subtitle(STATES.get(s.state, 'Unbekannt'))
            self.connection_button.set_label('Trennen' if s.state >= 2 else 'Verbinden')
            self.connection_button.set_sensitive(s.mode != 2)
            if not self.dirty:
                self.name_entry.set_text(s.broadcast_name)
                self.public_row.set_active(bool(s.broadcast_public))
                self.encryption_row.set_active(bool(s.broadcast_encrypted))
                self.broadcast_quality.set_selected(s.broadcast_quality)
            self.firmware_label.set_label(f'Firmware {s.firmware} · Unabhängige App · Keine Firmware-Updates')
        else:
            self.codec_label.set_label('BTD 700 verbinden')
            self.state_label.set_label('Warte auf den USB-Dongle …')
            self.quality_label.set_label('')
        self.save_button.set_sensitive(self.dirty and not self.busy)
        self.discard_button.set_sensitive(self.dirty and not self.busy)
        self.updating = False
        if self.tray:
            self.tray.update(s, self.busy, self.last_error)

    def _mode_clicked(self, button, mode):
        if not self.updating and button.get_active() and self.status and mode != self.status.mode:
            self.perform('set_mode', mode)

    def _codec_selected(self, row, _):
        i = row.get_selected()
        if not self.updating and i < len(self.codec_values):
            self.perform('set_codec', self.codec_values[i])

    def _transport_selected(self, row, _):
        i = row.get_selected()
        if not self.updating and self.status and i < len(self.transport_values):
            self.perform('set_mode', self.status.mode, transport=self.transport_values[i])

    def _form_changed(self, *_):
        if not self.updating:
            self.dirty = True
            self.save_button.set_sensitive(not self.busy)
            self.discard_button.set_sensitive(not self.busy)

    def _password_changed(self, *_):
        if not self.updating and self.password_entry.get_text():
            self.encryption_row.set_active(True)
        self._form_changed()

    def _discard(self, *_):
        self.dirty = False
        self.updating = True
        self.password_entry.set_text('')
        self.updating = False
        self._render()

    def _save_broadcast(self, *_):
        if not self.status:
            return
        name = self.name_entry.get_text()
        self.form_submitted = True
        self.perform('set_broadcast',
            name=name if name != self.status.broadcast_name else None,
            password=self.password_entry.get_text() or None,
            public=self.public_row.get_active(), quality=self.broadcast_quality.get_selected(),
            encrypted=self.encryption_row.get_active())

    def toggle_encryption(self):
        if self.status and self.status.broadcast_encrypted:
            self.perform('set_broadcast', encrypted=False)
        else:
            self.show_window('password')
            self.encryption_row.set_active(True)

    def confirm_reset(self):
        self.show_window()
        if not self.status or self.busy:
            return
        dialog = Adw.AlertDialog(heading='BTD 700 zurücksetzen?',
            body='Alle Kopplungen und gespeicherten Einstellungen werden gelöscht. Danach musst du die Kopfhörer erneut koppeln.')
        dialog.add_response('cancel', 'Abbrechen')
        dialog.add_response('reset', 'Zurücksetzen')
        dialog.set_response_appearance('reset', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response('cancel')
        dialog.set_close_response('cancel')
        dialog.connect('response', lambda _, response: self.perform('factory_reset', confirmed=True) if response == 'reset' else None)
        dialog.present(self.window)

    def _autostart_changed(self, row, _):
        try:
            set_autostart(row.get_active())
        except OSError as exc:
            self.last_error = f'Autostart konnte nicht gespeichert werden: {exc}'
            self._render()


def run(**kwargs):
    app = Application(**kwargs)
    result = app.run([sys.argv[0]])
    if kwargs.get('smoke_seconds') and not app.smoke_ok:
        return 1
    return result
