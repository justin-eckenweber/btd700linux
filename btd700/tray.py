"""StatusNotifierItem + libdbusmenu, compatible with GNOME AppIndicator and KDE."""
from .i18n import tr
import gi
from gi.repository import Gio, GLib
from .protocol import CODECS, MODES, STATES

gi.require_version('Dbusmenu', '0.4')
from gi.repository import Dbusmenu

INTERFACE = 'org.kde.StatusNotifierItem'
XML = '''<node><interface name="org.kde.StatusNotifierItem">
<property name="Category" type="s" access="read"/>
<property name="Id" type="s" access="read"/>
<property name="Title" type="s" access="read"/>
<property name="Status" type="s" access="read"/>
<property name="WindowId" type="u" access="read"/>
<property name="IconName" type="s" access="read"/>
<property name="IconThemePath" type="s" access="read"/>
<property name="IconPixmap" type="a(iiay)" access="read"/>
<property name="OverlayIconName" type="s" access="read"/>
<property name="OverlayIconPixmap" type="a(iiay)" access="read"/>
<property name="AttentionIconName" type="s" access="read"/>
<property name="AttentionIconPixmap" type="a(iiay)" access="read"/>
<property name="AttentionMovieName" type="s" access="read"/>
<property name="ToolTip" type="(sa(iiay)ss)" access="read"/>
<property name="ItemIsMenu" type="b" access="read"/>
<property name="Menu" type="o" access="read"/>
<method name="Activate"><arg type="i" direction="in"/><arg type="i" direction="in"/></method>
<method name="SecondaryActivate"><arg type="i" direction="in"/><arg type="i" direction="in"/></method>
<method name="ContextMenu"><arg type="i" direction="in"/><arg type="i" direction="in"/></method>
<method name="Scroll"><arg type="i" direction="in"/><arg type="s" direction="in"/></method>
<signal name="NewTitle"/><signal name="NewIcon"/><signal name="NewToolTip"/>
<signal name="NewStatus"><arg type="s"/></signal>
</interface></node>'''


