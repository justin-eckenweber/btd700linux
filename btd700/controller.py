"""Device operations with readback and capability checks."""
from dataclasses import asdict, dataclass
import time

from .protocol import CODECS, MODES, STATES, TRANSPORTS, Command as C, validate_text
from .transport import DeviceError


@dataclass
class Status:
    state: int
    mode: int
    transport: int
    connected_transport: int
    codecs: int
    codec: int
    resolution: int
    frequency: int
    le_state: int
    transports: int
    broadcast_public: int
    broadcast_quality: int
    broadcast_encrypted: int
    broadcast_name: str
    firmware: str
    gaming: int = -1

    @property
    def codec_name(self):
        return ' + '.join(name for bit, name in CODECS.items() if self.codec & bit) or '—'

    @property
    def quality(self):
        bits = {1: '16 Bit', 2: '24 Bit'}.get(self.resolution, '—')
        frequency = {1: '44,1 kHz', 2: '48 kHz', 3: '96 kHz'}.get(self.frequency, '—')
        return f'{bits} / {frequency}'

    @property
    def gaming_allowed(self):
        if self.gaming >= 0:
            return self.gaming == 1
        return self.mode == 1 or (self.state >= 2 and (self.connected_transport in (2, 3) or bool(self.codecs & 4)))

    def public_dict(self):
        result = asdict(self)
        result.update(state_name=STATES.get(self.state, f'Unbekannt ({self.state})'),
                      mode_name=MODES.get(self.mode, f'Unbekannt ({self.mode})'),
                      codec_name=self.codec_name, audio_quality=self.quality,
                      transport_name=TRANSPORTS.get(self.transport, f'Unbekannt ({self.transport})'))
        return result


