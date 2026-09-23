"""Check APK identity and signing certificate before announcing an update."""
import argparse
import re
import subprocess

APP_ID = 'app.polka'
SIGNER = 'd781f6729833bb303f6ad18eafd7b6be080b590f28e3a3070f2e3186f1df1a5a'


def capture(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)


def field(pattern, text, label):
    match = re.search(pattern, text)
    if not match:
        raise SystemExit(f'APK missing {label}')
    return match.group(1)


def inspect(apk, version_name, aapt='aapt', apksigner='apksigner'):
    badge = capture(aapt, 'dump', 'badging', apk)
    package = field(r"package: name='([^']+)'", badge, 'package ID')
    code = field(r"package: .*versionCode='([0-9]+)'", badge, 'versionCode')
    name = field(r"package: .*versionName='([^']+)'", badge, 'versionName')
    min_sdk = field(r"sdkVersion:'([0-9]+)'", badge, 'minSdk')
    certs = capture(apksigner, 'verify', '--print-certs', apk)
    signer = field(r'Signer #1 certificate SHA-256 digest: ([0-9a-fA-F]{64})', certs, 'signer').lower()
    if (package, name, signer) != (APP_ID, version_name, SIGNER):
        raise SystemExit(f'APK identity mismatch: {package} {name} signer={signer}')
    print(f'OK APK: {package} {name}, versionCode={code}, minSdk={min_sdk}, signer={signer}')
    return int(code), int(min_sdk)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apk', required=True)
    parser.add_argument('--version-name', required=True)
    parser.add_argument('--aapt', default='aapt')
    parser.add_argument('--apksigner', default='apksigner')
    args = parser.parse_args()
    inspect(args.apk, args.version_name, args.aapt, args.apksigner)
