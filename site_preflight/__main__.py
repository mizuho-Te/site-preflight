"""Command-line interface."""
import argparse
import json
import sys
from . import __version__
from .audit import report


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline static HTML preflight; no network requests.')
    parser.add_argument('directory', help='Local UTF-8 HTML export directory')
    parser.add_argument('--lang', choices=['en', 'ja'], default='en')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    parser.add_argument('--fail-on', choices=['error', 'warning', 'never'], default='error')
    parser.add_argument('--version', action='version', version=__version__)
    args = parser.parse_args(argv)
    try:
        result = report(args.directory, args.lang)
    except (ValueError, OSError) as exc:
        print(f'site-preflight: {exc}', file=sys.stderr)
        return 2
    if args.format == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        label = '点検ページ数' if args.lang == 'ja' else 'Pages checked'
        print(f"{label}: {result['pages_checked']}")
        print(' | '.join(f'{k}: {v}' for k, v in result['summary'].items()))
        print(('検査範囲: ' if args.lang == 'ja' else 'Coverage: ') + json.dumps(result['coverage'], ensure_ascii=False))
        print('オフライン点検のみ。外部 URL は未検査。完全な SEO・アクセシビリティ監査ではありません。' if args.lang == 'ja' else 'Offline only; external URLs unchecked. Not a full SEO/accessibility audit.')
        for f in result['findings']:
            safe_name = json.dumps(f['path'], ensure_ascii=False)
            print(f"[{f['severity']}] {safe_name}:{f['line']} {f['code']} — {f['message']}")
            if f['detail']:
                # Escape controls to avoid terminal escape injection from HTML input.
                print('  ' + json.dumps(f['detail'], ensure_ascii=False))
    counts = result['summary']
    return int(args.fail_on != 'never' and (counts['error'] > 0 or (args.fail_on == 'warning' and counts['warning'] > 0)))

if __name__ == '__main__':
    sys.exit(main())