class Controller:
    def __init__(self, transport):
        self.transport = transport
        self.firmware = None

    def snapshot(self) -> Status:
        q = self.transport.request
        state = q(C.GET_STATE)[0]
        mode = q(C.GET_MODE)
        quality = q(C.GET_QUALITY)
        codecs = q(C.GET_CODECS)[0]
        codec = q(C.GET_CODEC)[0]
        le = q(C.GET_LE_STATE)[0]
        transports = q(C.GET_TRANSPORTS)[0] if state >= 2 else 0
        broadcast = q(C.GET_BROADCAST)
        name = q(C.GET_NAME).split(b'\0', 1)[0].decode('utf-8', errors='replace')
        if self.firmware is None:
            try:
                self.firmware = '.'.join(map(str, q(C.GET_VERSION)[:3]))
            except TimeoutError:
                self.firmware = 'Unbekannt'
        # Firmware 3.11 does not respond to GET_GAMING; use events/fallback,
        # matching the original application's capability logic.
        event = self.transport.events.get(23, b'')
        return Status(state, mode[0], mode[1], mode[2] if len(mode) > 2 else mode[1],
                      codecs, codec, *quality[:2], le, transports, *broadcast[:3],
                      name, self.firmware, event[0] if event else -1)

    def _verify(self, getter, expected, *, timeout=5.0, exact=True, null_padded=False):
        deadline = time.monotonic() + timeout
        while True:
            result = self.transport.request(getter)
            comparison = result.rstrip(b'\0') if null_padded else result
            matches = comparison == expected if exact else comparison.startswith(expected)
            if matches:
                return
            if time.monotonic() >= deadline:
                raise DeviceError('Der Dongle hat die angeforderte Einstellung nicht bestätigt. Bitte den aktuellen Status prüfen.')
            time.sleep(0.15)

    def set_mode(self, mode: int, transport: int | None = None):
        status = self.snapshot()
        if mode not in MODES:
            raise ValueError('Unbekannter Audiomodus.')
        if mode == 1 and not status.gaming_allowed:
            raise ValueError('Gaming ist für die aktuelle Verbindung nicht verfügbar.')
        selected = status.transport if transport is None else transport
        if selected not in (1, 2, 3):
            raise ValueError('Unbekannter Bluetooth-Transport.')
        if transport is not None and selected in (1, 2) and status.transports and not status.transports & selected:
            raise ValueError('Die Kopfhörer unterstützen diesen Transport nicht.')
        payload = bytes((mode, selected))
        self.transport.request(C.SET_MODE, payload)
        self._verify(C.GET_MODE, payload, exact=False)

    def set_codec(self, codec: int):
        status = self.snapshot()
        if status.mode != 0 or status.state < 2:
            raise ValueError('Codec-Auswahl benötigt verbundene Kopfhörer im Standard-Modus.')
        if codec not in CODECS or not status.codecs & codec:
            raise ValueError('Dieser Codec wird für die aktuelle Verbindung nicht angeboten.')
        payload = bytes((codec,))
        self.transport.request(C.SET_CODEC, payload)
        self._verify(C.GET_CODEC, payload)

    def set_connection(self, connected: bool):
        self.transport.request(C.SET_CONNECTION, bytes((int(connected),)))
        deadline = time.monotonic() + 8
        while True:
            state = self.transport.request(C.GET_STATE)[0]
            if (state >= 2) == connected:
                return
            if time.monotonic() >= deadline:
                raise DeviceError('Verbindung wurde angefordert, aber noch nicht bestätigt. Sind die gekoppelten Kopfhörer eingeschaltet?')
            time.sleep(0.25)

    def set_broadcast(self, *, name=None, password=None, public=None, quality=None, encrypted=None):
        # Validate the entire change before issuing any setter.
        name_data = validate_text(name) if name is not None else None
        key_data = validate_text(password, key=True) if password is not None else None
        if any(value is not None and not isinstance(value, bool) for value in (public, encrypted)):
            raise ValueError('Auracast-Schalter benötigen einen booleschen Wert.')
        if quality is not None and quality not in (0, 1, 2):
            raise ValueError('Unbekannte Auracast-Qualität.')
        before = self.snapshot()
        info = [before.broadcast_public, before.broadcast_quality, before.broadcast_encrypted]
        if public is not None:
            info[0] = int(public)
        if quality is not None:
            info[1] = quality
        if password is not None:
            info[2] = int(bool(password))
        if encrypted is not None:
            info[2] = int(encrypted)
        if info[2] and key_data == b'':
            raise ValueError('Verschlüsselung benötigt ein Passwort mit 4–16 Zeichen.')
        if info[2] and key_data is None:
            existing = self.transport.request(C.GET_KEY).rstrip(b'\0')
            if len(existing) < 4:
                raise ValueError('Bitte zuerst ein Passwort mit 4–16 Zeichen eingeben.')
        # Preserve the original settings while changing a key, then write
        # key, name, and final settings in the order used by the original app.
        try:
            if key_data is not None and before.broadcast_encrypted:
                self.transport.request(C.SET_BROADCAST, bytes((before.broadcast_public, before.broadcast_quality, before.broadcast_encrypted)))
            if key_data is not None:
                self.transport.request(C.SET_KEY, key_data)
                self._verify(C.GET_KEY, key_data, null_padded=True)
            if name_data is not None:
                self.transport.request(C.SET_NAME, name_data)
                if name_data:
                    self._verify(C.GET_NAME, name_data, null_padded=True)
                else:
                    self.transport.request(C.GET_NAME)
            self.transport.request(C.SET_BROADCAST, bytes(info))
            self._verify(C.GET_BROADCAST, bytes(info))
        except Exception as exc:
            # Do not silently repeat writes or claim atomicity: settings persist
            # independently on the dongle.
            raise DeviceError('Auracast wurde nur teilweise oder nicht übernommen. Aktuellen Namen und Passwortschutz prüfen.') from exc

    def factory_reset(self, *, confirmed=False):
        if not confirmed:
            raise ValueError('Zurücksetzen muss ausdrücklich bestätigt werden; alle Kopplungen werden gelöscht.')
        self.transport.request(C.FACTORY_RESET)
