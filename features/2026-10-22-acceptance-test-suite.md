# Acceptance test suite

- Created: 2026-10-22
- Status: Planned (accepted by the user 2026-10-22)
- Priority: Medium
- From: logging and testing review on 2026-10-22. The 17 tests are unit-level, with
  RDAP mocked inside the process. Nothing tests the running app end to end.

## Scope

Black-box tests against the real container image, with no internet access:

- A **fake RDAP server** (small HTTP stub with scripted responses: registered,
  status change, NS change, 429, 5xx, 404 → available, pendingDelete) and a
  **fake Discord webhook** that records the payloads it receives (and can return
  404/500 on request).
- A Compose test profile wires the app to both stubs through env, using a
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
