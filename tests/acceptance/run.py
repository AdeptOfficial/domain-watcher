"""Workstation orchestrator. Explicit Compose project, no inherited app settings."""
import datetime as dt
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
CORE = '--core-only' in sys.argv
args = [x for x in sys.argv[1:] if x != '--core-only']
if len(args) != 1 or args[0].startswith('-'):
    sys.exit('Usage: ops/acceptance.sh [--core-only] BUILT_IMAGE')
image = args[0]
project = 'dw-acceptance-' + secrets.token_hex(6)
# Preserve only CLI necessities; do not inherit Compose/proxy/app configuration.
cli_env = {k: os.environ[k] for k in ('PATH', 'HOME', 'XDG_RUNTIME_DIR') if k in os.environ}
cli_env.update(ACCEPTANCE_IMAGE=image,
               ACCEPTANCE_START_HOUR=str((dt.datetime.now(dt.timezone.utc).hour + 12) % 24),
               ACCEPTANCE_HOUR=str((dt.datetime.now(dt.timezone.utc).hour + 11) % 24))
docker = ['docker', '--context', 'default']


def call(command, capture=False, timeout=240, check=True):
    return subprocess.run(command, env=cli_env, cwd=ROOT, text=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None,
                          timeout=timeout, check=check)


def ready(compose, service, url):
    script = 'import urllib.request; urllib.request.urlopen(' + repr(url) + ',timeout=2).read()'
    for _ in range(30):
        r = call(compose + ['exec', '-T', service, 'python', '-c', script], capture=True, check=False, timeout=5)
        if r.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError(service + ' failed readiness check')


def verify_network():
    network = project + '_isolated'
    internal = call(docker + ['network', 'inspect', '--format', '{{.Internal}}', network], capture=True)
    assert internal.stdout.strip() == 'true', 'network allows external connectivity'
    listing = call(docker + ['ps', '--filter', 'label=com.docker.compose.project=' + project,
                             '--format', '{{.Names}}|{{.Networks}}|{{.Ports}}'], capture=True)
    rows = listing.stdout.strip().splitlines()
    assert len(rows) == 2, 'unexpected test service count'
    for row in rows:
        name, networks, ports = row.split('|')
        assert name.startswith(project + '-'), 'unexpected container identity'
        assert networks == network, 'service attached outside isolated network'
        assert '->' not in ports, 'published test service port'
    print('PASS runtime network isolation and no published ports', flush=True)


def verify_logs(logs):
    assert 'manual sweep: 1 checked, 0 errors, 0 alerts' in logs, 'missing real sweep summary'
    for reason in ('HTTP 429', 'HTTP 503', 'json JSONDecodeError', 'parse AttributeError', 'request ReadTimeout'):
        assert 'reason=' + reason in logs, 'missing RDAP diagnostic: ' + reason
    assert 'rdap retry recovered:' in logs
    assert 'attempt=2/2' in logs and 'retry=no' in logs
    assert 'discord send failed: HTTP 404, not retrying' in logs
    assert 'ALERT NOT DELIVERED' in logs
    assert 'http://stub:8080/webhook' not in logs, 'webhook URL leaked'
    assert 'INVALID-JSON-SENTINEL' not in logs, 'RDAP response body leaked'
    hour = int(cli_env['ACCEPTANCE_HOUR'])
    assert f'daily check scheduled at {hour:02d}:00 (UTC)' in logs
    print('PASS runtime failure/retry logs, redaction, sweep summary and scheduler registration', flush=True)


def interrupted(signum, frame):
    raise SystemExit(128 + signum)


signal.signal(signal.SIGTERM, interrupted)


with tempfile.TemporaryDirectory(prefix='dw-acceptance-') as tmp:
    empty = Path(tmp) / 'empty.env'
    empty.write_text('')
    compose = docker + ['compose', '--env-file', str(empty), '-p', project,
                        '-f', str(ROOT / 'tests/acceptance/compose.yaml')]
    started = False
    try:
        image_id = call(docker + ['image', 'ls', '--no-trunc', '--format', '{{.ID}}', image], capture=True).stdout.strip()
        assert image_id and '\n' not in image_id, 'candidate must be exactly one locally built image'
        print('Candidate ' + image + ' ' + image_id, flush=True)
        started = True
        call(compose + ['up', '-d', 'stub', 'app'], timeout=90)
        ready(compose, 'stub', 'http://127.0.0.1:8080/healthz')
        ready(compose, 'app', 'http://127.0.0.1/healthz')
        verify_network()
        suffix = ['--core-only'] if CORE else []
        for phase in ('prepare', 'recover'):
            if phase == 'recover':
                call(compose + ['restart', 'app'], timeout=45)
                ready(compose, 'app', 'http://127.0.0.1/healthz')
                print('PASS real application container restart', flush=True)
            call(compose + ['run', '--rm', '--no-deps', 'runner', 'python', '/harness/scenarios.py', phase] + suffix,
                 timeout=360)
        logs = call(compose + ['logs', '--no-color', 'app'], capture=True).stdout
        if not CORE:
            verify_logs(logs)
        print('PASS acceptance suite complete for ' + image_id, flush=True)
    except BaseException:
        if started:
            # These are isolated fixture-only logs; no live environment/settings are loaded.
            result = call(compose + ['logs', '--no-color', '--tail', '100', 'app', 'stub'], capture=True, check=False)
            print(result.stdout, file=sys.stderr)
        raise
    finally:
        if started:
            call(compose + ['down', '--volumes', '--remove-orphans', '--timeout', '5'], timeout=60)
            print('Cleaned test project ' + project, flush=True)
