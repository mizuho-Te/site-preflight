# Security policy

No public reporting endpoint or support commitment has yet been established. Do not assume that private vulnerability reporting is enabled. A verified private reporting channel is a pending maintainer task. Do not publish secrets or sensitive sample exports in public issues.

## Intended boundary

- Local trusted static exports only; the tool sends no network requests.
- Symlink root ancestors, symlink entries and references escaping the selected root are not followed.
- This is not a hardened sandbox against a hostile user concurrently replacing paths/files. Do not run on a directory being changed by an untrusted process.
- HTML files are capped at 5 MiB individually. There is no total-file or total-memory cap; avoid huge/untrusted trees.
- Output includes root-relative file names and reference strings. Reports can reveal private content. Review them before sharing.
- Terminal controls from reference details and filenames are escaped in text output. JSON is data; consumers must escape fields when displaying in HTML.
- Do not treat JavaScript/data URLs as safe simply because their targets are not checked. This is not a malware scanner or HTML sanitizer.
- No dependencies are installed by the tool. CI configuration uses standard GitHub actions with read-only repository permissions.

0.1.0 is the initial source version. No security-response SLA is claimed.
