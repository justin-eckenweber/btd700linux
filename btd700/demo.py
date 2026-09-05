"""Explicit, isolated demonstration device; never opens USB."""
from .i18n import tr
from .protocol import Command as C, encode


class DemoTransport:
    def __init__(self):
        self.events = {}
        self.values = {C.GET_STATE: b'\x03', C.GET_MODE: b'\0\3\1',
            C.GET_CODECS: b'\x0f', C.GET_CODEC: b'\4', C.GET_LE_STATE: b'\1',
            C.GET_QUALITY: b'\2\2', C.GET_TRANSPORTS: b'\1',
            C.GET_BROADCAST: b'\1\2\0', C.GET_NAME: b'BTD700 Demo'+bytes(21),
            C.GET_KEY: bytes(16), C.GET_VERSION: b'\3\x0b\0'}

    def request(self, command, payload=b''):
        encode(command, payload)
        if command in self.values:
            return self.values[command]
        if command == C.SET_MODE:
            self.values[C.GET_MODE] = payload + b'\1'
        elif command == C.SET_CODEC:
            self.values[C.GET_CODEC] = payload
        elif command == C.SET_CONNECTION:
            self.values[C.GET_STATE] = b'\2' if payload[0] else b'\1'
        elif command == C.SET_BROADCAST:
            self.values[C.GET_BROADCAST] = payload
        elif command == C.SET_NAME:
            self.values[C.GET_NAME] = (payload or b'BTD700 Demo').ljust(32, b'\0')
        elif command == C.SET_KEY:
            self.values[C.GET_KEY] = payload.ljust(16, b'\0')
        elif command == C.FACTORY_RESET:
            self.__init__()
        else:
            raise TimeoutError(tr('Nicht unterstützte Demo-Abfrage'))
        return b''

    def close(self):
        pass
