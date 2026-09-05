import os
import socket
import threading
import unittest
from btd700.protocol import Command as C, ProtocolError
from btd700.transport import Hidraw


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.host, self.device = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.transport = Hidraw.__new__(Hidraw)
        self.transport.fd = self.host.detach()
        self.transport.timeout = 0.1
        self.transport.events = {}

    def tearDown(self):
        self.transport.close()
        self.device.close()

    def test_event_and_unrelated_response_do_not_complete_request(self):
        ack = []
        def device():
            self.device.recv(64)
            os.write(self.device.fileno(), bytes.fromhex('0100'))
            os.write(self.device.fileno(), bytes.fromhex('34ff01020003'))
            os.write(self.device.fileno(), bytes.fromhex('34fc0f0103'))
            ack.append(self.device.recv(64))
            os.write(self.device.fileno(), bytes.fromhex('34ff060103'))
        thread = threading.Thread(target=device)
        thread.start()
        self.assertEqual(self.transport.request(C.GET_STATE), b'\3')
        thread.join(timeout=1)
        self.assertEqual(self.transport.events[15], b'\3')
        self.assertEqual(ack[0][:4], bytes.fromhex('34fd0f00'))

    def test_timeout_is_bounded(self):
        with self.assertRaises(TimeoutError):
            self.transport.request(C.GET_STATE)

    def test_short_payload_is_rejected(self):
        def device():
            self.device.recv(64)
            os.write(self.device.fileno(), bytes.fromhex('34ff080102'))
        thread = threading.Thread(target=device)
        thread.start()
        with self.assertRaises(ProtocolError):
            self.transport.request(C.GET_QUALITY)
        thread.join(timeout=1)

    def test_invalid_command_does_not_touch_device(self):
        with self.assertRaises(ValueError):
            self.transport.request(255)
        self.device.settimeout(0.01)
        with self.assertRaises(TimeoutError):
            self.device.recv(64)
