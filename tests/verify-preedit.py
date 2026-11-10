#!/usr/bin/env python3
"""Exercise the Docker-built plugin through a private Fcitx D-Bus frontend."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

if os.environ.get('RIME_PATCH2_ISOLATED') != '1':
    env = dict(os.environ, RIME_PATCH2_ISOLATED='1')
    sys.exit(subprocess.run(['xvfb-run', '-a', '-s', '-screen 0 1600x900x24',
                            'dbus-run-session', '--', sys.executable, __file__],
                           env=env).returncode)

import dbus

fixtures = Path(__file__).resolve().parent / 'fixtures'
with tempfile.TemporaryDirectory(prefix='rime-patch2-preedit-') as directory:
    root = Path(directory)
    for name in ('home', 'config', 'data', 'cache', 'runtime'):
        (root / name).mkdir(mode=0o700)
    os.environ.update(HOME=str(root/'home'), XDG_CONFIG_HOME=str(root/'config'),
                      XDG_DATA_HOME=str(root/'data'), XDG_CACHE_HOME=str(root/'cache'),
                      XDG_RUNTIME_DIR=str(root/'runtime'), LANG='zh_CN.UTF-8')
    conf = root/'config/fcitx5'
    (conf/'conf').mkdir(parents=True)
    (conf/'profile').write_text('[Groups/0]\nName=Test\nDefault Layout=us\nDefaultIM=rime\n'
                               '[Groups/0/Items/0]\nName=rime\n[GroupOrder]\n0=Test\n')
    (conf/'conf/rime.conf').write_text('PreeditMode="Raw input"\nPreeditCursorPositionAtBeginning=False\n')
    shutil.copytree(fixtures, root/'data/fcitx5/rime')
    with (root/'fcitx.log').open('w') as log:
        process = subprocess.Popen(['fcitx5', '-D', '--disable=all',
                                    '--enable=xcb,dbus,dbusfrontend,classicui,keyboard,rime',
                                    '--ui=classicui'], stdout=log, stderr=log)
        try:
            bus = dbus.SessionBus()
            for _ in range(100):
                if bus.name_has_owner('org.fcitx.Fcitx5'):
                    break
                time.sleep(.1)
            im = dbus.Interface(bus.get_object('org.fcitx.Fcitx5',
                    '/org/freedesktop/portal/inputmethod'), 'org.fcitx.Fcitx.InputMethod1')
            path, _ = im.CreateInputContext(dbus.Array([
                    ('program', 'patch2-test'), ('display', 'x11:'+os.environ['DISPLAY'])], signature='(ss)'))
            ic = dbus.Interface(bus.get_object('org.fcitx.Fcitx5', path), 'org.fcitx.Fcitx.InputContext1')
            ic.SetCapability(dbus.UInt64(18))
            ic.FocusIn()
            ic.SetCursorRect(100, 100, 1, 20)
            subprocess.run(['fcitx5-remote', '-s', 'rime'], check=True)
            service = dbus.Interface(bus.get_object('org.fcitx.Fcitx5', '/rime'), 'org.fcitx.Fcitx.Rime1')
            for _ in range(100):
                if 'patch_test' in service.ListAllSchemas():
                    break
                time.sleep(.1)
            service.SetSchema('patch_test')
            service.SetAsciiMode(False)
            assert not service.IsAsciiMode()

            def key(symbol):
                events, handled = ic.ProcessKeyEventBatch(symbol, 0, 0, False, 0)
                preedits = []
                commits = []
                for kind, value in events:
                    if kind == 1:
                        parts, cursor = value
                        preedits.append((''.join(str(text) for text, flags in parts), int(cursor)))
                    elif kind == 0:
                        commits.append(str(value))
                return bool(handled), preedits, commits

            for index, letter in enumerate('nihao', 1):
                handled, preedits, _ = key(ord(letter))
                assert handled and preedits[-1] == ('nihao'[:index], index), preedits
            _, preedits, _ = key(0xff51)
            assert preedits[-1][0] == 'nihao' and preedits[-1][1] < 5, preedits
            for _ in range(10):
                _, preedits, _ = key(0xff53)
                if preedits and preedits[-1][1] == 5:
                    break
            _, _, commits = key(ord('2'))
            assert commits and any(any(ord(c) > 127 for c in word) for word in commits), commits
            key(ord('n'))
            _, preedits, _ = key(0xff1b)
            assert preedits[-1][0] == '', preedits
            for ascii_mode in (True, False):
                service.SetAsciiMode(ascii_mode)
                assert bool(service.IsAsciiMode()) == ascii_mode
            maps = Path(f'/proc/{process.pid}/maps').read_text()
            expected = os.environ.get('RIME_PATCH2_PLUGIN')
            if expected:
                assert str(Path(expected).resolve()) in maps, 'Wrong plugin loaded'
            print('PASS: raw letters, caret editing, Chinese commit, cancel, ASCII mode, plugin loading')
        except BaseException:
            print((root/'fcitx.log').read_text(), file=sys.stderr)
            raise
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
