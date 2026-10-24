# RDAP recovery readiness: implementation and verification plan

- Created: 2026-10-24
- Status: Awaiting user decision
- Decision: approve implementation and local isolated tests for the scope below?
- Sources: [acceptance feature](../../features/2026-10-22-acceptance-test-suite.md),
  [logging issue](../../issues/2026-10-22-rdap-failures-not-logged.md),
  [observation handoff](../../handoffs/2026-10-17-rdap-recovery-observation.md).
- Research only. Application code and deployments are unchanged.

## Current evidence and gaps

Live audit confirms the v2 app on DEV, six enabled domains, healthy SQLite, and all
11 application files matching release `4682df8`. October 23's scheduled sweep checked
six domains with zero errors/alerts. Production retains the separate v1 n8n workflow.
Audit evidence lives in `~/git/homeserver/notes/2026-10-24-domain-watcher-live-audit.md`.

The 17 existing tests exercise SQLite and application functions with mocked RDAP or
HTTP calls. They do not test the actual container's HTTP parsing, forms, persistence
across a process restart, and outgoing notification together. `_fetch_once` currently
collapses HTTP failures and exceptions into `error: True`, losing the cause.

The current settings page explicitly says changing the daily hour applies after a
restart; persistence checks should verify that documented contract. The notification
code retries within a send, but has no durable queue: after retries exhaust, a warning
persists and the alert is lost. Tests must describe that limit accurately.

## 1. Add RDAP failure diagnostics

Change `app/checker.py` and add focused regression tests:

- One flushed log line per failed attempt: safely escaped domain, attempt out of two,
  HTTP status or exception type, and whether another attempt follows.
- Distinguish HTTP failures, connection/read timeouts, transport failures, malformed
  JSON and response parsing failures. Use fixed categories and exception class names;
  never print response bodies, full request URLs or exception messages.
- Log recovery after a successful retry, so a transient failure can be distinguished
  from an exhausted lookup. A 404 retains its existing availability behavior.
- Preserve the existing one retry, six-second delay, 20-second HTTP timeout and
  snapshot/diff behavior. No schema change or UI error-history feature in this scope.
- Tests: 429 then success; persistent timeout (both attempts); 5xx exhaustion;
  malformed response; availability 404; log redaction/control-character escaping.

