#!/usr/bin/env python3
"""Recover the existing Telegram VPN, without restarting the bot or losing updates."""
import json
import logging
import subprocess
import time
from pathlib import Path

log = logging.getLogger('judges-vpn-health')


def reachable(run):
    try:
        result = run(['curl', '--silent', '--show-error', '--noproxy', '', '--proxy',
                      'http://10.200.0.2:8888', '--connect-timeout', '3', '--max-time', '8',
                      '--output', '/dev/null', '--write-out', '%{http_code}', 'https://api.telegram.org'],
                     capture_output=True, text=True, timeout=10)
        return result.returncode == 0 and result.stdout.strip() in ('200', '302')
    except (OSError, subprocess.TimeoutExpired):
        return False


def check(state_path, run=subprocess.run, now=None):
    now = time.time() if now is None else now
    # Respect intentional shutdown of the bot.
    if run(['systemctl', 'is-active', '--quiet', 'judges-bot'], timeout=10).returncode != 0:
        return 'bot_stopped'
    try:
        state = json.loads(state_path.read_text())
    except (FileNotFoundError, ValueError):
        state = {}
    state['failures'] = 0 if reachable(run) else state.get('failures', 0) + 1
    status = 'healthy' if state['failures'] == 0 else 'unreachable'
    if state['failures'] >= 2 and now - state.get('last_recovery', 0) >= 180:
        state['last_recovery'] = now
        state['failures'] = 0
        # Persist cooldown before restarting anything, including on exceptions.
        save(state_path, state)
        log.warning('Telegram unreachable twice; recovering VPN (bot stays running)')
        try:
            for operation, unit, timeout in [('stop', 'tinyproxy-cursorvpn', 15),
                                             ('restart', 'cursorvpn', 30),
                                             ('start', 'tinyproxy-cursorvpn', 90)]:
                run(['systemctl', operation, unit], check=True, timeout=timeout)
            status = 'recovered' if reachable(run) else 'recovery_failed'
        except (OSError, subprocess.SubprocessError) as exc:
            log.error('VPN recovery failed: %s', type(exc).__name__)
            status = 'recovery_failed'
        log.warning('VPN recovery result: %s', status)
    save(state_path, state)
    return status


def save(path, state):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(state))
    temporary.chmod(0o600)
    temporary.replace(path)


if __name__ == '__main__':
    import fcntl
    logging.basicConfig(level=logging.INFO)
    directory = Path('/var/lib/judges-vpn-health')
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (directory / 'lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        log.info('Health: %s', check(directory / 'state.json'))
