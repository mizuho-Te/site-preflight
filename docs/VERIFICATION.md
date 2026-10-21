# Local verification — 2026-10-21

Actual local environment: Linux, Python 3.12.14.

- `python -m unittest discover -s tests -v`: 48 tests passed. Transcript: local-test-results.txt.
- `python -m compileall -q site_preflight tests`: passed.
- Clean synthetic export: 2 pages, zero findings, exit status 0 with warning threshold. Output: clean-report.ja.txt.
- Broken synthetic export: expected error findings, exit status 1; JSON parsed successfully. Output: example-report.ja.json.
- Independent review identified FIFO blocking, fragment handling, symlink ancestor and canonical shape issues; corrected with regression tests.

Not tested: actual customer exports, live websites, hosting rewrites, JavaScript rendering, remote CI, Python 3.11/3.13, Windows/macOS. No external publication, user adoption, or support-program eligibility was verified.
