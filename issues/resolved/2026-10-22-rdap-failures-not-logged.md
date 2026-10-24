# RDAP lookup failures and retries are not logged

- Created: 2026-10-22
- Status: Resolved on DEV 2026-10-24, release `832726f`
- Severity: Low
- From: logging review on 2026-10-22.

## Problem

`checker._fetch_once` turns any HTTP error or exception into
`error: True`, and `fetch` retries once after 6s. Neither step logs anything. The
UI and alerts only say "RDAP lookups failing". Whether the cause was rate limiting
(429), a registry outage (5xx), a timeout or a parse error is lost. That is exactly
the evidence the observation review needs to judge whether failures were transient.

## Next steps

- Log one line per failed attempt: domain, attempt, HTTP status or error type.
- Optionally store the last error reason in the snapshot and show it on the
  domain page.
- Tests: mocked 429 then success logs a retry; a persistent timeout logs both attempts.

## Acceptance

A forced failure on DEV (mocked, not by hammering rdap.org) shows its reason in
`docker logs`.

## Implementation plan

[Researched readiness plan](../../docs/plans/2026-10-24-recovery-readiness.md)
(2026-10-24): approved by the user. Local diagnostics and regression coverage implemented;
DEV rollout/verification passed (see below). No snapshot schema or UI error-history change.

## Local verification — 2026-10-24

28 regressions pass. The real-container suite verifies 429 retry/recovery, 503
exhaustion, malformed JSON/shape, real read timeouts and diagnostic redaction.
Runtime logs identify each failed attempt and successful retry. Invalid base URLs
stop startup before database/network access. No timing or schema change.
The required DEV-host verification passed as recorded below.

## Resolution — 2026-10-24 DEV

Full isolated real-container acceptance on DEV verified the RDAP failure/retry
diagnostic lines for 429, 503, malformed JSON/shape and real read timeouts, with
redaction checks. The exact tested image was deployed as release `832726f`;
28 regressions also passed offline on DEV. Health/data preservation checks passed.
No failures were forced against real registries and no live notification was sent.
Evidence: `~/git/homeserver/notes/2026-10-24-domain-watcher-diagnostics-dev.md`.
