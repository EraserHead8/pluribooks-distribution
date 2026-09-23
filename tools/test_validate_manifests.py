import copy
import json
import tempfile
import unittest
from pathlib import Path

import validate_manifests as manifests


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_root = manifests.ROOT
        manifests.ROOT = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(setattr, manifests, 'ROOT', self.old_root)
        self.release = {
            'versionCode': 79, 'versionName': '0.2.74', 'publishedAt': '2026-09-23T12:00:00Z',
            'notes': ['Test'],
            'releaseUrl': 'https://github.com/EraserHead8/pluribooks-distribution/releases/tag/v0.2.74',
            'minSdk': 26,
            'apk': {'url': 'https://github.com/EraserHead8/pluribooks-distribution/releases/download/v0.2.74/app.apk',
                    'sha256': 'a' * 64, 'sizeBytes': 1024},
        }
        self.feed = {'schemaVersion': 1, 'channel': 'preview', 'applicationId': 'app.polka',
                     'release': self.release}
        self.history = {'schemaVersion': 1, 'channel': 'preview',
                        'versions': [{k: v for k, v in self.release.items() if k not in ('minSdk', 'apk')}]}

    def write(self):
        (manifests.ROOT / 'preview.json').write_text(json.dumps(self.feed))
        (manifests.ROOT / 'preview-versions.json').write_text(json.dumps(self.history))

    def test_valid_preview(self):
        self.write()
        manifests.validate('preview')

    def test_rejects_fake_checksum(self):
        self.feed['release']['apk']['sha256'] = '0' * 64
        self.write()
        with self.assertRaises(ValueError):
            manifests.validate('preview')

    def test_rejects_history_mismatch(self):
        self.history['versions'][0]['versionCode'] = 78
        self.write()
        with self.assertRaises(ValueError):
            manifests.validate('preview')

    def test_rejects_other_apk_host(self):
        self.feed['release']['apk']['url'] = 'https://example.com/app.apk'
        self.write()
        with self.assertRaises(ValueError):
            manifests.validate('preview')


if __name__ == '__main__':
    unittest.main()
