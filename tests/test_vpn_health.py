import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('vpn_healthcheck', Path(__file__).parents[1] / 'deploy/vpn_healthcheck.py')
health = importlib.util.module_from_spec(spec)
spec.loader.exec_module(health)


def test_two_failures_recover_vpn_without_restarting_bot(tmp_path):
    calls = []
    results = iter([False, False, True])
    def run(command, **kwargs):
        calls.append(command)
        if command[0] == 'curl':
            ok = next(results)
            return SimpleNamespace(returncode=0 if ok else 1, stdout='302' if ok else '')
        return SimpleNamespace(returncode=0)
    state = tmp_path / 'state.json'
    assert health.check(state, run, now=1000) == 'unreachable'
    assert health.check(state, run, now=1060) == 'recovered'
    assert ['systemctl','restart','cursorvpn'] in calls
    assert not any('restart' in c and 'judges-bot' in c for c in calls)
    assert json.loads(state.read_text())['last_recovery'] == 1060


def test_healthy_or_intentionally_stopped_does_not_restart(tmp_path):
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout='302')
    state = tmp_path / 'state.json'
    assert health.check(state, run, now=1000) == 'healthy'
    assert not any('restart' in c for c in calls)
    assert health.check(state, lambda *a, **k: SimpleNamespace(returncode=3), now=1100) == 'bot_stopped'


def test_failed_restart_has_persisted_cooldown(tmp_path):
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        if command[0] == 'curl':
            return SimpleNamespace(returncode=1, stdout='')
        if 'restart' in command:
            raise subprocess.TimeoutExpired(command,30)
        return SimpleNamespace(returncode=0)
    state=tmp_path/'state.json'
    state.write_text(json.dumps({'failures':1}))
    assert health.check(state,run,now=1000)=='recovery_failed'
    health.check(state,run,now=1060)
    health.check(state,run,now=1120)
    assert sum('restart' in c for c in calls)==1


def test_waits_for_proxy_to_listen_after_start(tmp_path):
    calls=[]
    results=iter([False, False, False, True])
    sleeps=[]
    def run(command, **kwargs):
        calls.append(command)
        if command[0]=='curl':
            ok=next(results)
            return SimpleNamespace(returncode=0 if ok else 7,stdout='302' if ok else '')
        return SimpleNamespace(returncode=0)
    state=tmp_path/'state.json'
    health.check(state,run,now=1000)
    assert health.check(state,run,now=1060,sleep=sleeps.append)=='recovered'
    assert sleeps==[1]
    assert sum('restart' in c for c in calls)==1
