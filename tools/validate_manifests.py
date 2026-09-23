"""Validate both public update feeds before deployment, without external packages."""
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1] / 'site' / 'releases'
APP_ID = 'app.polka'
REPO = '/EraserHead8/pluribooks-distribution/releases/'


def check(ok, message):
    if not ok:
        raise ValueError(message)


def github_url(value, suffix):
    check(isinstance(value, str), 'missing GitHub URL')
    url = urlparse(value)
    check(url.scheme == 'https' and url.netloc == 'github.com' and
          url.path.startswith(REPO + suffix) and not url.query and not url.fragment,
          'URL must point to this repository GitHub Releases')
    check(len(url.path) > len(REPO + suffix), 'missing release tag or asset')


def release_item(item, label, apk=False):
    check(isinstance(item, dict), f'{label}: expected object')
    code = item.get('versionCode')
    check(type(code) is int and code > 0, f'{label}: invalid versionCode')
    name = item.get('versionName')
    check(isinstance(name, str) and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?', name),
          f'{label}: invalid versionName')
    published = item.get('publishedAt')
    check(isinstance(published, str) and published.endswith('Z'), f'{label}: invalid publishedAt')
    datetime.fromisoformat(published.replace('Z', '+00:00'))
    notes = item.get('notes')
    check(isinstance(notes, list) and len(notes) <= 8 and
          all(isinstance(n, str) and 0 < len(n) <= 500 for n in notes), f'{label}: invalid notes')
    github_url(item.get('releaseUrl'), 'tag/')
    if apk:
        check(type(item.get('minSdk')) is int and 23 <= item['minSdk'] <= 35, f'{label}: invalid minSdk')
        asset = item.get('apk')
        check(isinstance(asset, dict), f'{label}: missing APK')
        github_url(asset.get('url'), 'download/')
        check(asset['url'].endswith('.apk'), f'{label}: URL is not an APK')
        sha = asset.get('sha256')
        check(isinstance(sha, str) and re.fullmatch('[0-9a-f]{64}', sha) and sha != '0' * 64,
              f'{label}: invalid SHA-256')
        check(type(asset.get('sizeBytes')) is int and asset['sizeBytes'] >= 1024,
              f'{label}: invalid APK size')


def validate(channel):
    feed = json.loads((ROOT / f'{channel}.json').read_text(encoding='utf-8'))
    history_name = 'versions.json' if channel == 'stable' else 'preview-versions.json'
    history = json.loads((ROOT / history_name).read_text(encoding='utf-8'))
    check(feed.get('schemaVersion') == 1 and feed.get('channel') == channel and
          feed.get('applicationId') == APP_ID, f'{channel}: invalid feed identity')
    check(history.get('schemaVersion') == 1 and history.get('channel') == channel,
          f'{channel}: invalid history identity')
    entries = history.get('versions')
    check(isinstance(entries, list) and len(entries) <= 10, f'{channel}: invalid history')
    check('release' in feed, f'{channel}: release key missing')
    current = feed['release']
    check(current is not None or not entries, f'{channel}: history without current release')
    if current is not None:
        release_item(current, channel, apk=True)
        check(bool(entries), f'{channel}: current release missing from history')
        for field in ('versionCode', 'versionName', 'publishedAt', 'releaseUrl', 'notes'):
            check(current[field] == entries[0].get(field), f'{channel}: history {field} mismatch')
    codes = []
    for i, entry in enumerate(entries):
        release_item(entry, f'{channel} history {i}')
        codes.append(entry['versionCode'])
    check(codes == sorted(set(codes), reverse=True), f'{channel}: history must be descending and unique')
    print(f'OK: {channel}, active={current["versionName"] if current else "none"}, history={len(entries)}')


if __name__ == '__main__':
    try:
        validate('preview')
        validate('stable')
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
