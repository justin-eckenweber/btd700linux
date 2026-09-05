import unittest
from btd700.controller import Controller
from btd700.demo import DemoTransport
from btd700.protocol import Command as C
from btd700.transport import DeviceError


class RecordingDevice(DemoTransport):
    def __init__(self):
        super().__init__()
        self.writes = []

    def request(self, command, payload=b''):
        if not command.name.startswith('GET_'):
            self.writes.append((command, payload))
        return super().request(command, payload)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.device = RecordingDevice()
        self.controller = Controller(self.device)

    def test_snapshot_does_not_read_password(self):
        self.device.values.pop(C.GET_KEY)
        status = self.controller.snapshot()
        self.assertEqual(status.codec_name, 'aptX Adaptive')
        self.assertEqual(status.quality, '24 Bit / 48 kHz')
        self.assertEqual(status.firmware, '3.11.0')
        self.assertEqual(self.device.writes, [])
        self.assertNotIn('password', status.public_dict())

    def test_mode_preserves_auto_transport(self):
        self.controller.set_mode(1)
        self.assertEqual(self.device.writes, [(C.SET_MODE, b'\1\3')])
        self.assertEqual(self.controller.snapshot().mode, 1)

    def test_codec_capabilities_and_mode(self):
        self.controller.set_codec(2)
        self.assertEqual(self.controller.snapshot().codec, 2)
        with self.assertRaises(ValueError):
            self.controller.set_codec(32)
        self.controller.set_mode(1)
        with self.assertRaises(ValueError):
            self.controller.set_codec(4)

    def test_validation_happens_before_writes(self):
        with self.assertRaises(ValueError):
            self.controller.set_broadcast(name='Valid Name', password='bad')
        self.assertEqual(self.device.writes, [])
        with self.assertRaises(ValueError):
            self.controller.set_broadcast(name='Valid Name', encrypted=True)
        self.assertEqual(self.device.writes, [])

    def test_broadcast_name_key_info_order(self):
        self.controller.set_broadcast(name='Studio Audio', password='Secret123', public=False, quality=1)
        self.assertEqual(self.device.writes, [(C.SET_KEY, b'Secret123'),
            (C.SET_NAME, b'Studio Audio'), (C.SET_BROADCAST, b'\0\1\1')])
        status = self.controller.snapshot()
        self.assertEqual(status.broadcast_name, 'Studio Audio')
        self.assertEqual(status.broadcast_encrypted, 1)
        self.assertNotIn('Secret123', str(status.public_dict()))

    def test_existing_password_not_cleared_on_other_change(self):
        self.controller.set_broadcast(password='Secret123')
        self.device.writes.clear()
        self.controller.set_broadcast(quality=0)
        self.assertEqual(self.device.writes, [(C.SET_BROADCAST, b'\1\0\1')])
        self.assertEqual(self.device.values[C.GET_KEY].rstrip(b'\0'), b'Secret123')

    def test_reset_requires_confirmation(self):
        with self.assertRaises(ValueError):
            self.controller.factory_reset()
        self.assertEqual(self.device.writes, [])

    def test_reconnect_and_disconnect(self):
        self.controller.set_connection(False)
        self.assertEqual(self.controller.snapshot().state, 1)
        self.controller.set_connection(True)
        self.assertEqual(self.controller.snapshot().state, 2)

    def test_readback_mismatch_is_error(self):
        original = self.device.request
        self.device.request = lambda command, payload=b'': b'\0' if command == C.GET_CODEC else original(command, payload)
        with self.assertRaises(DeviceError):
            self.controller._verify(C.GET_CODEC, b'\4', timeout=0)
