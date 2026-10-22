# RDAP lookup failures and retries are not logged

- Created: 2026-10-22
- Status: Open
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
