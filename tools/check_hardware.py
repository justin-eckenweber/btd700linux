#!/usr/bin/env python3
"""Opt-in reversible control test. Never resets or updates the dongle."""
import argparse
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from btd700.controller import Controller
from btd700.protocol import Command as C, encode
from btd700.transport import Hidraw, discover

parser = argparse.ArgumentParser(description='Steuerfunktionen testen und Originalwerte wiederherstellen; unterbricht kurz Audio.')
parser.add_argument('--run', action='store_true', required=True)
args = parser.parse_args()
devices = discover()
assert len(devices) == 1, 'Exactly one BTD 700 required'
with Hidraw(devices[0]) as transport:
    c = Controller(transport)
    original = c.snapshot()
    original_name = transport.request(C.GET_NAME).rstrip(b'\0')
    original_key = transport.request(C.GET_KEY).rstrip(b'\0')
    original_info = transport.request(C.GET_BROADCAST)
    # Refuse to mutate unless all saved values can be restored by this driver.
    encode(C.SET_KEY, original_key)
    encode(C.SET_NAME, original_name)
    encode(C.SET_BROADCAST, original_info)
    encode(C.SET_MODE, bytes((original.mode, original.transport)))
    print('Original:', original.mode, original.transport, original.codec, original.quality, flush=True)
    try:
        c.set_mode(0)
        print('PASS: Standard mode readback', flush=True)
        s = c.snapshot()
        chosen = next((value for value in (1, 2, 4, 8, 16, 32) if s.codecs & value), None)
        if chosen:
            c.set_codec(chosen)
            print('PASS: codec readback', chosen, flush=True)
        c.set_mode(2)
        print('PASS: Auracast mode readback', flush=True)
        c.set_broadcast(name='BTD700 Linux', public=not bool(original_info[0]), quality=(original_info[1]+1)%3)
        print('PASS: broadcast name, visibility and quality readback', flush=True)
        if len(original_key) <= 16 and all(32 <= b <= 126 for b in original_key):
            c.set_broadcast(password='LinuxTest2026', encrypted=True)
            assert transport.request(C.GET_KEY).rstrip(b'\0') == b'LinuxTest2026'
            print('PASS: password and encryption readback (secret omitted)', flush=True)
    finally:
        transport.request(C.SET_KEY, original_key)
        transport.request(C.SET_NAME, original_name)
        transport.request(C.SET_BROADCAST, original_info)
        transport.request(C.SET_MODE, bytes((0, original.transport)))
        deadline = time.monotonic()+10
        while time.monotonic() < deadline:
            s = c.snapshot()
            if s.state >= 2:
                break
            time.sleep(.25)
        if s.state >= 2 and s.codecs & original.codec:
            c.set_codec(original.codec)
        transport.request(C.SET_MODE, bytes((original.mode, original.transport)))
        c._verify(C.GET_MODE, bytes((original.mode, original.transport)), exact=False)
        assert transport.request(C.GET_NAME).rstrip(b'\0') == original_name
        assert transport.request(C.GET_KEY).rstrip(b'\0') == original_key
        assert transport.request(C.GET_BROADCAST) == original_info
        final = c.snapshot()
        print('RESTORED: mode, transport, Auracast name, key, visibility, quality, encryption', flush=True)
        print('Final:', final.mode, final.transport, final.codec, final.quality, flush=True)
