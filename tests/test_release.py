"""Packaging tests run against temporary copies, never against installed skills."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        # Keep isolated fixtures in the OS temp directory. No recursive deletion.
        self.root = Path(tempfile.mkdtemp(prefix='beer-buddy-release-test-'))
        for name in ['SKILL.md', 'VERSION', 'LICENSE', 'README.md', 'CONTRIBUTING.md', 'CHANGELOG.md', 'references', 'templates', 'agents', 'scripts', 'evals', 'docs', 'tests']:
            src = ROOT / name
            if src.is_dir():
                shutil.copytree(src, self.root / name, ignore=shutil.ignore_patterns('__pycache__'))
            elif src.exists():
                shutil.copy2(src, self.root / name)

    def run_release(self, *args):
        return subprocess.run([sys.executable, str(self.root / 'scripts/release.py'), *args], cwd=self.root, capture_output=True, text=True)

    def test_build_is_reproducible_and_portable(self):
        result = self.run_release()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        version = (self.root / 'VERSION').read_text().strip()
        archive = self.root / 'dist' / f'beer-buddy-{version}.zip'
        first = archive.read_bytes()
        with zipfile.ZipFile(archive) as z:
            self.assertIn('beer-buddy/SKILL.md', z.namelist())
            self.assertIn('beer-buddy/references/stories.json', z.namelist())
            self.assertTrue(all(n.startswith('beer-buddy/') and '..' not in n.split('/') for n in z.namelist()))
            self.assertFalse(any('release-work' in n or 'audit-' in n or '.git/' in n for n in z.namelist()))
        self.assertEqual(self.run_release().returncode, 0)
        self.assertEqual(first, archive.read_bytes())
        self.assertEqual(self.run_release('--check').returncode, 0)

    def test_stale_generated_prompt_is_detected(self):
        self.assertEqual(self.run_release().returncode, 0)
        (self.root / 'PROMPT.md').write_text('out of sync', encoding='utf-8')
        result = self.run_release('--check')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('PROMPT.md', result.stdout + result.stderr)

    def test_story_without_source_is_rejected(self):
        p = self.root / 'references/stories.json'
        data = json.loads(p.read_text())
        data['stories'][0]['source_url'] = ''
        p.write_text(json.dumps(data), encoding='utf-8')
        result = self.run_release()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('source_url', result.stdout + result.stderr)

    def test_shared_source_sections_reach_both_portable_editions(self):
        self.assertEqual(self.run_release('--generate-only').returncode, 0)
        for source in ['tasting', 'menu']:
            with self.subTest(source=source):
                p = self.root / ('references/' + source + '.md')
                marker = 'UNIQUE_' + source.upper() + '_FIXTURE'
                p.write_text(p.read_text(encoding='utf-8').replace('<!-- STARTER:END -->', marker + '\n<!-- STARTER:END -->'), encoding='utf-8')
                result = self.run_release('--check')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('stale', result.stderr)
                self.assertEqual(self.run_release('--generate-only').returncode, 0)
                for name in ['START.md', 'PROMPT.md']:
                    self.assertIn(marker, (self.root / name).read_text(encoding='utf-8'))

    def test_missing_or_duplicate_source_boundary_is_rejected(self):
        for source in ['tasting', 'menu']:
            p = self.root / ('references/' + source + '.md')
            original = p.read_text(encoding='utf-8')
            for replacement in ['', '<!-- STARTER:END --><!-- STARTER:END -->']:
                with self.subTest(source=source, replacement=replacement):
                    p.write_text(original.replace('<!-- STARTER:END -->', replacement), encoding='utf-8')
                    result = self.run_release('--generate-only')
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('STARTER', result.stderr)
            p.write_text(original, encoding='utf-8')

    def test_story_version_mismatch_is_rejected(self):
        p = self.root / 'references/stories.json'
        data = json.loads(p.read_text())
        data['skill_version'] = '0.0.0'
        p.write_text(json.dumps(data), encoding='utf-8')
        result = self.run_release()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('version', result.stdout + result.stderr)

    def test_private_files_do_not_enter_archive(self):
        (self.root / '.env').write_text('private fixture; not a real credential')
        (self.root / 'release-work').mkdir()
        (self.root / 'release-work/private.txt').write_text('not for publication')
        self.assertEqual(self.run_release().returncode, 0)
        version = (self.root / 'VERSION').read_text().strip()
        with zipfile.ZipFile(self.root / 'dist' / f'beer-buddy-{version}.zip') as z:
            self.assertFalse(any('.env' in n or 'private.txt' in n for n in z.namelist()))


if __name__ == '__main__':
    unittest.main()
