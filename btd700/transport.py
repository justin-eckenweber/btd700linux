"""Linux hidraw access, limited to the BTD 700 control interface."""
from dataclasses import dataclass
from pathlib import Path
import fcntl
import os
import select
import struct
import time

from .protocol import Command, EVENTS, MIN_LENGTHS, ProtocolError, acknowledge, decode, encode


class DeviceError(Exception):
    pass


@dataclass(frozen=True)
class Device:
    path: str
    serial: str
    name: str = 'Sennheiser BTD 700'


def discover(sysfs: Path = Path('/sys/class/hidraw')) -> list[Device]:
    devices = []
    for node in sorted(sysfs.glob('hidraw*')):
        try:
            info = dict(line.split('=', 1) for line in (node / 'device/uevent').read_text().splitlines() if '=' in line)
            if info.get('HID_ID', '').upper() != '0003:00003542:00003001':
                continue
            descriptor = (node / 'device/report_descriptor').read_bytes()
            if b'\x06\xa2\xff' not in descriptor or b'\x85\x34' not in descriptor:
                continue
            devices.append(Device('/dev/' + node.name, info.get('HID_UNIQ', '')))
        except (OSError, ValueError):
            continue
    return devices


class Hidraw:
    def __init__(self, device: Device, timeout: float = 1.0):
        self.device = device
        self.timeout = timeout
        self.fd = None
        self.events = {}
        try:
            self.fd = os.open(device.path, os.O_RDWR | os.O_NONBLOCK | os.O_CLOEXEC | os.O_NOFOLLOW)
            info = bytearray(8)
            fcntl.ioctl(self.fd, 0x80084803, info, True)  # HIDIOCGRAWINFO
            bus, vendor, product = struct.unpack('IHH', info)
            if (bus, vendor, product) != (3, 0x3542, 0x3001):
                raise DeviceError('Gerätepfad gehört nicht mehr zum BTD 700.')
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise DeviceError('Der Dongle ist bereits in einer anderen Instanz geöffnet.') from exc
        except PermissionError as exc:
            self.close()
            raise DeviceError('USB-Zugriff fehlt. Die mitgelieferte udev-Regel installieren und den Dongle neu einstecken.') from exc
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _write(self, report):
        if self.fd is None:
            raise DeviceError('Dongle ist nicht geöffnet.')
        if not select.select([], [self.fd], [], self.timeout)[1]:
            raise TimeoutError('USB-Schreibzugriff hat nicht geantwortet.')
        if os.write(self.fd, report) != len(report):
            raise DeviceError('Unvollständiger USB-Schreibvorgang.')

    def _receive(self):
        report = os.read(self.fd, 1024)
        if not report:
            raise DeviceError('Dongle wurde entfernt.')
        message = decode(report)
        if message and message.kind == 0xFC and message.command in EVENTS:
            self.events[message.command] = message.payload
            self._write(acknowledge(message.command))
        return message

    def request(self, command: Command, payload: bytes = b'') -> bytes:
        report = encode(command, payload)  # Validate before any I/O.
        try:
            # Discard stale replies, acknowledging events. The cap prevents an
            # unrelated consumer-control input flood from blocking indefinitely.
            for _ in range(128):
                if not select.select([self.fd], [], [], 0)[0]:
                    break
                self._receive()
            self._write(report)
            deadline = time.monotonic() + self.timeout
            while (remaining := deadline - time.monotonic()) > 0:
                if not select.select([self.fd], [], [], remaining)[0]:
                    break
                message = self._receive()
                if message and message.kind == 0xFF and message.command == command:
                    if len(message.payload) < MIN_LENGTHS.get(command, 0):
                        raise ProtocolError(f'Unvollständige Antwort auf {command.name}.')
                    return message.payload
            raise TimeoutError(f'Der Dongle antwortet nicht auf {command.name}.')
        except (OSError, ProtocolError):
            self.close()
            raise
