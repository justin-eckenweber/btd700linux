import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from btd700.integration import APP_ID, autostart_path, desktop_entry, set_autostart, installed_icon

ROOT = Path(__file__).resolve().parents[1]


class IntegrationTests(unittest.TestCase):
    def test_install_and_remove_only_own_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, XDG_DATA_HOME=tmp+'/data', XDG_CONFIG_HOME=tmp+'/config', BTD700_LANGUAGE='en')
            desktop = Path(tmp) / 'data/applications' / f'{APP_ID}.desktop'
            other = desktop.parent / 'other-app.desktop'
            subprocess.run([sys.executable, 'install.py'], cwd=ROOT, env=env, check=True, capture_output=True)
            self.assertIn('Comment=Linux controls', desktop.read_text())
            self.assertIn('Comment[de]=', desktop.read_text())
            other.write_text('do not remove')
            with patch.dict(os.environ, env):
                set_autostart(True)
                startup = autostart_path()
                self.assertTrue(startup.exists())
                self.assertIn('--background', startup.read_text())
            subprocess.run([sys.executable, 'install.py', '--uninstall'], cwd=ROOT, env=env, check=True, capture_output=True)
            self.assertFalse(desktop.exists())
            self.assertFalse(startup.exists())
            self.assertEqual(other.read_text(), 'do not remove')

    def test_launcher_quotes_special_path_characters(self):
        with patch('btd700.integration.ROOT', Path('/tmp/BTD "Control" $home 100%')):
            with patch.object(Path, 'is_file', return_value=True):
                text = desktop_entry()
        self.assertIn('\\"Control\\"', text)
        self.assertIn('\\$home', text)
        self.assertIn('100%%', text)

    def test_installed_package_launcher_uses_python_module(self):
        with patch.object(Path, 'is_file', return_value=False):
            text = desktop_entry(background=True)
        self.assertIn(' -m btd700 --background', text)
        self.assertIn('Icon=audio-headphones', text)

    def test_appimage_autostart_survives_temporary_mount_removal(self):
        with tempfile.TemporaryDirectory() as tmp:
            mount = Path(tmp) / 'temporary-mount'
            mount.mkdir()
            (mount / 'btd700-control.svg').write_text('<svg/>')
            env = dict(APPIMAGE='/home/example/Apps/BTD "700" 100%.AppImage',
                       APPDIR=str(mount), XDG_CONFIG_HOME=tmp+'/config', XDG_DATA_HOME=tmp+'/data')
            with patch.dict(os.environ, env):
                set_autostart(True)
                text = autostart_path().read_text()
                self.assertIn('Exec="/home/example/Apps/BTD \\"700\\" 100%%.AppImage" --background', text)
                self.assertNotIn(str(mount), text)
                self.assertNotIn(' -m btd700', text)
                (mount / 'btd700-control.svg').unlink()
                mount.rmdir()
                self.assertEqual(installed_icon().read_text(), '<svg/>')

    def test_extracted_appimage_launcher_uses_environment_wrapper(self):
        with patch.dict(os.environ, {'APPDIR': '/tmp/Extracted app', 'APPIMAGE': ''}):
            text = desktop_entry()
        self.assertIn('Exec="/tmp/Extracted app/AppRun"', text)
        self.assertIn('Icon=/tmp/Extracted app/btd700-control.svg', text)
        self.assertNotIn(' -m btd700', text)

    def test_appimage_launcher_preserves_fuse_free_mode(self):
        with patch.dict(os.environ, {'APPDIR': '/tmp/mount', 'APPIMAGE': '/tmp/BTD.AppImage', 'APPIMAGE_EXTRACT_AND_RUN': '1'}):
            text = desktop_entry(background=True)
        self.assertIn('"/tmp/BTD.AppImage" --appimage-extract-and-run --background', text)

    def test_runtime_extraction_directory_preserves_fuse_free_mode(self):
        with patch.dict(os.environ, {'APPDIR': '/tmp/appimage_extracted_abc', 'APPIMAGE': '/tmp/BTD.AppImage'}):
            text = desktop_entry(background=True)
        self.assertIn(' --appimage-extract-and-run --background', text)
