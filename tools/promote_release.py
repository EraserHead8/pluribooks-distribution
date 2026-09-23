"""Promote an already verified GitHub Release APK to a public channel."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from validate_manifests import ROOT, validate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--channel', choices=('preview', 'stable'), required=True)
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--version-name', required=True)
    parser.add_argument('--version-code', type=int, required=True)
    parser.add_argument('--min-sdk', type=int, required=True)
    parser.add_argument('--apk-url', required=True)
    parser.add_argument('--release-url', required=True)
    parser.add_argument('--notes-file', type=Path, required=True)
    args = parser.parse_args()
    feed_path = ROOT / f'{args.channel}.json'
    history_path = ROOT / ('versions.json' if args.channel == 'stable' else 'preview-versions.json')
    feed = json.loads(feed_path.read_text(encoding='utf-8'))
    history = json.loads(history_path.read_text(encoding='utf-8'))
    previous = feed['release']['versionCode'] if feed['release'] else 0
    if args.version_code <= previous or not args.apk.is_file():
        raise SystemExit('APK missing or versionCode has not increased')
    notes = [line.strip() for line in args.notes_file.read_text(encoding='utf-8').splitlines() if line.strip()][:8]
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    entry = {'versionCode': args.version_code, 'versionName': args.version_name,
             'publishedAt': stamp, 'notes': notes, 'releaseUrl': args.release_url}
    feed['release'] = {**entry, 'minSdk': args.min_sdk,
                       'apk': {'url': args.apk_url,
                               'sha256': hashlib.sha256(args.apk.read_bytes()).hexdigest(),
                               'sizeBytes': args.apk.stat().st_size}}
    history['versions'] = ([entry] + [v for v in history['versions'] if v['versionCode'] != args.version_code])[:10]
    feed_path.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    validate(args.channel)
    print(f'Promoted {args.channel} {args.version_name} ({args.version_code})')


if __name__ == '__main__':
    main()
