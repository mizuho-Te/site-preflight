# site-preflight · 0.1.0

[日本語](README.ja.md)

A small offline preflight checklist for exported static HTML sites. Python 3.11+, standard library only, no API keys, network requests, account, or third-party Python dependencies.

**Initial source release under the [MIT License](LICENSE).** This is an early project validated on synthetic fixtures, not evidence of community adoption. No eligibility for or acceptance into an open-source support program is claimed.

## Try it

Clone this repository or download/extract its source ZIP and open a terminal in this directory. Nothing needs to be installed from a package registry.

```sh
python -m site_preflight examples/clean --lang en
python -m site_preflight examples/broken --lang ja
python -m site_preflight /path/to/export --format json > report.json
python -m site_preflight /path/to/export --fail-on warning
```

On Windows use `py -3` instead of `python` if necessary. Paths containing spaces must be quoted. Only inspect trusted local exports that are not being modified during the check. Input HTML must be UTF-8 (BOM supported), at most 5 MiB per file.

Exit status: 0 means no findings at the selected threshold, **not** a passing SEO/accessibility audit; 1 means findings at that threshold; 2 means invocation/input-directory failure. Default threshold is `error`; `--fail-on warning` includes warnings, and `--fail-on never` always returns 0 after a completed scan. Informational findings never fail a scan.

## What it checks

- Missing/empty and multiple titles and meta descriptions.
- H1 count for human review (one is a project convention, not a universal validity rule).
- Missing image `alt`. Empty `alt=""` is accepted because decorative images may require it; the tool cannot judge whether the image is truly decorative or the wording is appropriate.
- Missing/multiple canonical links and non-absolute HTTP(S) canonicals; this is a review aid, not verification of the canonical destination.
- Local navigation links, common `src` assets, stylesheet links, and HTML fragment targets.
- Root `robots.txt` and `sitemap.xml` existence only, not syntax, directives, crawl permission, or indexing status.

`title.missing`, missing local targets, unsafe paths, unreadable/oversized HTML, and empty exports are errors. Descriptions/canonicals/H1/alt/fragment issues are warnings. Missing robots/sitemap is informational: they are not universally required.

## Resolution and limits

All scheme-bearing and protocol-relative URLs are **unchecked**, including external HTTP(S), mailto, tel, data, JavaScript, and same-domain absolute URLs. Unchecked counts appear in the report; unchecked does not mean valid. No requests are sent.

Relative and root-relative references resolve within the supplied directory. Queries are ignored, percent-encoded paths/fragments decoded, and directories use index.html then index.htm. Exact file names are used: `/about` is not assumed to rewrite to `/about.html`. Host rewrite rules, deployment subpaths, redirects and SPA routes may produce local false positives and must be reviewed in the actual hosting environment. An HTML `base href` causes that page's local reference checks to be skipped with a warning. Text fragments are not validated. Anchors in unreadable or non-HTML files are not validated. Resource types such as CSS `url()`, `srcset`, inline SVG links, form submissions, JS-generated links and sitemap entries are not checked.

Symlinks are not followed, including targets inside the root and symlink components in the root path, and path traversal outside the root is rejected. This is a safe-use boundary, not a hardened sandbox against concurrent filesystem mutation. Run on trusted, stable exports only. Directory traversal/read failures should be reviewed independently; unreadable HTML is reported. Files not decoded as HTML are not counted as checked pages. There is no total project-size limit; very large sites may consume substantial memory/time.

This is **not** a browser, HTML standards validator, full SEO/accessibility audit, performance test, or security scanner. It cannot assess dynamic JavaScript, keyboard access, contrast, content usefulness, rankings, live availability or actual indexing. It does not guarantee search ranking or legal compliance.

## Reports

Text reports support `--lang en` and `--lang ja`. JSON schema version 1 contains `tool_version`, `language`, `pages_checked`, `coverage`, `limitations`, `summary`, and `findings`. A finding includes stable rule `code`, `severity`, root-relative `path`, `line` (0 means page/site scope), `detail`, and localized `message`. Prefer rule codes, not localized wording, for automation. Sorting is deterministic. Reports may contain private page filenames and original URLs from input: review before sharing.

## Development

```sh
python -m unittest discover -s tests -v
python -m compileall -q site_preflight tests
```

Synthetic fixtures only. The clean fixture should return 0; the broken fixture intentionally returns 1. [Verified CI](https://github.com/mizuho-Te/site-preflight/actions/runs/39561280839): all 9 OS/Python combinations passed on 2026-10-21; see docs/VERIFICATION.md. CLI stdout/stderr use UTF-8, including redirected Windows output.

## Why another checklist?

This project combines a narrow static-export checklist, no third-party Python packages, Japanese/English findings and JSON rule codes. It is complementary to established tools, not a claim of unique coverage or superiority. For broader work consider [HTML-validate](https://html-validate.org/), [lychee](https://github.com/lycheeverse/lychee), [Pa11y](https://pa11y.org/), and [Lighthouse](https://developer.chrome.com/docs/lighthouse/overview).

See [CONTRIBUTING](CONTRIBUTING.md), [SECURITY](SECURITY.md), and [release checklist](docs/RELEASE_CHECKLIST.md). Public repository: https://github.com/mizuho-Te/site-preflight . Use issues for non-sensitive bug reports; a private security-reporting channel remains to be established.
