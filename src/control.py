"""Local WDA lifecycle helper. No Apple authentication or network-facing API."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import psutil


from kit_common import ROOT, CONFIG

STATE = ROOT / 'processes.json'


async def status():
    from pymobiledevice3.lockdown import create_using_usbmux
    from pymobiledevice3.services.wda import WdaServiceClient
    async with await create_using_usbmux(serial=CONFIG['udid']) as lockdown:
        data = await WdaServiceClient(lockdown).get_status()
        value = data.get('value', {})
        return {'ready': value.get('ready') is True, 'ios': value.get('os', {}).get('version'), 'wda_reported_version': value.get('build', {}).get('version')}


def probe():
    try:
        return asyncio.run(asyncio.wait_for(status(), timeout=8))
    except Exception as exc:
        return {'ready': False, 'error_type': type(exc).__name__}


def save(state):
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(state), encoding='utf-8')
    temp.replace(STATE)


def matching_process(entry):
    try:
        p = psutil.Process(entry['pid'])
        if abs(p.create_time() - entry['created']) > 0.1:
            return None
        if os.path.normcase(p.exe()) != os.path.normcase(entry['exe']):
            return None
        return p
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def stop():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    for name in ['runner', 'tunnel']:
        if name not in state:
            continue
        p = matching_process(state[name])
        if p:
            p.terminate()
            p.wait(timeout=10)
    save({})
    deadline = time.monotonic() + 10
    while probe()['ready']:
        if time.monotonic() >= deadline:
            raise RuntimeError('Registered processes stopped, but a WDA service still responds; inspect before starting another runner')
        time.sleep(0.5)


def spawn(name, args, state):
    with (ROOT / f'{name}.log').open('ab') as log:
        p = subprocess.Popen([CONFIG['ios'], *args], stdout=log, stderr=log, stdin=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    proc = psutil.Process(p.pid)
    state[name] = {'pid': p.pid, 'created': proc.create_time(), 'exe': proc.exe()}
    save(state)
    return p


def start():
    current = probe()
    if current['ready']:
        return current
    stop()
    # Refuse to attach to another task's listener.
    with socket.socket() as sock:
        try:
            sock.bind(('127.0.0.1', CONFIG['tunnel_info_port']))
        except OSError:
            raise RuntimeError('Tunnel info port is occupied by an unmanaged process')
    mount = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'pymobiledevice3', 'mounter', 'auto-mount', '--udid', CONFIG['udid']], capture_output=True, timeout=600, creationflags=subprocess.CREATE_NO_WINDOW)
    (ROOT / 'mount.log').write_bytes(mount.stdout + mount.stderr)
    if mount.returncode:
        raise RuntimeError('Developer image mount failed; inspect local mount.log')
    common = [f"--udid={CONFIG['udid']}", f"--tunnel-info-port={CONFIG['tunnel_info_port']}"]
    state = {}
    tunnel = spawn('tunnel', ['tunnel', 'start', '--userspace', *common], state)
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        if tunnel.poll() is not None:
            raise RuntimeError('Tunnel exited; inspect local tunnel.log')
        r = subprocess.run([CONFIG['ios'], 'tunnel', 'ls', *common], capture_output=True, timeout=8, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            entries = json.loads(r.stdout)
            if any(x.get('udid') == CONFIG['udid'] for x in entries):
                break
        except (ValueError, TypeError):
            pass
        time.sleep(1)
    else:
        raise RuntimeError('Tunnel did not become ready')
    runner = spawn('runner', ['runwda', *common, f"--bundleid={CONFIG['bundle_id']}", f"--testrunnerbundleid={CONFIG['bundle_id']}", '--xctestconfig=WebDriverAgentRunner.xctest', '--env=USE_IP=127.0.0.1', '--env=USE_PORT=8100', '--log-output=NUL'], state)
    print('若手机出现 XCTest / Enable UI Automation，请在手机上完成指纹或密码确认。', flush=True)
    deadline = time.monotonic() + 75
    while time.monotonic() < deadline:
        if runner.poll() is not None:
            raise RuntimeError('WDA exited; inspect runner.log. If authentication timed out, run start again when ready.')
        current = probe()
        if current['ready']:
            return current
        time.sleep(1)
    raise RuntimeError('WDA startup timed out; inspect local runner.log')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['start', 'stop', 'status'])
    action = parser.parse_args().action
    try:
        if action == 'start':
            result = start()
        elif action == 'stop':
            stop()
            result = {'stopped': True}
        else:
            result = probe()
        print(json.dumps(result, ensure_ascii=False))
        if action == 'status' and not result['ready']:
            sys.exit(1)
    except Exception as exc:
        if action == 'start':
            stop()
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
