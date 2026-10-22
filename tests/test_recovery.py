"""Recovery regressions: isolated SQLite, mocked RDAP, no network or notifier."""
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from app import db, main


def snapshot(**changes):
    return dict(dict(available=False, error=False, status=['active'],
                     expiry=None, ns=['ns.example.test'], registrar='Example'), **changes)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {}, clear=True)
        env.start()
        self.addCleanup(env.stop)
        path = patch.object(db, 'DB_PATH', self.tmp.name + '/watcher.db')
        path.start()
        self.addCleanup(path.stop)
        db.init()
        db.set_setting('ping_discord_id', '123')
        self.did = db.add_domain('example.test')
        self.failed = snapshot(error=True, status=[], ns=[], registrar=None)

    def check(self, value):
        # Reload from SQLite for every check, as after an application restart.
        with patch.object(main, 'fetch', return_value=value.copy()):
            return main.check_domain(db.get_domain(self.did))

    def test_availability_after_repeated_failure_alerts_once(self):
        self.assertEqual(self.check(snapshot()), [])
        self.assertIn('failing', ' '.join(self.check(self.failed)))
        self.assertEqual(self.check(self.failed), [])
        stored = json.loads(db.get_domain(self.did)['snapshot'])
        self.assertEqual(stored['last_success']['status'], ['active'])
        self.assertNotIn('last_success', stored['last_success'])
        available = snapshot(available=True, status=[], ns=[], registrar=None)
        alerts = ' '.join(self.check(available))
        self.assertIn('recovered', alerts)
        self.assertIn('IS AVAILABLE', alerts)
        self.assertIn('<@123>', alerts)
        self.assertEqual(self.check(available), [])
        self.assertNotIn('last_success', json.loads(db.get_domain(self.did)['snapshot']))

    def test_drop_and_other_changes_during_outage(self):
        self.check(snapshot())
        self.check(self.failed)
        alerts = ' '.join(self.check(snapshot(status=['pending delete'],
                                             ns=['ns.sedo.com'], registrar='New')))
        for expected in ('recovered', 'DROP INCOMING', '<@123>', 'parking service', 'registrar:'):
            self.assertIn(expected, alerts)

    def test_unchanged_recovery_only_reports_recovery(self):
        self.check(snapshot())
        self.check(self.failed)
        alerts = self.check(snapshot())
        self.assertEqual(len(alerts), 1)
        self.assertIn('recovered', alerts[0])

    def test_already_available_does_not_repeat_alert_after_outage(self):
        available = snapshot(available=True, status=[], ns=[], registrar=None)
        self.check(available)
        self.check(self.failed)
        alerts = self.check(available)
        self.assertEqual(len(alerts), 1)
        self.assertIn('recovered', alerts[0])

    def test_unknown_baseline_normal_recovery_has_no_invented_changes(self):
        self.check(self.failed)
        alerts = self.check(snapshot())
        self.assertEqual(len(alerts), 1)
        self.assertIn('recovered', alerts[0])

    def test_legacy_error_without_baseline_available(self):
        db.save_check(self.did, self.failed, None, 'error')
        alerts = ' '.join(self.check(snapshot(available=True, status=[], ns=[], registrar=None)))
        self.assertIn('IS AVAILABLE', alerts)
        self.assertNotIn('registrar:', alerts)

    def test_failed_first_check_then_drop(self):
        self.assertEqual(self.check(self.failed), [])
        alerts = ' '.join(self.check(snapshot(status=['redemptionPeriod'])))
        self.assertIn('DROP INCOMING', alerts)
        self.assertNotIn('nameservers:', alerts)
        self.assertNotIn('registrar:', alerts)

    def test_ping_preferences_and_disabled_channel(self):
        db.toggle(self.did, 'ping_available')
        self.check(snapshot())
        self.check(self.failed)
        self.assertNotIn('<@', ' '.join(self.check(snapshot(available=True))))
        db.set_notify(self.did, 'none')
        self.check(self.failed)
        self.assertEqual(self.check(snapshot(status=['pendingDelete'])), [])
        self.assertFalse(json.loads(db.get_domain(self.did)['snapshot'])['error'])

    def test_expiry_warning_dedup_survives_failure(self):
        import datetime as dt
        expiring = snapshot(expiry=(dt.date.today() + dt.timedelta(days=7)).isoformat())
        self.assertIn('expires in', ' '.join(self.check(expiring)))
        self.check(self.failed)
        self.assertNotIn('expires in', ' '.join(self.check(expiring)))


class DbLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {}, clear=True)
        env.start()
        self.addCleanup(env.stop)
        path = patch.object(db, 'DB_PATH', self.tmp.name + '/watcher.db')
        path.start()
        self.addCleanup(path.stop)

    def test_connections_close_and_failed_writes_roll_back(self):
        import sqlite3
        opened, connect = [], sqlite3.connect
        def tracking(*a, **kw):
            opened.append(connect(*a, **kw))
            return opened[-1]
        with patch.object(db.sqlite3, 'connect', tracking):
            db.init()
            did = db.add_domain('example.test')
            db.get_domain(did)
            with self.assertRaises(sqlite3.IntegrityError):
                db.add_domain('example.test')
        self.assertTrue(opened)
        for c in opened:  # a closed connection refuses work
            with self.assertRaises(sqlite3.ProgrammingError):
                c.execute('SELECT 1')
        self.assertEqual(len(db.list_domains()), 1)

    def test_sweep_logs_one_summary_line(self):
        import io, contextlib
        db.init()
        db.add_domain('example.test')
        out = io.StringIO()
        with patch.object(main, 'fetch', return_value=snapshot()), \
                patch.object(main.notify, 'send') as send, contextlib.redirect_stdout(out):
            main.run_all()
        send.assert_not_called()
        self.assertIn('scheduled sweep: 1 checked, 0 errors, 0 alerts', out.getvalue())


if __name__ == '__main__':
    unittest.main()
