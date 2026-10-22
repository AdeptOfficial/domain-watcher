# Failed Discord alerts are dropped without a trace

- Created: 2026-10-22
- Status: Open (fix ready on `feature/notify-failure-logging`, not deployed)
- Severity: High. Alerting is the app's whole job, and a broken webhook would hide a
  domain drop.
- From: logging review on 2026-10-22, after the sweep-log deploy.

## Problem

`send_discord` caught every exception and returned `False`, and no caller checked
the result. A deleted webhook (404), a Discord outage (5xx), a rate limit (429) or a
network error lost the alert. Nothing was retried, logged or shown in the UI. Neither
the scheduled sweep nor manual checks would ever reveal it.

## Fix

- `checker.send_discord` makes up to 3 attempts on 5xx, 429 (honouring `retry_after`,
  capped at 30s) and network errors, 5s apart. Any other 4xx fails at once, because a
  bad webhook won't fix itself. Each failure is logged with only the status code or
  error type. The webhook URL is a credential and never appears in logs.
- `notify.send` logs `ALERT NOT DELIVERED (<reason>): N line(s)` and stores
  `notify_failed`. It also covers the case where no webhook is configured.
- The watchlist shows a crimson "discord alert not delivered" line until the next
  successful send clears it.

## Evidence

Six `NotifyFailureTests` cover success clearing the warning, 500 → 429 → success,
404 with no retry, three network errors with no URL in the log, a missing webhook,
and the UI warning. All six fail on the old code. Full suite 17/17 in the
Python 3.12 image with networking disabled.

## Acceptance

Deployed to DEV with health and data preserved, then moved to `resolved/`. A live
failure test (pointing the webhook at a dead URL on DEV) only with the user's go-ahead.
