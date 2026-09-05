"""Minimal StatusNotifier watcher for GUI tests on a private CI session bus."""
from gi.repository import Gio, GLib


def start_host():
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    result = bus.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus',
                          'org.freedesktop.DBus', 'RequestName',
                          GLib.Variant('(su)', ('org.kde.StatusNotifierWatcher', 4)),
                          GLib.VariantType.new('(u)'), Gio.DBusCallFlags.NONE, 2000, None)
    if result.unpack()[0] != 1:
        raise RuntimeError('Test watcher refuses to replace an existing tray host')
    xml = '<node><interface name="org.kde.StatusNotifierWatcher"><method name="RegisterStatusNotifierItem"><arg type="s" direction="in"/></method></interface></node>'
    def register(_bus, _sender, _path, _interface, _method, _params, invocation):
        invocation.return_value(None)
    registration = bus.register_object('/StatusNotifierWatcher', Gio.DBusNodeInfo.new_for_xml(xml).interfaces[0], register, None, None)
    return bus, registration


if __name__ == '__main__':
    host = start_host()
    print('TEST_TRAY_READY', flush=True)
    GLib.MainLoop().run()