HTTPX documents separate transport/timeout exception classes, which support these
categories without exposing exception messages. Its timeout limits network operations,
not an overall sweep deadline. [Exceptions](https://www.python-httpx.org/exceptions/),
[timeouts](https://www.python-httpx.org/advanced/timeouts/).

## 2. Build a separate container acceptance harness

Proposed files: `ops/acceptance.sh`, `tests/acceptance/compose.yaml`, a small threaded
fake-service server, and an HTTP scenario runner under `tests/acceptance/`.

- Run the normal app image with its normal entry point; tests interact through its
  existing HTTP forms/routes. No application source mount or in-process RDAP mocking.
- Add one deployment-level `RDAP_BASE_URL` setting, defaulting to
  `https://rdap.org/domain/`. The harness sets it to the fake RDAP service. Validate
  the configured base and construct the domain path safely. Ordinary deployments
  retain the current default. Document the setting and test that default explicitly.
- Use the existing webhook setting to target fake Discord. Fake domains use `.test`
  and ping IDs use the approved example value. Fixtures contain no live settings.
- Use a standalone Compose file, explicit unique project name, temporary named data
  volume and `internal: true` network. App, stubs and runner share only that network.
  No published ports, host networking, live-data mounts, inherited credential env
  files or Docker socket mounts. The workstation shell controls restarts/cleanup.
- Explicitly select the test Compose file and an empty environment file; use a small
  allowlist of runner inputs so ambient Compose variables cannot select the live stack.
  Verify all test services are attached only to the isolated network before scenarios.
- Build/pull dependencies beforehand. Runtime tests run without internet access;
  image preparation may need internet. Load the same candidate image on DEV and
  compare its image ID rather than rebuilding from floating dependencies there.
- Use health readiness checks, bounded waits, explicit expected request counts and
  per-scenario PASS/FAIL output. Unexpected requests to a stub fail the scenario.
- Keep normal retry timing in container scenarios. A deliberate read timeout will
  cost roughly 46 seconds for two attempts and a delay; allow bounded time for it.
- Clean up only the uniquely named test project and its disposable volume, including
  on failure/interruption. Preserve sanitized test diagnostics before cleanup.

Docker profiles control which services start, but unprofiled services still start by
default. A separate file avoids inheriting the app's fixed container name, port and
live data path. This is a deliberate refinement of the feature's original profile
proposal. [Profiles](https://docs.docker.com/compose/how-tos/profiles/).

Docker documents project names for environment separation and `internal: true` for
externally isolated networking. These support the proposed harness boundaries.
[Project names](https://docs.docker.com/compose/how-tos/project-name/),
[networks](https://docs.docker.com/reference/compose-file/networks/).

Use explicit readiness checks: dependency startup alone does not establish readiness.
[Startup order](https://docs.docker.com/compose/how-tos/startup-order/).
HTTPX honors proxy variables by default; avoid forwarding workstation proxy variables
into these test containers. [Environment variables](https://www.python-httpx.org/environment_variables/).

## 3. Acceptance scenarios and required assertions

| Scenario | Required evidence |
|---|---|
| Add a registered domain | Snapshot rendered in watchlist/detail; no change alert for baseline |
| Registered to available | Fake RDAP 404; one accepted webhook payload with availability and configured ping; repeat is quiet |
| Drop / parking / registrar / expiry changes | Correct alert text and ping behavior; unchanged follow-up is quiet |
| Repeated outage, restart, then available | Last successful baseline survives real container restart; recovery plus availability; no duplicate on next check |
| Outage then drop/other changes | Recovery reports changes against the saved successful snapshot |
| First lookup fails, then recovery | Available/drop alerted; no fabricated registrar/nameserver differences |
| 429 then success; exhausted 5xx; timeout; malformed JSON | Expected attempt counts and sanitized diagnostic lines; failed lookups retain baseline |
| Expiry thresholds | Warnings deduplicated across repeated checks, outages and restart; date-relative fixtures |
| Preferences | Ping toggles, notify=none and disabled domains behave as documented; disabled domains skipped by bulk sweep |
| Discord 500/429 then success | Retry counts match; one accepted message, no undelivered warning |
| Discord 404 / exhausted retries | Persistent visible warning and redacted log; restart retains warning; a subsequent successful alert clears it |
| Settings and restart | Note, expiry override, toggles, fake webhook and daily hour persist; hour takes effect after restart |
| Bulk check and health | `/check` exercises real sweep and summary log; `/healthz` reports expected domain count |

A manual `/check` is not proof that the scheduler fires. Keep scheduler registration
checks distinct from actual daily-execution evidence. Fast unit tests may inspect cron
configuration, but only a scheduled sweep log counts toward the live observation period.
APScheduler documents timezone configuration and job triggers separately from execution.
[APScheduler 3.x guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html).

Validate that the core outage scenario catches the original defect: use a disposable
candidate variant restoring the old error-only recovery comparison and confirm that
scenario fails. Also disable baseline preservation alone and verify that the
registrar/nameserver recovery scenario fails, since legacy availability fallback can
otherwise conceal that mutation.
The variant never becomes a deployment candidate. Tests report accepted webhook messages
separately from attempted HTTP sends; retries are not duplicate accepted delivery.

## 4. Deliverables after implementation approval

1. Integrate the existing documentation audit through the feature-to-release workflow;
   develop the two changes on a fresh feature branch from release.
2. Run the existing regressions, new diagnostic regressions and full container suite
   locally. Record exact image/source identifiers and failures or omissions.
3. Document the one-command suite in the ops runbook and feature usage doc. Add the
   Domain Watcher-specific acceptance requirement to the shared production gate.
4. Update the feature/issue records using actual verification status, the handoff and
   diary. Capture the result in the existing recovery content-backlog candidate.
5. Present the tested candidate and backup/rollback procedure for DEV rollout approval.

Approval requested here covers implementation and local tests. DEV rollout is a later
concrete review step; the user requested a plan before work. Production cutover and n8n
retirement retain their separate explicit authorization gate.

## 5. DEV verification and production-readiness recommendation

After DEV rollout approval: run the isolated suite on the DEV host with its own test
volume, back up the live SQLite database/source, retain the previous image, deploy the
exact tested candidate, and verify health, hashes, integrity and preservation of saved
domains/settings using secret-safe comparisons. No schema migration is planned.

For the clean observation week, recommend seven consecutive documented scheduled daily
sweeps on the final runtime build. This is a proposed acceptance criterion, not evidence
already collected. Documentation-only edits do not restart observation. Upstream transient
errors are acceptable when retries/recovery behave correctly; missed runs, unresolved
lookup failures or undelivered alerts require investigation before recommending cutover.
The October 25 revisit is a review date, not an automatic readiness deadline.

At review, distinguish synthetic outage/delivery coverage from actual daily operation.
Real domain drops cannot be guaranteed during observation. Report remaining gaps and
recommend readiness only when the accepted criteria pass. Prepare a production cutover
that avoids overlapping v2 schedules and retires v1 n8n at the authorized point; define
rollback of both app and monitoring ownership before asking for production approval.
