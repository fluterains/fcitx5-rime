#!/usr/bin/env python3
"""Repackage Ubuntu 24.04 base debs with the two Docker-built plugins."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--rime-base', required=True, type=Path)
parser.add_argument('--modules-base', required=True, type=Path)
parser.add_argument('--build-dir', type=Path, default=Path('out/linear-highlight'))
parser.add_argument('--revision', type=int, default=1)
args = parser.parse_args()
if args.revision < 1:
    parser.error('--revision must be positive')
suffix = '+linear' + str(args.revision)
output = args.build_dir.resolve()
output.mkdir(parents=True, exist_ok=True)


def package(base, name, replace):
    with tempfile.TemporaryDirectory(prefix='linear-package-') as temporary:
        root = Path(temporary) / 'root'
        subprocess.run(['dpkg-deb', '-R', str(base), str(root)], check=True)
        control = root / 'DEBIAN/control'
        text = control.read_text()
        if not re.search(r'^Package: ' + re.escape(name) + r'$', text, re.M):
            raise ValueError(f'{base} is not a {name} package')
        old_version = re.search(r'^Version: (.+)$', text, re.M).group(1)
        # fcitx5 and fcitx5-modules-dev depend on the exact modules version.
        # Keep that version and identify this rebuild with a custom field.
        version = old_version if name == 'fcitx5-modules' else old_version + suffix
        replace(root)
        files = sorted(p for p in root.rglob('*')
                       if p.is_file() and not p.is_symlink()
                       and 'DEBIAN' not in p.relative_to(root).parts)
        (root / 'DEBIAN/md5sums').write_text(''.join(
            f'{hashlib.md5(p.read_bytes()).hexdigest()}  {p.relative_to(root)}\n'
            for p in files))
        text = re.sub(r'^Version: .+$', 'Version: ' + version, text, flags=re.M)
        text += f'X-Local-Variant: linear-highlight-{args.revision}\n'
        size = (sum(p.stat().st_size for p in files) + 1023) // 1024
        text = re.sub(r'^Installed-Size: \d+$', f'Installed-Size: {size}', text, flags=re.M)
        control.write_text(text)
        filename_version = old_version + suffix
        destination = output / f'{name}_{filename_version}_amd64.deb'
        subprocess.run(['dpkg-deb', '--root-owner-group', '-b', str(root), str(destination)], check=True)
        return destination


def replace_rime(root):
    with tarfile.open(output / 'fcitx5-rime-5.1.4-tray-labels.tar.gz') as archive:
        archive.extractall(root, filter='data')


def replace_classicui(root):
    shutil.copy2(output / 'libclassicui.so', root / 'usr/lib/x86_64-linux-gnu/fcitx5/libclassicui.so')


paths = [package(args.rime_base, 'fcitx5-rime', replace_rime),
         package(args.modules_base, 'fcitx5-modules', replace_classicui)]
(output / 'SHA256SUMS').write_text(''.join(
    f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in paths))
