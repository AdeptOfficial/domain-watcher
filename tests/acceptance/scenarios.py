"""Black-box checks against the real app HTTP routes and scripted peers."""
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

APP = 'http://app'
STUB = 'http://stub:8080'
PING = '123456789012345678'
CORE = '--core-only' in sys.argv


def request(base, path, data=None, form=False):
    if data is None:
        payload = None
    else:
        payload = urllib.parse.urlencode(data).encode() if form else json.dumps(data).encode()
    headers = {'Content-Type': 'application/x-www-form-urlencoded' if form else 'application/json'}
    with urllib.request.urlopen(urllib.request.Request(base + path, payload, headers), timeout=100) as response:
        return response.read().decode()


def page(path='/'):
    return request(APP, path)


def post(path, data=None):
    return request(APP, path, data or {}, form=True)


def state():
    return json.loads(request(STUB, '/state'))


def script(domain=None, responses=None, discord=()):
    payload = {'discord': list(discord)}
    if domain:
        payload['rdap'] = {domain: responses}
    request(STUB, '/script', payload)


def registered(**changes):
    body = {'status': ['active'], 'nameservers': [{'ldhName': 'ns.old.test'}],
            'entities': [{'roles': ['registrar'], 'vcardArray': ['vcard', [['fn', {}, 'text', 'Old Registrar']]]}],
            'events': [{'eventAction': 'expiration', 'eventDate': (dt.date.today() + dt.timedelta(days=365)).isoformat()}]}
    body.update(changes)
    return {'status': 200, 'body': body}


def assert_clean():
    s = state()
    assert not s['unexpected'], s['unexpected']
    assert not s['pending_rdap'], s['pending_rdap']
    assert not s['pending_discord'], s['pending_discord']


def did(domain):
    text = page()
    match = re.search(r'href="/domains/(\d+)"[^>]*>\s*' + re.escape(domain) + r'\s*</a>', text)
    assert match, f'domain missing from watchlist: {domain}'
    return match.group(1)


def add(domain, response=None):
    before = state()
    script(domain, [response or registered()])
    post('/domains', {'domain': domain, 'note': 'acceptance fixture'})
    assert len(state()['attempts']) == len(before['attempts']), 'baseline sent unexpected notification'
    assert_clean()
    return did(domain)


def check(domain, responses, contains=(), absent=(), discord=None, accepted=0):
    before = state()
    script(domain, responses, discord or ())
    text = post(f'/domains/{did(domain)}/check')
    after = state()
    attempts = after['attempts'][len(before['attempts']):]
    delivered = after['accepted'][len(before['accepted']):]
    assert len(after['requests']) - len(before['requests']) == len(responses), 'RDAP attempt count'
    assert len(attempts) == len(discord or ()), f'webhook attempt count: {attempts}'
    assert len(delivered) == accepted, f'accepted messages: {delivered}'
    content = '\n'.join(x['content'] for x in attempts)
    for value in contains:
        assert value in content, f'missing notification text {value!r}: {content}'
    for value in absent:
        assert value not in content, f'unexpected notification text {value!r}: {content}'
    assert_clean()
    return text


def success():
    return [{'status': 204}]


def run(name, func):
    func()
    assert_clean()
    print('PASS ' + name, flush=True)


def prepare_recovery():
    add('recovery.test')
    failure = {'status': 503}
    check('recovery.test', [failure, failure], contains=['lookups failing'], discord=success(), accepted=1)
    check('recovery.test', [failure, failure])
    post(f'/domains/{did("recovery.test")}/settings', {
        'note': 'persist this note', 'notify_ch': 'discord', 'ping_available': 'on', 'ping_drop': 'on'})
    add('changes.test')
    check('changes.test', [failure, failure], contains=['lookups failing'], discord=success(), accepted=1)
    # A safe hour far from now avoids incidental scheduled sweeps in this short-lived stack.
    post('/settings', {'webhook': STUB + '/webhook', 'ping_id': PING,
                       'check_hour': os.environ['ACCEPTANCE_HOUR']})


