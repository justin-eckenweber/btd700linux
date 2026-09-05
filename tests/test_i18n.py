import json
import os
from pathlib import Path
import string
import subprocess
import sys
import unittest

from btd700.controller import Controller
from btd700.demo import DemoTransport
from btd700.i18n import ENGLISH, detect_language, get_language, set_language, tr

ROOT = Path(__file__).resolve().parents[1]


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.language = get_language()

    def tearDown(self):
        set_language(self.language)

    def test_language_detection(self):
        for env, expected in (({}, 'en'), ({'LANG': 'de_DE.UTF-8'}, 'de'),
                              ({'LANG': 'fr_FR.UTF-8'}, 'en'),
                              ({'LANGUAGE': 'de:en', 'LANG': 'en_GB.UTF-8'}, 'de'),
                              ({'BTD700_LANGUAGE': 'en', 'LANG': 'de_DE.UTF-8'}, 'en')):
            self.assertEqual(detect_language(env), expected)

    def test_templates_keep_all_fields(self):
        formatter = string.Formatter()
        def fields(text):
            return sorted((field, spec, conversion) for _, field, spec, conversion in formatter.parse(text) if field is not None)
        for source, translated in ENGLISH.items():
            self.assertTrue(translated)
            self.assertEqual(fields(source), fields(translated), source)

    def test_status_translates_without_changing_device_values(self):
        controller = Controller(DemoTransport())
        set_language('en')
        english = controller.snapshot().public_dict()
        self.assertEqual(english['state_name'], 'Playing audio')
        self.assertEqual(english['transport_name'], 'Automatic')
        self.assertEqual(english['audio_quality'], '24-bit / 48 kHz')
        set_language('de')
        german = controller.snapshot().public_dict()
        self.assertEqual(german['state_name'], 'Musikwiedergabe')
        self.assertEqual(german['audio_quality'], '24 Bit / 48 kHz')
        for field in ('mode', 'transport', 'codec', 'firmware', 'broadcast_name'):
            self.assertEqual(english[field], german[field])

    def test_english_error(self):
        set_language('en')
        with self.assertRaisesRegex(ValueError, 'Unknown audio mode'):
            Controller(DemoTransport()).set_mode(255)
        set_language('de')
        self.assertEqual(tr('Speichern'), 'Speichern')
        self.assertEqual(tr('aptX Adaptive'), 'aptX Adaptive')

    def test_cli_override_and_help(self):
        env = dict(os.environ, BTD700_LANGUAGE='de')
        command = [sys.executable, '-m', 'btd700', '--language', 'en']
        result = subprocess.run(command + ['--demo', 'status'], cwd=ROOT, env=env, check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout)['state_name'], 'Playing audio')
        result = subprocess.run(command + ['--help'], cwd=ROOT, env=env, check=True, text=True, capture_output=True)
        self.assertIn('Start in the system tray only', result.stdout)
        self.assertNotIn('Nur im Infobereich', result.stdout)
