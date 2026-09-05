#!/usr/bin/env python3
"""Extract only the application assembly from a locally supplied .NET bundle.

No downloading or execution of the original application. Output remains private
analysis material; it is not needed at runtime and must not be distributed here.
"""
import argparse
import io
from pathlib import Path
import struct
import zlib

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('output', type=Path, help='Output DLL path, outside this project')
args = parser.parse_args()
data = args.exe.read_bytes()
signature = bytes.fromhex('8b1202b96a612038727b930214d7a03213f5b9e6efae3318ee3b2dce24b36aae')
position = data.find(signature)
if position < 8:
    parser.error('No .NET bundle signature found')
offset = struct.unpack_from('<q', data, position - 8)[0]
if not 0 <= offset < len(data):
    parser.error('Invalid manifest offset')
stream = io.BytesIO(data)
stream.seek(offset)


def unpack(fmt):
    return struct.unpack(fmt, stream.read(struct.calcsize(fmt)))


def read_string():
    length = 0
    for shift in range(0, 35, 7):
        value = unpack('<B')[0]
        length |= (value & 127) << shift
        if not value & 128:
            if length > 4096:
                raise ValueError('Unexpected string length')
            return stream.read(length).decode('utf-8')
    raise ValueError('Invalid string prefix')


major, minor, count = unpack('<IIi')
if major != 6 or not 1 <= count <= 10000:
    parser.error('Expected a version-6 .NET bundle')
read_string()
stream.read(40)
for _ in range(count):
    offset, size, compressed, kind = unpack('<qqqB')
    name = read_string()
    if name != 'Sennheiser Dongle Control.dll':
        continue
    length = compressed or size
    if not 0 <= offset <= offset + length <= len(data) or not 0 < size < 32 * 1024 * 1024:
        parser.error('Invalid assembly bounds')
    blob = data[offset:offset + length]
    if compressed:
        decoder = zlib.decompressobj(-15)
        blob = decoder.decompress(blob, size + 1)
    if len(blob) != size or not blob.startswith(b'MZ'):
        parser.error('Assembly size or signature mismatch')
    with args.output.open('xb') as output:
        output.write(blob)
    print(f'Extracted {name}: {len(blob)} bytes to {args.output}')
    break
else:
    parser.error('Application assembly not found')
