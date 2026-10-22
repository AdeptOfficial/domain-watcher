# SQLite connections are never closed

- Created: 2026-10-22
- Status: Resolved 2026-10-22, fixed on DEV (release `073c99e`)
- Severity: Low
- From: the 2026-10-17 diary noted ResourceWarnings during a Python 3.14 test run and
  called it a separate follow-up, but no record was filed until now.

## Problem

`db.conn()` returned a bare `sqlite3.Connection`, and every caller used
`with conn() as c:`. sqlite3's context manager only commits or rolls back the
transaction. It does not close the connection, so every DB call (several per page
view and per domain check) left a connection open until garbage collection freed it.
CPython frees them quickly, so nothing has failed in practice. It is still an open
file handle per call, and Python 3.13+ warns about it.

## Fix

`conn()` becomes a `contextlib.contextmanager`: it opens the connection, commits on
success, rolls back on error and always closes. No caller had to change.

## Evidence

- Regression test `DbLifecycleTests.test_connections_close_and_failed_writes_roll_back`
  tracks every connection opened through `init`, `add_domain`, `get_domain` and a
  failed duplicate insert, and asserts that each one is closed and that the failed
  write rolled back. It **fails on the old `db.py`** and passes with the fix.
- Full suite 11/11 in the Python 3.12 app image with networking disabled (2026-10-22).

## Next steps / acceptance

- Deployed to DEV 2026-10-22. `/healthz` ok with 6 domains, homepage 200, SQLite
  integrity ok, and the domain and settings fingerprints match the pre-deploy backup.
  Suite 11/11 on the dev host with networking disabled. Production is a separate,
  user-gated step.
