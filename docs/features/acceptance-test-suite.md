# Container acceptance tests and RDAP diagnostics

The suite exercises the normal Domain Watcher image through its HTTP interface using
scripted RDAP and Discord peers. It uses disposable data and an isolated Docker network.

## Run locally

Requirements: Python 3 on the workstation, Docker Engine and Docker Compose v2 or later
on the default Docker context. Build the image first (dependencies may need internet):

```bash
docker build -t domain-watcher:candidate .
docker run --rm --network none -v "$PWD/tests:/tests:ro" \
  domain-watcher:candidate python -m unittest discover -s /tests -v
ops/acceptance.sh domain-watcher:candidate
```

The acceptance command requires an already built local image; it does not build or pull.
It prints the candidate image identifier, PASS/FAIL groups and cleanup result. Expect a
few minutes, including normal retry delays and a real 20-second read timeout on each
RDAP attempt. A nonzero exit code means failure, including failures during cleanup.
`--core-only` runs the recovery/restart checks for targeted regression investigations;
it does not satisfy the full acceptance gate.

The harness always selects its standalone Compose file and a random project name.
Its network has `internal: true`; no host ports or Docker socket are published/mounted.
Only harness files are mounted read-only; app code comes from the candidate image.
Settings contain a fake webhook and example ping ID. The data volume belongs to that
test run; cleanup removes it on success, failure, Ctrl+C or SIGTERM. Force-killing the
orchestrator or Docker daemon can prevent cleanup; use the exact printed project name
with the test Compose file to remove that run, never the live project.

The driver does not inherit workstation proxy or Compose variables. Runtime network
checks verify that app and stub have only the internal network and no published ports.

## Coverage

Tests check baseline rendering, availability/drop/parking/registrar/expiry changes,
repeated failures and recovery across a real app restart, legacy/initial failure
fallback, RDAP retries, malformed responses and read timeouts, expiry deduplication,
ping/channel/enable preferences, saved settings, Discord retries/failure warnings,
bulk sweeps, health, redacted logs and scheduler registration after restart.

The stub fails unexpected or unconsumed requests. Assertions distinguish webhook
attempts from messages accepted by the fake Discord peer. Deliberately broken recovery
and baseline variants were rejected during local verification.

This proves the container's HTTP, persistence and notification integration with controlled
peers. It does not prove real Discord receipt, registry semantics or daily scheduler
execution. A scheduled sweep log is still needed for live observation. Exhausted Discord
retries persist a warning; the lost alert is not queued or resent on restart. A later
successful alert clears the warning.

## RDAP configuration and logs

`RDAP_BASE_URL` defaults to `https://rdap.org/domain/`. Deployment overrides must be an
HTTP(S) base ending in `/`, without credentials, query or fragment. Invalid settings
fail app startup. The test harness supplies its private RDAP peer. Normal deployments
need no override; never point a real watchlist at a fixture server.

Each failed lookup attempt logs the JSON-escaped domain, attempt out of two, HTTP status
or exception category/class, and whether another attempt follows. Successful retries
log recovery. Bodies, exception messages and full request/webhook URLs are excluded.
The existing one retry, six-second delay and 20-second HTTP timeout are preserved.
A 404 continues to mean available under the current RDAP interpretation.

## DEV and production

Load the exact tested image on DEV and check its identifier; rerun the full isolated
suite with the same source revision's harness. Keep its test data separate from the
live watchlist. Instance state and backups live in
`~/git/homeserver/configs/dev/services/domain-watcher/README.md`.

The full suite is required by `~/git/workflows/promote-to-prod.md` for Domain Watcher.
Local success is one prerequisite; DEV rollout, daily observation and explicit production
approval remain separate. No database migration is introduced by these diagnostics.