def recover():
    if not CORE:
        assert 'alert not delivered' in page(), 'notification warning lost at restart'
        run('notification warning persists across a real restart', lambda: None)
    text = page(f'/domains/{did("recovery.test")}')
    assert 'persist this note' in text
    available = {'status': 404}
    check('recovery.test', [available], contains=['lookups recovered', 'IS AVAILABLE', '<@' + PING + '>'],
          discord=success(), accepted=1)
    check('recovery.test', [available])
    if not CORE:
        assert 'alert not delivered' not in page(), 'successful recovery did not clear warning'
    run('outage baseline survives restart; recovery availability alerts once', lambda: None)
    changed = registered(status=['pendingDelete'], nameservers=[{'ldhName': 'ns.sedo.com'}],
                         entities=[{'roles': ['registrar'], 'vcardArray': ['vcard', [['fn', {}, 'text', 'New Registrar']]]}])
    check('changes.test', [changed], contains=['lookups recovered', 'DROP INCOMING', 'parking service',
                                             'Old Registrar', 'New Registrar', '<@' + PING + '>'],
          discord=success(), accepted=1)
    check('changes.test', [changed])
    run('outage retains drop, nameserver and registrar diffs across restart', lambda: None)


def normal_changes():
    add('available.test')
    check('available.test', [{'status': 404}], contains=['IS AVAILABLE', '<@' + PING + '>'],
          discord=success(), accepted=1)
    check('available.test', [{'status': 404}])
    add('drop.test')
    changed = registered(status=['redemptionPeriod'], nameservers=[{'ldhName': 'ns.sedo.com'}],
                         entities=[{'roles': ['registrar'], 'vcardArray': ['vcard', [['fn', {}, 'text', 'New Registrar']]]}])
    check('drop.test', [changed], contains=['DROP INCOMING', 'parking service', 'registrar:', '<@' + PING + '>'],
          discord=success(), accepted=1)
    check('drop.test', [changed])


def thresholds():
    add('expiry.test')
    for days in (30, 14, 7, 1):
        response = registered(events=[{'eventAction': 'expiration',
                                      'eventDate': (dt.date.today() + dt.timedelta(days=days)).isoformat()}])
        check('expiry.test', [response], contains=[f'expires in {days} day(s)', 'expiry moved:'],
              discord=success(), accepted=1)
        check('expiry.test', [response])
    failure = {'status': 500}
    check('expiry.test', [failure, failure], contains=['lookups failing'], discord=success(), accepted=1)
    # Leave expiry in an outage for the restart test.


def preferences():
    add('preferences.test')
    post(f'/domains/{did("preferences.test")}/toggle/ping_available')
    check('preferences.test', [{'status': 404}], contains=['IS AVAILABLE'], absent=['<@'],
          discord=success(), accepted=1)
    post(f'/domains/{did("preferences.test")}/toggle/ping_drop')
    check('preferences.test', [registered(status=['pendingDelete'])], contains=['DROP INCOMING'], absent=['<@'],
          discord=success(), accepted=1)
    post(f'/domains/{did("preferences.test")}/notify', {'value': 'none'})
    check('preferences.test', [{'status': 404}])
    post(f'/domains/{did("preferences.test")}/toggle/enabled')
    post(f'/domains/{did("preferences.test")}/settings', {
        'note': 'saved preferences', 'notify_ch': 'none', 'expiry_override': '2035-01-01'})


def request_failures():
    add('diagnostics.test')
    check('diagnostics.test', [{'status': 429}, registered()])
    check('diagnostics.test', [{'status': 503}, {'status': 503}], contains=['lookups failing'],
          discord=success(), accepted=1)
    check('diagnostics.test', [{'status': 200, 'raw': 'INVALID-JSON-SENTINEL'}] * 2)
    check('diagnostics.test', [{'status': 200, 'body': []}] * 2)
    check('diagnostics.test', [{'status': 200, 'delay': 21}, {'status': 200, 'delay': 21}])
    check('diagnostics.test', [registered()], contains=['lookups recovered'], discord=success(), accepted=1)


def failed_first():
    script('first.test', [{'status': 503}, {'status': 503}])
    post('/domains', {'domain': 'first.test'})
    assert_clean()
    check('first.test', [registered(status=['pendingDelete'])],
          contains=['lookups recovered', 'DROP INCOMING'], absent=['nameservers:', 'registrar:'],
          discord=success(), accepted=1)
    script('first-available.test', [{'status': 503}, {'status': 503}])
    post('/domains', {'domain': 'first-available.test'})
    check('first-available.test', [{'status': 404}], contains=['lookups recovered', 'IS AVAILABLE'],
          absent=['nameservers:', 'registrar:'], discord=success(), accepted=1)


