"""RDAP request diagnostics and deployment URL regressions; no network."""
import contextlib
import io
import os
import unittest
from unittest.mock import patch

import httpx
from app import checker


class RdapTests(unittest.TestCase):
    def setUp(self):
        p = patch.dict(os.environ, {}, clear=True)
        p.start()
        self.addCleanup(p.stop)

    def fetch(self, *results, domain='example.test'):
        out = io.StringIO()
        with patch.object(checker.httpx, 'get', side_effect=results) as get, \
                patch.object(checker.time, 'sleep') as sleep, contextlib.redirect_stdout(out):
            snap = checker.fetch(domain)
        return snap, out.getvalue(), get, sleep

    def test_default_endpoint_and_timeout(self):
        snap, log, get, sleep = self.fetch(httpx.Response(200, json={}))
        self.assertFalse(snap['error'])
        self.assertEqual(get.call_args.args[0], 'https://rdap.org/domain/example.test')
        self.assertEqual(get.call_args.kwargs['timeout'], 20)
        self.assertEqual(log, '')
        sleep.assert_not_called()

    def test_rate_limit_then_success_logs_recovery(self):
        snap, log, get, sleep = self.fetch(httpx.Response(429), httpx.Response(200, json={}))
        self.assertFalse(snap['error'])
        self.assertIn('attempt=1/2 reason=HTTP 429 retry=yes', log)
        self.assertIn('rdap retry recovered:', log)
        self.assertEqual(get.call_count, 2)
        sleep.assert_called_once_with(6)

    def test_timeout_both_attempts_without_exception_message(self):
        secret = 'https://private.example.test/token-secret'
        snap, log, get, _ = self.fetch(httpx.ReadTimeout(secret), httpx.ReadTimeout(secret))
        self.assertTrue(snap['error'])
        self.assertEqual(get.call_count, 2)
        self.assertIn('attempt=1/2 reason=request ReadTimeout retry=yes', log)
        self.assertIn('attempt=2/2 reason=request ReadTimeout retry=no', log)
        self.assertNotIn(secret, log)

    def test_connection_error_class(self):
        _, log, _, _ = self.fetch(httpx.ConnectError('sensitive'), httpx.ConnectError('sensitive'))
        self.assertIn('request ConnectError', log)
        self.assertNotIn('sensitive', log)

    def test_persistent_server_errors(self):
        snap, log, _, _ = self.fetch(httpx.Response(503), httpx.Response(503))
        self.assertTrue(snap['error'])
        self.assertEqual(log.count('HTTP 503'), 2)
        self.assertNotIn('recovered', log)

    def test_malformed_json_and_shape(self):
        for response, category in [(httpx.Response(200, content=b'secret-body'), 'json JSONDecodeError'),
                                   (httpx.Response(200, json=[]), 'parse AttributeError')]:
            with self.subTest(category=category):
                snap, log, _, _ = self.fetch(response, response)
                self.assertTrue(snap['error'])
                self.assertIn(category, log)
                self.assertNotIn('secret-body', log)

    def test_404_is_availability_without_failure(self):
        snap, log, get, _ = self.fetch(httpx.Response(404))
        self.assertTrue(snap['available'])
        self.assertFalse(snap['error'])
        self.assertEqual(get.call_count, 1)
        self.assertEqual(log, '')

    def test_domain_log_cannot_inject_lines(self):
        _, log, _, _ = self.fetch(httpx.Response(500), httpx.Response(500), domain='bad\n\x1b.test')
        self.assertEqual(len(log.splitlines()), 2)
        self.assertIn(r'bad\n\u001b.test', log)

    def test_endpoint_override_and_encoded_domain(self):
        with patch.dict(os.environ, {'RDAP_BASE_URL': 'http://rdap:8080/domain/'}):
            self.assertEqual(checker.rdap_url('a/b?x.test'), 'http://rdap:8080/domain/a%2Fb%3Fx.test')

    def test_invalid_endpoint_is_rejected_without_network(self):
        for value in ['file:///tmp/', 'http://', 'http://user:pass@rdap/',
                      'http://rdap/no-slash', 'http://rdap/?key=x/', 'http://rdap/#x/', 'http://rdap:bad/']:
            with self.subTest(value=value), patch.dict(os.environ, {'RDAP_BASE_URL': value}):
                with self.assertRaises(ValueError):
                    checker.rdap_url('example.test')

    def test_invalid_endpoint_stops_startup_before_database_or_network(self):
        from fastapi.testclient import TestClient
        from app import main
        with patch.dict(os.environ, {'RDAP_BASE_URL': 'file:///tmp/'}), \
                patch.object(main.db, 'init') as init, patch.object(checker.httpx, 'get') as get:
            with self.assertRaises(ValueError):
                with TestClient(main.app):
                    pass
            init.assert_not_called()
            get.assert_not_called()
