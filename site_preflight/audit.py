"""Read local HTML only. No network, JavaScript, or third-party dependencies."""
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import os
import stat

MAX_HTML_BYTES = 5 * 1024 * 1024

MESSAGES = {
    'title.missing': ('Add a nonempty page title.', '空でないページタイトルを設定してください。'),
    'title.multiple': ('Use one title element.', 'title 要素を 1 個にしてください。'),
    'description.missing': ('Add a nonempty meta description.', '空でない meta description を設定してください。'),
    'description.multiple': ('Use one meta description.', 'meta description を 1 個にしてください。'),
    'h1.count': ('Review H1 count (expected one as a project convention).', 'H1 の数を確認してください（本ツールでは 1 個を推奨）。'),
    'image.alt': ('Image has no alt attribute; use meaningful text or empty alt for decoration.', '画像に alt がありません。説明文、または装飾画像なら空の alt を設定してください。'),
    'canonical.missing': ('Consider an absolute canonical URL.', '絶対 URL の canonical 設定を検討してください。'),
    'canonical.multiple': ('Review multiple canonical links.', 'canonical が複数あります。確認してください。'),
    'canonical.invalid': ('Canonical should be an absolute HTTP(S) URL without a fragment.', 'canonical はフラグメントのない HTTP(S) 絶対 URL にしてください。'),
    'link.missing': ('Local target does not exist.', 'ローカルのリンク先が存在しません。'),
    'link.anchor': ('Fragment ID/name not found in target HTML.', 'リンク先 HTML にフラグメントの ID/name がありません。'),
    'link.unsafe': ('Target escapes root or uses a symlink; not inspected.', 'ルート外またはシンボリックリンクのリンク先のため検査しません。'),
    'link.invalid': ('URL cannot be parsed.', 'URL を解析できません。'),
    'link.base': ('HTML base element changes URL resolution; local link checks skipped for this page.', 'base 要素により URL 解決が変わるため、このページのローカルリンク検査は省略しました。'),
    'file.unreadable': ('Cannot read HTML as UTF-8.', 'HTML を UTF-8 として読み取れません。'),
    'file.large': ('HTML exceeds 5 MiB inspection limit.', 'HTML が検査上限の 5 MiB を超えています。'),
    'file.special': ('Non-regular file skipped.', '通常のファイルではないため省略しました。'),
    'file.symlink': ('Symlink skipped.', 'シンボリックリンクを省略しました。'),
    'directory.unreadable': ('Directory cannot be read; coverage is incomplete.', 'ディレクトリを読み取れないため検査範囲が不完全です。'),
    'site.empty': ('No HTML files found.', 'HTML ファイルが見つかりません。'),
    'robots.missing': ('Root robots.txt missing (not always required).', 'ルートに robots.txt がありません（必須とは限りません）。'),
    'sitemap.missing': ('Root sitemap.xml missing (not always required).', 'ルートに sitemap.xml がありません（必須とは限りません）。'),
}

@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    path: str
    line: int = 0
    detail: str = ''

    def serialize(self, lang='en'):
        return {**asdict(self), 'message': MESSAGES[self.code][lang == 'ja']}

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titles, self.descriptions, self.canonicals = [], [], []
        self.h1 = 0
        self.ids, self.refs, self.images = set(), [], []
        self.title_depth = 0
        self.base = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        line = self.getpos()[0]
        if a.get('id') is not None:
            self.ids.add(a['id'])
        if tag == 'a' and a.get('name') is not None:
            self.ids.add(a['name'])
        if tag == 'title':
            self.titles.append('')
            self.title_depth += 1
        if tag == 'h1':
            self.h1 += 1
        if tag == 'meta' and (a.get('name') or '').lower() == 'description':
            self.descriptions.append(a.get('content') or '')
        if tag == 'link' and 'canonical' in (a.get('rel') or '').lower().split():
            self.canonicals.append((a.get('href') or '', line))
        if tag == 'img':
            self.images.append((a, line))
        if tag == 'base' and 'href' in a:
            self.base = True
        # Canonical/alternate/resource hints are not local navigation targets.
        if tag in ('a', 'area') and a.get('href') is not None:
            self.refs.append((a['href'], line))
        if tag in ('img', 'script', 'iframe', 'source', 'audio', 'video') and a.get('src'):
            self.refs.append((a['src'], line))
        if tag == 'link' and 'stylesheet' in (a.get('rel') or '').lower().split() and a.get('href'):
            self.refs.append((a['href'], line))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == 'title':
            self.title_depth = max(0, self.title_depth - 1)

    def handle_data(self, data):
        if self.title_depth and self.titles:
            self.titles[-1] += data


def safe_path(root, target):
    """No symlink component is allowed, even one resolving within root."""
    try:
        relative = target.relative_to(root)
    except ValueError:
        return False
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return False
    try:
        target.resolve().relative_to(root)
    except (ValueError, OSError, RuntimeError):
        return False
    return True


