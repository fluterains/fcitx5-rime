#!/usr/bin/env python3
"""Repackage a matching Ubuntu 24.04 base package with a Docker-built payload."""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile
import tarfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('base', type=Path)
parser.add_argument('payload', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
with tempfile.TemporaryDirectory(prefix='fcitx5-patch2-') as directory:
    root = Path(directory) / 'root'
    subprocess.run(['dpkg-deb', '-R', str(args.base), str(root)], check=True)
    control = root / 'DEBIAN/control'
    text = control.read_text()
    if not re.search(r'^Version: 5\.1\.4-2build2$', text, re.M):
        raise ValueError('Expected Ubuntu base version 5.1.4-2build2')
    if 'Architecture: amd64\n' not in text:
        raise ValueError('Expected amd64 package')
    if not re.search(r'^Package: fcitx5-rime$', text, re.M):
        raise ValueError('Unexpected base package')
    text = re.sub(r'^Version: .+$', 'Version: 5.1.4-2build2+patched.2', text, flags=re.M)
    text = re.sub(r'^X-Local-Variant:.*\n?', '', text, flags=re.M)
    text += 'X-Local-Variant: patch2\n'
    with tarfile.open(args.payload) as archive:
        archive.extractall(root, filter='data')
    files = sorted(p for p in root.rglob('*') if p.is_file() and not p.is_symlink()
                   and 'DEBIAN' not in p.relative_to(root).parts)
    (root / 'DEBIAN/md5sums').write_text(''.join(
        f'{hashlib.md5(p.read_bytes()).hexdigest()}  {p.relative_to(root)}\n' for p in files))
    text = re.sub(r'^Installed-Size: .+$',
                  f'Installed-Size: {(sum(p.stat().st_size for p in files)+1023)//1024}', text, flags=re.M)
    control.write_text(text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['dpkg-deb', '--root-owner-group', '-b', str(root), str(args.output)], check=True)