class Tray:
    def __init__(self, app):
        self.app = app
        self.status = None
        self.available = False
        self._signature = None
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.registration = self.bus.register_object('/StatusNotifierItem',
            Gio.DBusNodeInfo.new_for_xml(XML).interfaces[0], self._method, self._property, None)
        self.server = Dbusmenu.Server.new('/Menu')
        self.watch = Gio.bus_watch_name_on_connection(self.bus, 'org.kde.StatusNotifierWatcher',
            Gio.BusNameWatcherFlags.NONE, self._watcher_appeared, self._watcher_lost)
        self.update(None, False)

    def _watcher_appeared(self, connection, _name, _owner):
        def done(bus, result):
            try:
                bus.call_finish(result)
                self.available = True
            except GLib.Error:
                self.available = False
            self.app.tray_changed()
        connection.call('org.kde.StatusNotifierWatcher', '/StatusNotifierWatcher',
                        'org.kde.StatusNotifierWatcher', 'RegisterStatusNotifierItem',
                        GLib.Variant('(s)', (connection.get_unique_name(),)), None,
                        Gio.DBusCallFlags.NONE, 3000, None, done)

    def _watcher_lost(self, *_):
        self.available = False
        self.app.tray_changed()

    def _property(self, _bus, _sender, _path, _iface, name):
        tooltip = tr('BTD 700 anschließen')
        if self.status:
            tooltip = f'{MODES.get(self.status.mode, "—")} · {self.status.codec_name} · {self.status.quality}'
        props = {
            'Category': ('s', 'Hardware'), 'Id': ('s', 'btd700-control-demo' if self.app.demo else 'btd700-control'),
            'Title': ('s', 'BTD 700 Control · DEMO' if self.app.demo else 'BTD 700 Control'), 'Status': ('s', 'Active'),
            'WindowId': ('u', 0), 'IconName': ('s', 'audio-headphones-symbolic'),
            'IconThemePath': ('s', ''), 'IconPixmap': ('a(iiay)', []),
            'OverlayIconName': ('s', ''), 'OverlayIconPixmap': ('a(iiay)', []),
            'AttentionIconName': ('s', ''), 'AttentionIconPixmap': ('a(iiay)', []),
            'AttentionMovieName': ('s', ''),
            'ToolTip': ('(sa(iiay)ss)', ('audio-headphones-symbolic', [], 'BTD 700', tooltip)),
            'ItemIsMenu': ('b', True), 'Menu': ('o', '/Menu')}
        if name in props:
            return GLib.Variant(*props[name])
        return None

    def _method(self, _bus, _sender, _path, _iface, method, _params, invocation):
        if method in ('Activate', 'SecondaryActivate', 'ContextMenu'):
            self.app.show_window()
        invocation.return_value(None)

    @staticmethod
    def _item(label, action=None, *, enabled=True, checked=None, radio=False):
        item = Dbusmenu.Menuitem.new()
        item.property_set('label', label)
        item.property_set_bool('visible', True)
        item.property_set_bool('enabled', enabled)
        if checked is not None:
            item.property_set('toggle-type', 'radio' if radio else 'checkmark')
            item.property_set_int('toggle-state', int(checked))
        if action:
            item.connect('item-activated', lambda *_: action())
        return item

    def _submenu(self, root, label):
        item = self._item(label)
        item.property_set('children-display', 'submenu')
        root.child_append(item)
        return item

    def update(self, status, busy, error=''):
        signature = (repr(status), busy, error)
        if signature == self._signature:
            return
        self._signature = signature
        self.status = status
        root = Dbusmenu.Menuitem.new()
        add = root.child_append
        add(self._item('BTD 700 Control · DEMO' if self.app.demo else 'BTD 700 Control', self.app.show_window))
        if status:
            add(self._item(f'{status.codec_name} · {status.quality}', enabled=False))
            add(self._item(tr(STATES.get(status.state, 'Unbekannter Status')), enabled=False))
            modes = self._submenu(root, tr('Audiomodus'))
            for value, label in MODES.items():
                modes.child_append(self._item(label,
                    lambda v=value: self.app.perform('set_mode', v),
                    enabled=not busy and (value != 1 or status.gaming_allowed),
                    checked=status.mode == value, radio=True))
            codecs = self._submenu(root, 'Codec')
            for value, label in CODECS.items():
                if status.codecs & value:
                    codecs.child_append(self._item(label,
                        lambda v=value: self.app.perform('set_codec', v),
                        enabled=not busy and status.mode == 0 and status.state >= 2,
                        checked=bool(status.codec & value), radio=True))
            if not codecs.get_children():
                codecs.child_append(self._item(tr('Keine verbundenen Kopfhörer'), enabled=False))
            transports = self._submenu(root, tr('Bluetooth-Transport'))
            for value, label in ((3, tr('Automatisch')), (1, 'Bluetooth Classic'), (2, 'LE Audio')):
                transports.child_append(self._item(label,
                    lambda v=value: self.app.perform('set_mode', status.mode, transport=v),
                    enabled=not busy and status.mode == 0 and (value == 3 or bool(status.transports & value)),
                    checked=status.transport == value, radio=True))
            auracast = self._submenu(root, 'Auracast')
            auracast.child_append(self._item(tr('Name und Passwort …'), lambda: self.app.show_window('auracast')))
            auracast.child_append(self._item(tr('Öffentlich auffindbar'),
                lambda: self.app.perform('set_broadcast', public=not status.broadcast_public),
                enabled=not busy, checked=bool(status.broadcast_public)))
            auracast.child_append(self._item(tr('Passwortschutz'),
                lambda: self.app.toggle_encryption(), enabled=not busy,
                checked=bool(status.broadcast_encrypted)))
            quality = self._submenu(auracast, tr('Übertragungsqualität'))
            for value, label in enumerate((tr('Standard · 16 kHz'), tr('Standard · 24 kHz'), tr('Hohe Qualität'))):
                quality.child_append(self._item(label,
                    lambda v=value: self.app.perform('set_broadcast', quality=v),
                    enabled=not busy, checked=status.broadcast_quality == value, radio=True))
            add(self._item(tr('Kopfhörer trennen') if status.state >= 2 else tr('Kopfhörer verbinden'),
                lambda: self.app.perform('set_connection', status.state < 2), enabled=not busy and status.mode != 2))
            add(self._item(tr('Werkseinstellungen …'), self.app.confirm_reset, enabled=not busy))
        else:
            add(self._item(tr('Dongle nicht verbunden') if not error else tr('USB-Zugriff prüfen – Fenster öffnen'),
                           self.app.show_window))
        if busy:
            add(self._item(tr('Einstellung wird übernommen …'), enabled=False))
        if error:
            add(self._item(tr('Fehler anzeigen …'), self.app.show_window))
        separator = Dbusmenu.Menuitem.new()
        separator.property_set('type', 'separator')
        add(separator)
        add(self._item(tr('Fenster öffnen'), self.app.show_window))
        add(self._item(tr('Beenden'), self.app.quit))
        self.root = root  # Keep Python signal closures alive.
        self.server.set_root(root)
        self.bus.emit_signal(None, '/StatusNotifierItem', INTERFACE, 'NewToolTip', None)

    def close(self):
        Gio.bus_unwatch_name(self.watch)
        self.bus.unregister_object(self.registration)
