# Contributing

Thank you for helping make a small, honest static-export checklist useful.

This is an early MIT-licensed project. Contributions should describe a real problem and include a small reproducible synthetic example.

## Reproduce first

1. Use Python 3.11+ with no runtime dependencies.
2. Make a minimal synthetic HTML fixture. Remove customer data, real contact details, credentials, private URLs and access tokens.
3. Run `python -m unittest discover -s tests -v` and `python -m compileall -q site_preflight tests`.
4. Include expected vs actual behavior, Python version and operating system.

For changes, add focused tests, keep findings deterministic, keep rule IDs stable, and update both English/Japanese wording. Explain false-positive tradeoffs. A warning is not a standards violation unless the rule is truly normative. Do not turn intentionally empty decorative alt text into an error.

Avoid network crawling, paid APIs, telemetry and automatic publication in this narrow tool. Propose changes in scope before implementing them. AI-assisted contributions are welcome if the contributor checks the output, explains relevant assistance, and can account for rights and dependencies. Never fabricate tests, user feedback, benchmark results or adoption.

Security issues follow SECURITY.md, not a public issue containing a private export.
