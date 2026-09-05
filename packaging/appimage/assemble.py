#!/usr/bin/env python3
"""Bundle Ubuntu runtime files and record every contributing binary/source package."""
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
APPDIR = ROOT / 'build/appimage/BTD_700_Control.AppDir'
if APPDIR.exists():
    shutil.rmtree(APPDIR)
APPDIR.mkdir(parents=True)


def output(*args):
    return subprocess.check_output(args, text=True)


packages = {}
owners = {}
for line in output('dpkg-query', '-W', '-f=${binary:Package}\t${Version}\t${source:Package}\t${source:Version}\n').splitlines():
    name, version, source, source_version = line.split('\t')
    packages[name] = dict(package=name, version=version, source=source, source_version=source_version)
    for path in output('dpkg-query', '-L', name).splitlines():
        owners[path] = name
        if Path(path).is_file():
            owners[str(Path(path).resolve())] = name
included = set()


def copy(path, destination=None):
    path = Path(path)
    if path.name in {'__pycache__', 'icon-theme.cache', 'gschemas.compiled'} or path.suffix == '.pyc':
        return
    if path.is_dir():
        for child in sorted(path.iterdir()):
            copy(child, Path(destination) / child.name if destination else None)
    elif path.is_file():
        target = APPDIR / (str(destination) if destination else str(path).lstrip('/'))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        owner = owners.get(str(path)) or owners.get(str(path.resolve()))
        if not owner and path.is_relative_to('/usr/share/mime'):
            owner = owners['/usr/share/mime/packages/freedesktop.org.xml']
        if owner:
            included.add(owner)
        elif not path.is_relative_to(ROOT):
            raise RuntimeError(f'No package provenance for {path}')


for path in ['/usr/bin/python3.12', '/usr/lib/python3.12',
             '/usr/lib/python3/dist-packages/gi', '/usr/lib/python3/dist-packages/cairo',
             '/usr/lib/x86_64-linux-gnu/girepository-1.0',
             '/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders',
             '/usr/share/glib-2.0/schemas', '/usr/share/icons/Adwaita',
             '/usr/share/icons/hicolor', '/usr/share/fonts/truetype/dejavu',
             '/usr/share/mime',
             '/etc/fonts', '/usr/share/fontconfig']:
    copy(path)
# Include GTK/libadwaita's German translations as well as the app's own catalog.
for path in Path('/usr/share/locale').glob('de*/LC_MESSAGES/*.mo'):
    if path.name.startswith(('gtk40', 'libadwaita', 'glib20', 'gdk-pixbuf')):
        copy(path)
roots = list(APPDIR.rglob('*.so')) + [APPDIR / 'usr/bin/python3.12']
roots += [Path('/usr/lib/x86_64-linux-gnu') / name for name in
          ['libgtk-4.so.1', 'libadwaita-1.so.0', 'libdbusmenu-glib.so.4']]
# ldd includes the transitive ELF dependencies. glibc and the ELF loader belong
# to the host; Ubuntu 24.04 (glibc 2.39) is the documented compatibility floor.
host_libraries = re.compile(r'^(ld-linux.*|lib(c|m|dl|rt|pthread|resolv|util|nss_.*)\.so\..*)$')
libraries = set(roots[-3:])
for path in roots:
    for line in output('ldd', str(path)).splitlines():
        if 'not found' in line:
            raise RuntimeError(f'Missing dependency of {path}: {line}')
        match = re.search(r'=> (/\S+)', line)
        if match and not host_libraries.match(Path(match[1]).name):
            libraries.add(Path(match[1]))
for path in sorted(libraries):
    copy(path, 'usr/lib/x86_64-linux-gnu/' + path.name)

copy(ROOT / 'btd700', 'usr/share/btd700-control/btd700')
for name in ['install.py', 'LICENSE', 'THIRD_PARTY_NOTICES.md']:
    copy(ROOT / name, 'usr/share/btd700-control/' + name)
copy(ROOT / 'packaging/btd700-control.svg', 'btd700-control.svg')
copy(ROOT / 'packaging/btd700-control.svg', 'usr/share/icons/hicolor/scalable/apps/btd700-control.svg')
copy(ROOT / 'packaging/70-btd700-control.rules', 'usr/share/btd700-control/packaging/70-btd700-control.rules')
copy(ROOT / 'packaging/appimage/AppRun', 'AppRun')
copy(ROOT / 'packaging/appimage/environment.sh', 'usr/share/btd700-control/appimage-environment.sh')
(APPDIR / 'AppRun').chmod(0o755)
copy(ROOT / 'packaging/appimage/btd700-control.desktop', 'btd700-control.desktop')
(APPDIR / '.DirIcon').symlink_to('btd700-control.svg')
subprocess.run(['desktop-file-validate', str(APPDIR / 'btd700-control.desktop')], check=True)
subprocess.run(['glib-compile-schemas', str(APPDIR / 'usr/share/glib-2.0/schemas')], check=True)
cache = output('/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/gdk-pixbuf-query-loaders')
# A bare module name is resolved by dlopen through our LD_LIBRARY_PATH. This
# avoids storing a container or temporary AppImage mount path in the cache.
cache = re.sub(r'^"[^"\n]*/([^/"\n]+\.so)"$', r'"\1"', cache, flags=re.MULTILINE)
(APPDIR / 'usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders.cache').write_text(cache)
# Make the bundled fonts available without relying on a host font installation.
font_config = APPDIR / 'etc/fonts/fonts.conf'
font_config.write_text(font_config.read_text().replace('<fontconfig>',
    '<fontconfig>\n  <dir prefix="relative">../../usr/share/fonts</dir>'))

# License texts accompany the binary; complete corresponding Ubuntu source
# archives are downloaded separately by build.sh and attached to the release.
copy('/usr/share/common-licenses')
for package in sorted(included):
    doc = Path('/usr/share/doc') / package.split(':')[0] / 'copyright'
    if not doc.is_file():
        raise RuntimeError(f'No copyright file for {package}')
    copy(doc, 'usr/share/doc/btd700-bundled/' + package.replace(':', '_') + '.copyright')
manifest = [packages[name] for name in sorted(included)]
(APPDIR / 'usr/share/doc/btd700-bundled/packages.json').write_text(json.dumps(manifest, indent=2) + '\n')
(ROOT / 'build/appimage/packages.json').write_text(json.dumps(manifest, indent=2) + '\n')
sources = sorted({f"{p['source']}={p['source_version']}" for p in manifest})
(ROOT / 'build/appimage/sources.txt').write_text('\n'.join(sources) + '\n')
# Do not ship bytecode, Python tests, or compilation-only metadata.
for path in list(APPDIR.rglob('__pycache__')):
    shutil.rmtree(path)
for path in [APPDIR / 'usr/lib/python3.12/test', APPDIR / 'usr/lib/python3.12/config-3.12-x86_64-linux-gnu']:
    if path.exists():
        shutil.rmtree(path)
print(f'Assembled {APPDIR}: {len(manifest)} binary packages, {len(sources)} source packages')
