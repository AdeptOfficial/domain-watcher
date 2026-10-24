# No record of past sweeps

- Created: 2026-10-22
- Status: Resolved on DEV 2026-10-24. Scheduled summary verified live; code deployed 2026-10-22 as `073c99e` (before history rewrite; current code commit `ba80dce`).
- Severity: Low
- From: preparing the 2026-10-24 observation review. The review has to confirm
  that every daily sweep ran, and the app could not answer that.

## Problem

The app stores only `last_sweep` (the latest run) and each domain's `last_check`, and
it logs nothing per sweep. A sweep with no changes posts nothing to Discord. So a
missed day looks exactly like a quiet day.

Evidence from DEV on 2026-10-22 (read-only): the container has been up since
2026-10-17 21:05 CT with 0 restarts, the scheduler is registered for 09:00
America/Chicago, and `last_sweep` is `2026-10-22T09:00:11` with all six domains
checked. Discord alerts prove the 10-20 and 10-22 sweeps ran. 10-18, 10-19 and 10-21
cannot be proven from the app.

## Fix

`run_all` prints one line per sweep to the container log:
`[domain-watcher] scheduled sweep: N checked, E errors, A alerts`
(`manual` for UI-triggered sweeps). Covered by
`DbLifecycleTests.test_sweep_logs_one_summary_line`.

## Next steps / acceptance

- After deploying, `docker logs domain-watcher | grep sweep:` shows one line per day.
- Later, optionally: keep a small `sweeps` table and show recent sweeps in the UI,
  or ping a heartbeat (healthchecks-style) so a missed sweep raises an alert itself.

## Verification — 2026-10-24 UTC

Read-only live audit found the October 23 14:00:10 UTC scheduled summary:
6 checked, 0 errors, 0 alerts. SQLite last_sweep and all six last_check timestamps
confirm the same run. The October 24 run was not yet due at audit time. This resolves
missing logging going forward; it cannot reconstruct the October 18/19/21 DEV runs.
Evidence: `~/git/homeserver/notes/2026-10-24-domain-watcher-live-audit.md`.