def discord_failures():
    add('webhook.test')
    check('webhook.test', [{'status': 404}], contains=['IS AVAILABLE'],
          discord=[{'status': 500}, {'status': 429, 'body': {'retry_after': 0.01}}, {'status': 204}], accepted=1)
    assert 'alert not delivered' not in page()
    text = check('webhook.test', [registered()], discord=[{'status': 500}] * 3)
    assert 'alert not delivered' in text
    check('webhook.test', [{'status': 404}], discord=success(), accepted=1)
    assert 'alert not delivered' not in page()
    text = check('webhook.test', [registered()], discord=[{'status': 404}])
    assert 'alert not delivered' in text
    # This final warning must survive the restart; no queued resend is expected.


def finish():
    check('webhook.test', [{'status': 404}], discord=success(), accepted=1)
    assert 'alert not delivered' not in page()
    run('subsequent successful alert leaves notification warning clear', lambda: None)
    response = registered(events=[{'eventAction': 'expiration',
                                  'eventDate': (dt.date.today() + dt.timedelta(days=1)).isoformat()}])
    check('expiry.test', [response], contains=['lookups recovered'], absent=['expires in'],
          discord=success(), accepted=1)
    check('expiry.test', [response])
    run('expiry threshold deduplication survives outage and restart', lambda: None)
    text = page(f'/domains/{did("preferences.test")}')
    assert 'saved preferences' in text and '2035-01-01' in text
    assert re.search(r'<option value="none"\s+selected', text), 'notify preference not persisted'
    for name in ('ping_available', 'ping_drop'):
        tag = re.search(r'<input[^>]*name="' + name + r'"[^>]*>', text).group()
        assert 'checked' not in tag, name
    settings = page('/settings')
    assert STUB + '/webhook' in settings and PING in settings
    assert f'value="{os.environ["ACCEPTANCE_HOUR"]}"' in settings
    run('settings and domain preferences persist across restart', lambda: None)
    # Disable every domain except one, then exercise the real bulk-check route.
    for domain in ['recovery.test', 'changes.test', 'available.test', 'drop.test', 'expiry.test',
                   'diagnostics.test', 'first.test', 'first-available.test', 'webhook.test']:
        post(f'/domains/{did(domain)}/toggle/enabled')
    add('bulk.test')
    before = state()
    script('bulk.test', [registered()])
    post('/check')
    after = state()
    assert after['requests'][len(before['requests']):] == ['bulk.test'], 'disabled domain checked'
    assert len(after['attempts']) == len(before['attempts']), 'unchanged sweep notified'
    assert json.loads(page('/healthz')) == {'status': 'ok', 'domains': 11}
    run('bulk sweep skips disabled domains; health reports all watched domains', lambda: None)


def main():
    phase = sys.argv[1]
    if phase == 'prepare':
        post('/settings', {'webhook': STUB + '/webhook', 'ping_id': PING,
                           'check_hour': os.environ['ACCEPTANCE_HOUR']})
        assert json.loads(page('/healthz'))['domains'] == 0
        run('registered baseline appears without notification', lambda: add('recovery.test'))
        # prepare_recovery owns its initial registered snapshot; remove the smoke fixture.
        post(f'/domains/{did("recovery.test")}/delete')
        run('prepare repeated outages and persistent baseline', prepare_recovery)
        if not CORE:
            run('availability, drop, parking and registrar changes', normal_changes)
            run('expiry threshold transitions and duplicate suppression', thresholds)
            run('ping and channel preferences', preferences)
            run('HTTP retries, malformed responses and real read timeouts', request_failures)
            run('initial failure recovery has no invented changes', failed_first)
            run('Discord retry success, exhaustion and permanent failure', discord_failures)
    elif phase == 'recover':
        recover()
        if not CORE:
            finish()
    else:
        raise ValueError('unknown scenario phase')
    assert_clean()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'FAIL {type(exc).__name__}: {exc}', flush=True)
        raise
