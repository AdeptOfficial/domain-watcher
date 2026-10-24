# Acceptance test suite

- Created: 2026-10-22
- Status: In progress — implementation approved 2026-10-24; local suite built; DEV verification pending
- Priority: Medium
- From: logging and testing review on 2026-10-22. The 17 tests are unit-level, with
  RDAP mocked inside the process. At capture time, nothing tested the running app end to end.

## Scope

Black-box tests against the real container image, with no internet access:

- A **fake RDAP server** (small HTTP stub with scripted responses: registered,
  status change, NS change, 429, 5xx, 404 → available, pendingDelete) and a
  **fake Discord webhook** that records the payloads it receives (and can return
  404/500 on request).
- A separate test Compose project wires the app to both stubs through env, using a
  throwaway volume.
- Scenarios:
  - add a domain, then see the baseline on the watchlist
  - registered → available sends a ping alert
  - a drop status sends 🚨
  - an NS change to a parking service is flagged
  - an outage then recovery keeps the change (the 2026-10-17 fix, end to end)
  - expiry thresholds fire once
  - webhook 404 shows the UI warning and the log line
  - settings and toggles persist across a container restart
  - `/healthz` works
- One command (`ops/acceptance.sh` or a `make` target) prints pass/fail per scenario.

## Acceptance

- Runs locally and on the DEV host with no outbound network.
- Becomes a required step of the production gate for this app
  (`~/git/workflows/promote-to-prod.md` references it).
- The ops runbook explains how to run it.

## Implementation plan

[Researched readiness plan](../docs/plans/2026-10-24-recovery-readiness.md)
(2026-10-24): scope approved by the user; local implementation and checks are recorded below.

## Local verification — 2026-10-24

Full container suite passed against candidate image
`sha256:e0e0b1241388fdd8888b961137d9c81531e82238660d0e8b302848760c6f0f69`.
28 offline regressions passed (17 existing plus 11 RDAP/configuration checks).
Both intentionally broken recovery variants failed at the expected assertions.
Success, failure and SIGTERM cleanup verified. The first full development run's
warning-persistence assertion was reordered before recovery could clear it.
Usage: [acceptance suite](../docs/features/acceptance-test-suite.md).
Evidence: `~/git/homeserver/notes/2026-10-24-domain-watcher-acceptance-local.md`.
DEV-host execution and exact-image rollout are pending; keep this record In progress.
