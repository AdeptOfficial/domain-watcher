# RDAP lookup failures and retries are not logged

- Created: 2026-10-22
- Status: In progress — implemented locally; DEV verification pending (2026-10-24)
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

[Researched readiness plan](../docs/plans/2026-10-24-recovery-readiness.md)
(2026-10-24): approved by the user. Local diagnostics and regression coverage implemented;
DEV rollout/verification is pending. No snapshot schema or UI error-history change.

## Local verification — 2026-10-24

28 regressions pass. The real-container suite verifies 429 retry/recovery, 503
exhaustion, malformed JSON/shape, real read timeouts and diagnostic redaction.
Runtime logs identify each failed attempt and successful retry. Invalid base URLs
stop startup before database/network access. No timing or schema change.
The required DEV-host test remains pending, so the issue is not yet resolved.
