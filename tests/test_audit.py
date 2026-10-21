import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from site_preflight.audit import inspect, report, MAX_HTML_BYTES
from site_preflight.__main__ import main

HEAD = '<title>Sample</title><meta name="description" content="A synthetic sample"><link rel="canonical" href="https://example.test/">'
def html(body=''):
    return '<!doctype html><html lang="en"><head>' + HEAD + '</head><body><h1>Sample</h1>' + body + '</body></html>'

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.write('index.html', html())
        self.write('robots.txt', 'User-agent: *\nAllow: /\n')
        self.write('sitemap.xml', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>')
    def tearDown(self):
        self.temp.cleanup()
    def write(self, name, content):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
    def codes(self):
        return [f.code for f in inspect(self.root)[1]]
    def test_clean(self):
        self.assertEqual(self.codes(), [])
    def test_empty_title(self):
        self.write('index.html', html().replace('<title>Sample</title>', '<title> </title>'))
        self.assertIn('title.missing', self.codes())
    def test_duplicate_title(self):
        self.write('index.html', html('<title>Second</title>'))
        self.assertIn('title.multiple', self.codes())
    def test_missing_description(self):
        self.write('index.html', html().replace('name="description"', 'name="other"'))
        self.assertIn('description.missing', self.codes())
    def test_duplicate_description(self):
        self.write('index.html', html('<meta name="description" content="second">'))
        self.assertIn('description.multiple', self.codes())
    def test_h1_review_not_error(self):
        self.write('index.html', html('<h1>Second</h1>'))
        f = next(f for f in inspect(self.root)[1] if f.code == 'h1.count')
        self.assertEqual(f.severity, 'warning')
    def test_empty_alt_allowed(self):
        self.write('index.html', html('<img alt=""><img alt="Descriptive"><img alt>'))
        self.assertNotIn('image.alt', self.codes())
    def test_missing_alt(self):
        self.write('index.html', html('<img>'))
        self.assertIn('image.alt', self.codes())
    def test_external_schemes_excluded(self):
        self.write('index.html', html(''.join(f'<a href="{u}">link</a>' for u in ['https://example.invalid/missing', '//example.invalid/no', 'mailto:a@example.test', 'tel:123', 'data:text/plain,test', 'javascript:void(0)'])))
        self.assertEqual(self.codes(), [])
    def test_missing_local(self):
        self.write('index.html', html('<a href="gone.html">Link</a>'))
        self.assertIn('link.missing', self.codes())
    def test_query_and_fragment(self):
        self.write('index.html', html('<a href="?sort=1#hello">Link</a><p id="hello">Hi</p>'))
        self.assertEqual(self.codes(), [])
    def test_percent_path_and_anchor(self):
        self.write('index.html', html('<a href="hello%20world.html?x=1#%E9%B3%A5">Link</a>'))
        self.write('hello world.html', html('<p id="鳥">Hi</p>'))
        self.assertEqual(self.codes(), [])
    def test_directory_index(self):
        self.write('index.html', html('<a href="/guide/">Link</a><a href="guide">Link</a>'))
        self.write('guide/index.html', html())
        self.assertEqual(self.codes(), [])
    def test_index_htm(self):
        self.write('index.html', html('<a href="guide/">Link</a>'))
        self.write('guide/index.htm', html())
        self.assertEqual(self.codes(), [])
    def test_extensionless_no_implicit_rewrite(self):
        self.write('index.html', html('<a href="page">Link</a>'))
        self.write('page.html', html())
        self.assertIn('link.missing', self.codes())
    def test_missing_fragment(self):
        self.write('index.html', html('<a href="#gone">Link</a>'))
        self.assertIn('link.anchor', self.codes())
    def test_legacy_anchor(self):
        self.write('index.html', html('<a href="#old">Link</a><a name="old"></a>'))
        self.assertEqual(self.codes(), [])
    def test_text_fragment_skipped(self):
        self.write('index.html', html('<a href="#:~:text=Hi">Link</a>'))
        self.assertEqual(self.codes(), [])
    def test_relative_canonical(self):
        self.write('index.html', html().replace('https://example.test/', '/'))
        self.assertIn('canonical.invalid', self.codes())
    def test_canonical_fragment(self):
        self.write('index.html', html().replace('https://example.test/', 'https://example.test/#a'))
        self.assertIn('canonical.invalid', self.codes())
    def test_missing_root_metadata_info(self):
        (self.root / 'robots.txt').unlink()
        (self.root / 'sitemap.xml').unlink()
        self.assertTrue(all(f.severity == 'info' for f in inspect(self.root)[1]))
    def test_traversal_blocked(self):
        self.write('index.html', html('<a href="../outside.html">Link</a>'))
        self.assertIn('link.unsafe', self.codes())
    def test_encoded_traversal_blocked(self):
        self.write('index.html', html('<a href="%2e%2e/outside.html">Link</a>'))
        self.assertIn('link.unsafe', self.codes())
    def test_safe_parent_navigation(self):
        self.write('guide/index.html', html('<a href="../index.html">Home</a>'))
        self.assertEqual(self.codes(), [])
    def test_null_path(self):
        self.write('index.html', html('<a href="a%00b">Link</a>'))
        self.assertIn('link.unsafe', self.codes())
    def test_symlink_not_read(self):
        try:
            (self.root / 'alias.html').symlink_to(self.root / 'index.html')
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unsupported')
        self.write('index.html', html('<a href="alias.html">Link</a>'))
        self.assertIn('file.symlink', self.codes())
        self.assertIn('link.unsafe', self.codes())
        self.assertEqual(inspect(self.root)[0], 1)
    def test_symlink_directory_not_followed(self):
        try:
            (self.root / 'linked').symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unsupported')
        self.assertEqual(inspect(self.root)[0], 1)
    def test_invalid_utf8(self):
        (self.root / 'bad.html').write_bytes(b'\xff')
        self.assertIn('file.unreadable', self.codes())
    def test_large_html(self):
        (self.root / 'large.html').write_bytes(b' ' * (MAX_HTML_BYTES + 1))
        self.assertIn('file.large', self.codes())
    def test_base_skips_resolution(self):
        self.write('index.html', html('<base href="https://example.test/"><a href="absent">Link</a>'))
        self.assertEqual(self.codes(), ['link.base'])
    def test_asset_link(self):
        self.write('index.html', html('<img src="missing.png" alt="Bird">'))
        self.assertIn('link.missing', self.codes())
    def test_json_japanese(self):
        self.write('index.html', '<h1>Sample</h1>')
        result = report(self.root, 'ja')
        self.assertIn('タイトル', next(f['message'] for f in result['findings'] if f['code'] == 'title.missing'))
        self.assertNotIn(str(self.root), json.dumps(result))
    def test_deterministic(self):
        self.assertEqual(report(self.root), report(self.root))
    def test_cli_clean(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([str(self.root)]), 0)
    def test_cli_error(self):
        self.write('index.html', '')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([str(self.root)]), 1)
    def test_cli_warning_policy(self):
        self.write('index.html', html('<h1>Another</h1>'))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([str(self.root)]), 0)
            self.assertEqual(main([str(self.root), '--fail-on', 'warning']), 1)
            self.assertEqual(main([str(self.root), '--fail-on', 'never']), 0)
    def test_cli_json(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main([str(self.root), '--format', 'json']), 0)
        self.assertEqual(json.loads(output.getvalue())['schema_version'], 1)
    def test_nonexistent_root(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main([str(self.root / 'absent')]), 2)
    def test_coverage_external(self):
        self.write('index.html', html('<a href="https://example.test/">External</a>'))
        self.assertEqual(report(self.root)['coverage']['external_or_scheme_refs_unchecked'], 1)
    def test_coverage_base(self):
        self.write('index.html', html('<base href="/"><a href="unknown">Unknown</a>'))
        self.assertEqual(report(self.root)['coverage']['base_page_refs_unchecked'], 1)
    def test_root_symlink_refused(self):
        alias = self.root / 'root-alias'
        try:
            alias.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unsupported')
        with self.assertRaises(ValueError):
            inspect(alias)
    def test_directory_error_reported(self):
        def failed_walk(root, followlinks, onerror):
            onerror(PermissionError(13, 'denied', str(root / 'locked')))
            return iter([])
        with patch('site_preflight.audit.os.walk', failed_walk):
            self.assertIn('directory.unreadable', self.codes())
    def test_controls_escaped_in_text(self):
        self.write('index.html', html('<a href="missing\x1b[2J">X</a>'))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main([str(self.root)])
        self.assertNotIn('\x1b', output.getvalue())
    def test_top_and_combined_text_fragment(self):
        self.write('index.html', html('<a href="#top">Top</a><a href="#foo:~:text=X">X</a><p id="foo">X</p>'))
        self.assertEqual(self.codes(), [])
        self.assertEqual(report(self.root)['coverage']['fragment_targets_unchecked'], 1)
    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO not supported')
    def test_fifo_skipped(self):
        os.mkfifo(self.root / 'pipe.html')
        self.assertIn('file.special', self.codes())
    def test_root_symlink_ancestor_refused(self):
        self.write('real/sub/index.html', html())
        alias = self.root / 'alias'
        try:
            alias.symlink_to(self.root / 'real', target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unsupported')
        with self.assertRaises(ValueError):
            inspect(alias / 'sub')
    def test_bad_canonical_host_or_port(self):
        for bad in ('https://exa mple.test/', 'https://example.test:invalid/', 'https://user:pass@example.test/'):
            self.write('index.html', html().replace('https://example.test/', bad))
            self.assertIn('canonical.invalid', self.codes())
    def test_empty_site(self):
        (self.root / 'index.html').unlink()
        self.assertIn('site.empty', self.codes())

if __name__ == '__main__':
    unittest.main()
