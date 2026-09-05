"""One thread owns the USB handle; the GTK main loop never waits for USB."""
import queue
import threading
from gi.repository import GLib
from .controller import Controller
from .transport import DeviceError, Hidraw, discover


class Worker(threading.Thread):
    def __init__(self, callback, *, device_path=None, demo=False):
        super().__init__(name='btd700-usb', daemon=True)
        self.callback = callback
        self.device_path = device_path
        self.demo = demo
        self.commands = queue.Queue()
        self.stopping = threading.Event()
        self.controller = None
        self.transport = None

    def submit(self, method, args, kwargs):
        self.commands.put((method, args, kwargs))

    def stop(self):
        self.stopping.set()
        self.commands.put(None)

    def run(self):
        try:
            while not self.stopping.is_set():
                try:
                    action = self.commands.get(timeout=2)
                except queue.Empty:
                    action = None
                if self.stopping.is_set():
                    break
                error = ''
                try:
                    if self.controller is None:
                        if self.demo:
                            from .demo import DemoTransport
                            self.transport = DemoTransport()
                        else:
                            devices = discover()
                            if self.device_path:
                                devices = [d for d in devices if d.path == self.device_path]
                            if not devices:
                                raise DeviceError('Kein BTD 700 gefunden. Bitte den Dongle einstecken.')
                            if len(devices) > 1:
                                raise DeviceError('Mehrere BTD 700 gefunden. Mit --device /dev/hidrawN auswählen.')
                            self.transport = Hidraw(devices[0])
                        self.controller = Controller(self.transport)
                    if action:
                        method, args, kwargs = action
                        try:
                            getattr(self.controller, method)(*args, **kwargs)
                        except (ValueError, DeviceError, TimeoutError) as exc:
                            error = str(exc)
                    status = self.controller.snapshot()
                    GLib.idle_add(self.callback, status, error, bool(action))
                except Exception as exc:
                    if self.transport:
                        self.transport.close()
                    self.transport = self.controller = None
                    GLib.idle_add(self.callback, None, error or str(exc), bool(action))
        finally:
            if self.transport:
                self.transport.close()
