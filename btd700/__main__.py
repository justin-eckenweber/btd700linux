import argparse
import getpass
import json
import sys


def main():
    parser = argparse.ArgumentParser(description='Native Linux-Steuerung für den BTD 700; ohne Firmware-Updates.')
    parser.add_argument('--device', help='Steuergerät aus dem Befehl devices, z. B. /dev/hidraw6')
    parser.add_argument('--background', action='store_true', help='Nur im Infobereich starten')
    parser.add_argument('--demo', action='store_true', help='Vorführmodus ohne USB-Zugriff')
    parser.add_argument('--smoke-seconds', type=int, default=0, help=argparse.SUPPRESS)
    subs = parser.add_subparsers(dest='command')
    subs.add_parser('devices', help='BTD-700-Steuerschnittstellen auflisten')
    subs.add_parser('status', help='Aktuellen Status als JSON ausgeben (ohne Passwort)')
    mode = subs.add_parser('mode', help='Audiomodus wählen')
    mode.add_argument('value', choices=['standard', 'gaming', 'auracast'])
    mode.add_argument('--transport', choices=['auto', 'classic', 'le'])
    codec = subs.add_parser('codec', help='Codec im Standard-Modus wählen')
    codec.add_argument('value', choices=['sbc', 'aptx', 'adaptive', 'lossless', 'qmap', 'lc3'])
    subs.add_parser('connect', help='Gekoppelte Kopfhörer verbinden')
    subs.add_parser('disconnect', help='Kopfhörer trennen')
    broadcast = subs.add_parser('auracast', help='Auracast-Einstellungen speichern')
    broadcast.add_argument('--name')
    broadcast.add_argument('--password', action='store_true', help='Neues Passwort verdeckt abfragen')
    broadcast.add_argument('--public', choices=['on', 'off'])
    broadcast.add_argument('--encryption', choices=['on', 'off'])
    broadcast.add_argument('--quality', choices=['16k', '24k', 'high'])
    reset = subs.add_parser('reset', help='Alle Kopplungen und Einstellungen löschen')
    reset.add_argument('--confirm', action='store_true')
    args = parser.parse_args()
    if not args.command:
        try:
            from .app import run
            return run(background=args.background, demo=args.demo, device=args.device, smoke_seconds=args.smoke_seconds)
        except (ImportError, ValueError) as exc:
            print(f'GTK-Oberfläche nicht verfügbar: {exc}\nAbhängigkeiten: siehe README.md. CLI: ./run.sh status', file=sys.stderr)
            return 1
    from .transport import DeviceError, Hidraw, discover
    from .controller import Controller
    from .protocol import ProtocolError
    if args.command == 'devices':
        from dataclasses import asdict
        print(json.dumps([asdict(d) for d in discover()], indent=2))
        return 0
    transport = None
    try:
        if args.demo:
            from .demo import DemoTransport
            transport = DemoTransport()
        else:
            devices = [d for d in discover() if not args.device or d.path == args.device]
            if len(devices) != 1:
                raise DeviceError('Kein eindeutiger BTD 700 gefunden. devices ausführen; bei mehreren Dongles --device angeben.')
            transport = Hidraw(devices[0])
        controller = Controller(transport)
        if args.command == 'mode':
            controller.set_mode(['standard', 'gaming', 'auracast'].index(args.value),
                {'auto': 3, 'classic': 1, 'le': 2}.get(args.transport))
        elif args.command == 'codec':
            controller.set_codec(1 << ['sbc', 'aptx', 'adaptive', 'lossless', 'qmap', 'lc3'].index(args.value))
        elif args.command in ('connect', 'disconnect'):
            controller.set_connection(args.command == 'connect')
        elif args.command == 'auracast':
            controller.set_broadcast(name=args.name,
                password=getpass.getpass('Neues Auracast-Passwort: ') if args.password else None,
                public=None if args.public is None else args.public == 'on',
                encrypted=None if args.encryption is None else args.encryption == 'on',
                quality={'16k': 0, '24k': 1, 'high': 2}.get(args.quality))
        elif args.command == 'reset':
            controller.factory_reset(confirmed=args.confirm)
            print('Zurücksetzen angefordert. Kopfhörer danach neu koppeln.')
            return 0
        print(json.dumps(controller.snapshot().public_dict(), indent=2, ensure_ascii=False))
        return 0
    except (OSError, DeviceError, ProtocolError, ValueError) as exc:
        print(f'Fehler: {exc}', file=sys.stderr)
        return 1
    finally:
        if transport:
            transport.close()


if __name__ == '__main__':
    raise SystemExit(main())