def inspect(root, coverage=None):
    if coverage is None:
        coverage = {}
    coverage.update(external_or_scheme_refs_unchecked=0, base_page_refs_unchecked=0, local_refs_checked=0, fragment_targets_unchecked=0)
    root = Path(root)
    if any(part.is_symlink() for part in (root, *root.parents)):
        raise ValueError('Site root and its ancestors must not be symlinks.')
    root = root.resolve()
    if not root.is_dir():
        raise ValueError('Site root must be an existing directory.')
    findings, pages = [], {}
    def add(code, severity, path='.', line=0, detail=''):
        findings.append(Finding(code, severity, path, line, detail))
    def walk_error(exc):
        try:
            name = Path(exc.filename).relative_to(root).as_posix()
        except (TypeError, ValueError):
            name = '.'
        add('directory.unreadable', 'error', name)
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        for name in sorted(dirs + files):
            p = Path(directory) / name
            if p.is_symlink():
                add('file.symlink', 'warning', p.relative_to(root).as_posix())
        dirs[:] = sorted(d for d in dirs if not (Path(directory) / d).is_symlink())
        for name in sorted(files):
            p = Path(directory) / name
            if p.suffix.lower() not in ('.html', '.htm') or p.is_symlink():
                continue
            rel = p.relative_to(root).as_posix()
            try:
                if not stat.S_ISREG(p.stat().st_mode):
                    add('file.special', 'warning', rel)
                    continue
                with p.open('rb') as stream:
                    raw = stream.read(MAX_HTML_BYTES + 1)
                if len(raw) > MAX_HTML_BYTES:
                    add('file.large', 'error', rel)
                    continue
                page = Page()
                page.feed(raw.decode('utf-8-sig'))
                page.close()
            except (OSError, UnicodeError):
                add('file.unreadable', 'error', rel)
                continue
            pages[p] = page
            if not page.titles or not any(t.strip() for t in page.titles):
                add('title.missing', 'error', rel)
            if len(page.titles) > 1:
                add('title.multiple', 'warning', rel)
            if not page.descriptions or not any(d.strip() for d in page.descriptions):
                add('description.missing', 'warning', rel)
            if len(page.descriptions) > 1:
                add('description.multiple', 'warning', rel)
            if page.h1 != 1:
                add('h1.count', 'warning', rel, detail=str(page.h1))
            for attrs, line in page.images:
                if 'alt' not in attrs:
                    add('image.alt', 'warning', rel, line)
            if not page.canonicals:
                add('canonical.missing', 'warning', rel)
            if len(page.canonicals) > 1:
                add('canonical.multiple', 'warning', rel)
            for canonical, line in page.canonicals:
                try:
                    u = urlsplit(canonical)
                    valid = (u.scheme in ('http', 'https') and bool(u.hostname)
                             and not u.fragment and u.username is None and u.password is None
                             and not any(ch.isspace() or ord(ch) < 32 for ch in canonical))
                    _ = u.port  # urlsplit defers invalid-port validation until access
                except ValueError:
                    valid = False
                if not valid:
                    add('canonical.invalid', 'warning', rel, line, canonical)
    if not pages:
        add('site.empty', 'error')
    for name, code in [('robots.txt', 'robots.missing'), ('sitemap.xml', 'sitemap.missing')]:
        if not safe_path(root, root / name) or not (root / name).is_file():
            add(code, 'info', name)
    for p, page in pages.items():
        rel = p.relative_to(root).as_posix()
        if page.base:
            add('link.base', 'warning', rel)
            coverage['base_page_refs_unchecked'] += len(page.refs)
            continue
        for ref, line in page.refs:
            try:
                u = urlsplit(ref)
            except ValueError:
                add('link.invalid', 'warning', rel, line, ref)
                continue
            if u.scheme or u.netloc:
                coverage['external_or_scheme_refs_unchecked'] += 1
                continue
            coverage['local_refs_checked'] += 1
            path = unquote(u.path)
            if '\x00' in path or '\\' in path:
                add('link.unsafe', 'error', rel, line, ref)
                continue
            target = p if not path else (root / path.lstrip('/') if path.startswith('/') else p.parent / path)
            if not safe_path(root, target):
                add('link.unsafe', 'error', rel, line, ref)
                continue
            target = target.resolve()
            candidates = [target / 'index.html', target / 'index.htm'] if target.is_dir() else [target]
            # Do not assume server-specific extensionless URL rewrites.
            target = next((t for t in candidates if safe_path(root, t) and t.is_file()), None)
            if target is None:
                add('link.missing', 'error', rel, line, ref)
                continue
            fragment = unquote(u.fragment)
            if fragment and (target not in pages or ':~:' in fragment):
                coverage['fragment_targets_unchecked'] += 1
            # Fragment directives are not element IDs; their text matching is unchecked.
            element_fragment = fragment.split(':~:', 1)[0]
            if element_fragment and target in pages:
                if element_fragment not in pages[target].ids and element_fragment.lower() != 'top':
                    add('link.anchor', 'warning', rel, line, ref)
    findings.sort(key=lambda f: (f.path, f.line, f.code, f.detail))
    return len(pages), findings


def report(root, lang='en'):
    coverage = {}
    count, findings = inspect(root, coverage)
    return {
        'schema_version': 1,
        'tool_version': '0.1.0',
        'language': lang,
        'coverage': coverage,
        'limitations': ['No network or JavaScript rendering', 'No full SEO or accessibility audit', 'No ranking guarantee', 'No server rewrite inference', 'robots/sitemap existence only; contents not validated'],
        'pages_checked': count,
        'summary': {s: sum(f.severity == s for f in findings) for s in ('error', 'warning', 'info')},
        'findings': [f.serialize(lang) for f in findings],
    }
