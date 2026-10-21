# Local verification — 2026-10-21

Actual local environment: Linux, Python 3.12.14.

- `python -m unittest discover -s tests -v`: 52 tests passed. Transcript: local-test-results.txt.
- `python -m compileall -q site_preflight tests`: passed.
- Clean synthetic export: 2 pages, zero findings, exit status 0 with warning threshold. Output: clean-report.ja.txt.
- Broken synthetic export: expected error findings, exit status 1; JSON parsed successfully. Output: example-report.ja.json.
- Independent review identified FIFO blocking, fragment handling, symlink ancestor and canonical shape issues; corrected with regression tests.

Remote CI: all 9 jobs passed on Ubuntu, Windows, macOS with Python 3.11, 3.12, 3.13. Windows skips the unsupported FIFO test. Run: https://github.com/mizuho-Te/site-preflight/actions/runs/39561280839 . Code commit: 7066ce01b765610864a97c6eb334164db8aa5698. The first remote run found a Windows cp1252 output error; UTF-8 CLI output and four subprocess regressions fixed it.

Not tested: actual customer exports, live websites, hosting rewrites, JavaScript rendering. Source publication was verified at https://github.com/mizuho-Te/site-preflight on 2026-10-21.  no user adoption or support-program eligibility is claimed.
