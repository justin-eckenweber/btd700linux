"""BTD 700 control protocol. No updater transport or arbitrary commands."""
from dataclasses import dataclass
from enum import IntEnum
import re

REPORT_ID = 0x34
REPORT_SIZE = 64


class ProtocolError(Exception):
    pass


class Command(IntEnum):
    GET_MODE = 0x01
    SET_MODE = 0x02
    GET_CODECS = 0x03
    SET_CODEC = 0x04
    GET_CODEC = 0x05
    GET_STATE = 0x06
    GET_LE_STATE = 0x07
    GET_QUALITY = 0x08
    GET_BROADCAST = 0x09
    SET_BROADCAST = 0x0A
    GET_KEY = 0x0B
    SET_KEY = 0x0C
    GET_NAME = 0x0D
    SET_NAME = 0x0E
    GET_VERSION = 0x12
    FACTORY_RESET = 0x13
    SET_CONNECTION = 0x14
    GET_TRANSPORTS = 0x15
    GET_GAMING = 0x17


READ_COMMANDS = frozenset(c for c in Command if c.name.startswith('GET_'))
EVENTS = frozenset((2, 3, 4, 15, 16, 17, 22, 23))
CODECS = {1: 'SBC', 2: 'aptX Classic', 4: 'aptX Adaptive', 8: 'aptX Lossless',
          16: 'aptX Lite (QMAP)', 32: 'LC3'}
MODES = {0: 'Standard', 1: 'Gaming', 2: 'Auracast'}
TRANSPORTS = {0: 'Nicht verbunden', 1: 'Bluetooth Classic', 2: 'LE Audio', 3: 'Automatisch'}
STATES = {0: 'Bereit', 1: 'Kopfhörer getrennt', 2: 'Kopfhörer verbunden',
          3: 'Musikwiedergabe', 4: 'Sprachanruf'}
MIN_LENGTHS = {Command.GET_MODE: 2, Command.GET_CODECS: 1, Command.GET_CODEC: 1,
               Command.GET_STATE: 1, Command.GET_LE_STATE: 1, Command.GET_QUALITY: 2,
               Command.GET_BROADCAST: 3, Command.GET_VERSION: 3,
               Command.GET_TRANSPORTS: 1, Command.GET_GAMING: 1}


def validate_text(value: str, *, key: bool = False) -> bytes:
    """Match the original app's 4–16 ASCII character input bounds; empty resets."""
    pattern = r'[A-Za-z0-9]{4,16}' if key else r'[A-Za-z0-9 ]{4,16}'
    if value and (not re.fullmatch(pattern, value) or value != value.strip()):
        what = 'Passwort: 4–16 Buchstaben oder Ziffern.' if key else (
            'Name: 4–16 Buchstaben, Ziffern oder innere Leerzeichen.')
        raise ValueError(what)
    return value.encode('ascii')


def encode(command: Command, payload: bytes = b'') -> bytes:
    try:
        command = Command(command)
    except ValueError as exc:
        raise ValueError('Unbekannter Steuerbefehl; kein Zugriff auf Update-Befehle.') from exc
    if command in READ_COMMANDS or command == Command.FACTORY_RESET:
        valid = not payload
    elif command == Command.SET_MODE:
        valid = len(payload) == 2 and payload[0] in MODES and payload[1] in (1, 2, 3)
    elif command == Command.SET_CODEC:
        valid = len(payload) == 1 and payload[0] in CODECS
    elif command == Command.SET_CONNECTION:
        valid = payload in (b'\0', b'\1')
    elif command == Command.SET_BROADCAST:
        valid = len(payload) == 3 and payload[0] in (0, 1) and payload[1] in (0, 1, 2) and payload[2] in (0, 1)
    elif command in (Command.SET_NAME, Command.SET_KEY):
        # Existing device names can contain an underscore. New user input is
        # validated more narrowly by validate_text, preserving originals on undo.
        valid = len(payload) <= 16 and all(32 <= b <= 126 for b in payload)
    else:
        valid = False
    if not valid:
        raise ValueError(f'Ungültige Parameter für {command.name}.')
    return bytes((REPORT_ID, 0xFE, command, len(payload))) + payload + bytes(60 - len(payload))


def acknowledge(event: int) -> bytes:
    if event not in EVENTS:
        raise ProtocolError(f'Unbekannte Benachrichtigung: {event:#x}')
    return bytes((REPORT_ID, 0xFD, event, 0)) + bytes(60)


@dataclass(frozen=True)
class Message:
    kind: int
    command: int
    payload: bytes


def decode(report: bytes) -> Message | None:
    if not report or report[0] != REPORT_ID:
        return None  # Media keys share the same interface.
    if len(report) < 4 or report[1] not in (0xFC, 0xFF) or report[3] > 60 or len(report) < 4 + report[3]:
        raise ProtocolError('Ungültige Antwort des Dongles.')
    return Message(report[1], report[2], report[4:4 + report[3]])
