"""Install, launch, or capture local Android diagnostics without clearing data."""
from pathlib import Path
import argparse
import shutil
import subprocess
import datetime

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'com.hyunmoo.hatchimon.arm64.dev'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--adb', default=shutil.which('adb') or 'adb')
    p.add_argument('--serial', required=True)
    sub = p.add_subparsers(dest='command', required=True)
    install = sub.add_parser('install')
    install.add_argument('apk', type=Path)
    sub.add_parser('launch')
    sub.add_parser('capture')
    a = p.parse_args()
    def run(*args, timeout=60):
        return subprocess.run([a.adb, '-s', a.serial, *map(str, args)], check=True,
                              stdout=subprocess.PIPE, timeout=timeout).stdout
    if a.command == 'install':
        print(run('install', '-r', a.apk).decode(errors='replace'))
    elif a.command == 'launch':
        print(run('shell', 'am', 'start', '-n', PACKAGE + '/com.zettabridge.launcher.HatchimonLaunchActivity').decode(errors='replace'))
    else:
        out = ROOT / 'device-debug' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        out.mkdir(parents=True)
        (out / 'logcat.txt').write_bytes(run('logcat', '-d', '-v', 'threadtime'))
        (out / 'screen.png').write_bytes(run('exec-out', 'screencap', '-p'))
        # Bugreport generation can take several minutes on the connected device.
        run('bugreport', out / 'bugreport.zip', timeout=300)
        print(out)

if __name__ == '__main__':
    main()
