import tempfile
import unittest
from pathlib import Path
from btd700.protocol import Command as C, ProtocolError, acknowledge, decode, encode, validate_text
from btd700.transport import discover


class ProtocolTests(unittest.TestCase):
    def test_captured_status_response(self):
        message = decode(bytes.fromhex('34ff0103010301'))
        self.assertEqual(message.payload, b'\1\3\1')
        self.assertEqual(message.command, C.GET_MODE)

    def test_captured_get_state_request(self):
        self.assertEqual(encode(C.GET_STATE), bytes.fromhex('34fe0600') + bytes(60))

    def test_all_non_control_command_numbers_rejected(self):
        for value in range(256):
            if value not in set(C):
                with self.assertRaises(ValueError):
                    encode(value)

    def test_setter_validation(self):
        for command, args in ((C.SET_MODE, b'\3\3'), (C.SET_MODE, b'\0\0'),
                              (C.SET_CODEC, b'\3'), (C.SET_CONNECTION, b'\2'),
                              (C.SET_BROADCAST, b'\1\3\0'), (C.GET_STATE, b'\1'),
                              (C.SET_KEY, b'x' * 17), (C.FACTORY_RESET, b'\1')):
            with self.assertRaises(ValueError):
                encode(command, args)

    def test_malformed_and_unrelated_reports(self):
        for report in (b'\x34', b'\x34\xff\1', bytes.fromhex('34ff013d'), bytes.fromhex('34ff0602ff'), bytes.fromhex('34000600')):
            with self.assertRaises(ProtocolError):
                decode(report)
        self.assertIsNone(decode(b'\1\0'))
        self.assertIsNone(decode(b''))

    def test_event_ack(self):
        self.assertEqual(acknowledge(15), bytes.fromhex('34fd0f00') + bytes(60))
        with self.assertRaises(ProtocolError):
            acknowledge(255)

    def test_name_and_key_bounds(self):
        self.assertEqual(validate_text('Studio Audio'), b'Studio Audio')
        self.assertEqual(validate_text(''), b'')
        self.assertEqual(validate_text('A' * 16, key=True), b'A' * 16)
        for name in ('Hi', 'x' * 17, ' Musik', 'Musik ', 'Müsik', 'abc\0def'):
            with self.assertRaises(ValueError):
                validate_text(name)
        with self.assertRaises(ValueError):
            validate_text('abc def', key=True)

    def test_discovery_excludes_updater_and_other_devices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for number, vendor, descriptor in ((0, '3542', b'\x06\xa2\xff\x85\x34'),
                                               (1, '3542', b'\x06\x00\xff\x85\x05'),
                                               (2, '046D', b'\x06\xa2\xff\x85\x34')):
                node = root / f'hidraw{number}' / 'device'
                node.mkdir(parents=True)
                (node / 'uevent').write_text(f'HID_ID=0003:0000{vendor}:00003001\nHID_UNIQ=test\n')
                (node / 'report_descriptor').write_bytes(descriptor)
            self.assertEqual([d.path for d in discover(root)], ['/dev/hidraw0'])
