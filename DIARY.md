## 2026-10-24 UTC: Domain Watcher session wrapped

Recovery diagnostics and acceptance release `832726f` are verified on DEV: full
isolated suite and 28 regressions pass; six domains/settings preserved, health,
assets, SQLite integrity and application hashes verified. Backup/rollback are in
the private DEV service README. Active resume point:
[observation handoff](handoffs/2026-10-17-rdap-recovery-observation.md).
The recovery content candidate stays deferred for a future combined update.
No immediate implementation remains for the agreed recovery scope. Ownership/plain
alerts revisit October 25; optional missed-sweep heartbeat revisits November 1.
Production/n8n cutover remains separately owner-gated. Changes committed locally;
no push requested. Private records remain on homeserver `feature/domain-watcher-live-audit`;
content capture is on studio `feature/domain-watcher-acceptance-backlog` for review.
Next: verify the first scheduled 09:00 Chicago sweep, collect seven daily summaries,
and review interim progress October 25; earliest seventh run October 30 if all pass.

## 2026-10-24 UTC: Diagnostics and acceptance release verified on DEV

User-approved release `832726f` deployed at 06:32 UTC using the exact locally tested
image, without rebuilding. All 52 source files matched the transferred manifest;
28 offline regressions and the full isolated acceptance suite passed on DEV first.
After rollout: all 11 running app files and served CSS/emblem match; health and
homepage pass through the DEV hostname; SQLite integrity ok, six enabled domains
and settings fingerprints unchanged; environment/override metadata unchanged.
Daily 09:00 America/Chicago registration logged. No live sweep or Discord message
triggered; production v1 n8n unchanged. Consistent private backup and retained image
verified; instance paths are in the homeserver DEV service README. Evidence:
`~/git/homeserver/notes/2026-10-24-domain-watcher-diagnostics-dev.md`.
Moved the suite to features/implemented and RDAP diagnostics issue to issues/resolved;
updated usage/plan/handoff. Existing content candidate captures this DEV stage.
Next: verify October 24's 09:00 sweep and collect seven documented daily sweeps.
October 25 is interim review; earliest seventh run October 30 if all complete.
Production cutover/n8n retirement remain separately owner-gated.

## 2026-10-24 UTC: RDAP diagnostics and container acceptance pass locally

Implemented safe per-attempt RDAP diagnostics, retry-recovery logs and validated
`RDAP_BASE_URL` override; default endpoint, retry timing and schema retained.
New standalone acceptance harness uses the normal image, fake RDAP/Discord peers,
internal-only network, disposable data and real app restart. Full suite passes;
28 offline regressions pass. Two deliberately broken variants fail as intended;
success/failure/SIGTERM cleanup verified. An initial harness assertion-ordering
failure was corrected; no application warning-persistence defect was found.
Candidate `domain-watcher:recovery-acceptance-20261024`, image identifier
`sha256:e0e0b1241388fdd8888b961137d9c81531e82238660d0e8b302848760c6f0f69`.
Usage: `docs/features/acceptance-test-suite.md`. Private evidence:
`~/git/homeserver/notes/2026-10-24-domain-watcher-acceptance-local.md`.
Existing DEV and production n8n remain unchanged. The shared production gate now
requires the full suite locally and on DEV. Feature/issue remain In progress until
DEV verification; no real Discord message or domain drop was tested.
Next: request exact-image DEV rollout approval after isolated DEV suite, consistent
backup and retained rollback image; then collect seven documented daily sweeps.
Capture: update deferred candidate `2026-10-17-domain-watcher-recovery` with local stage.

## 2026-10-24 UTC: Recovery readiness plan researched

Reviewed the running-app test gaps and official Docker, HTTPX and APScheduler docs.
Plan: `docs/plans/2026-10-24-recovery-readiness.md` covers safe RDAP diagnostics,
a separate isolated container suite, restart/recovery and notification scenarios,
exact-image DEV verification and proposed seven-day scheduled observation evidence.
Research/documentation only; application code and deployments unchanged.
Next: present the plan for implementation/local-test approval as the user requested;
DEV rollout and production cutover remain later review steps.

## 2026-10-24 UTC: Live observation and deployment documentation reconciled

Read-only audit confirms DEV-only v2 app, all 11 application files matching release
`4682df8`, health/homepage 200, six enabled domains and SQLite integrity ok. October 23
scheduled sweep: 6 checked / 0 errors / 0 alerts; October 24 run not yet due. Production
v1 n8n remains active with successful October 18–23 executions. No runtime changes.
Corrected ops health path, resolved sweep-log issue, updated observation handoff.
Evidence: `~/git/homeserver/notes/2026-10-24-domain-watcher-live-audit.md`.
Next: review subsequent DEV sweeps and remaining readiness gaps on October 25;
production cutover and n8n retirement still require explicit owner authorization.

## 2026-10-22: Public history rewritten to remove a personal identifier

The owner's Discord user ID had survived in the history of `workflow/domain-watcher.n8n.json` (v1, commit from
2026-10-17) as a `<@…>` mention. With the user's approval the history was rewritten (that value only → `__PING_ID__`;
current files unchanged) and force-pushed. Branch protection was relaxed and restored. Commit hashes changed: main
`cca5a2d`, release `0b0ad84`, tag `v0.0.1` `964dc02`. Anyone with an old clone should re-clone. Record:
homeserver `issues/security/resolved/2026-10-22-discord-id-in-public-git-history.md`.

## 2026-10-22: Missed-sweep idea gets a revisit date

Wrap-up: the user set `Revisit: 2026-11-01` on `ideas/2026-10-22-missed-sweep-heartbeat.md`.
Next: unchanged from the entry below.

## 2026-10-22: Decisions tagged for the user

Both ideas and the observation handoff now carry `Status: Awaiting user decision` (the ideas
and the handoff revisit 2026-10-24), so `~/git/tools/awaiting-decisions.sh` surfaces them at
session start and wrap-up. No source change.

## 2026-10-22: Notify-failure fix and log rotation deployed to DEV

- User-approved DEV deploy of release `5755649` (same procedure; `.env`, override and
  data kept). Backup: `/opt/backups/domain-watcher-before-notify-20261022`, integrity
  ok. Rollback image: `domain-watcher:before-notify-20261022`.
- Verified: `/healthz` ok with 6 domains, homepage 200 with no undelivered warning,
  integrity ok, fingerprints unchanged, 0 restarts, log config json-file 5m × 3,
  suite 17/17 on the host offline. No sweep and no Discord message triggered.
- Resolved the silent-drop bug and the unbounded-logs issue. Content candidate
  `2026-10-17-domain-watcher-recovery` updated on the studio branch
  `feature/backlog-domain-watcher-20261022` (not merged, because studio `release` holds
  another session's unpushed work).

## 2026-10-22: Discord delivery failures retried and surfaced (branch only)

- Logging and testing review filed: bug `2026-10-22-failed-discord-alerts-dropped-silently`,
  issues `rdap-failures-not-logged` and `container-logs-unbounded`, feature
  `acceptance-test-suite` (Planned, accepted by the user) and idea `missed-sweep-heartbeat`.
- Fixed the bug: retries on 5xx, 429 and network errors; redacted log lines; a
  persisted `notify_failed` warning shown on the watchlist. Six new tests, all failing
  on the old code. 17/17 in the Python 3.12 image, offline. On
  `feature/notify-failure-logging`; not on release and not deployed.

## 2026-10-22: Connection-close and sweep-log fix deployed to DEV

- User-approved DEV deploy of release `073c99e` using the documented rsync procedure;
  `.env`, the Compose override and `data/` were retained.
- Before deploying: an online SQLite backup plus source in
  `/opt/backups/domain-watcher-before-dbclose-20261022` (owner-only, integrity ok)
  and rollback image `domain-watcher:before-dbclose-20261022`.
- Verified: `/healthz` ok with 6 domains, homepage 200, integrity ok, domain and
  settings fingerprints identical before and after, 0 restarts, 09:00 job
  registered, suite 11/11 on the host with networking disabled. No manual sweep and
  no Discord message triggered.
- The observation week now spans two builds; the 10-24 review covers both. The first
  `sweep:` log line is expected 2026-10-23 09:00. Production and n8n unchanged.

## 2026-10-22: Connection-close fix and sweep log line (branch only)

- Filed `issues/2026-10-22-sqlite-connections-never-closed.md` (the 10-17 follow-up)
  and `issues/2026-10-22-no-sweep-history.md`.
- `db.conn()` now closes every connection; `run_all` logs one summary line per sweep.
  Two new tests; the connection test fails on the old code. 11/11 pass in the
  Python 3.12 image with networking disabled. On `feature/db-close-and-sweep-log`,
  not merged to release and not deployed.
- DEV evidence (read-only): up since 2026-10-17 21:05 CT, 0 restarts, last sweep
  2026-10-22T09:00:11 with six domains. The 10-20 and 10-22 sweeps are proven by
  Discord. 10-18, 10-19 and 10-21 cannot be proven (that is the second issue).
  Observed: adept.dev now expires 2035-10-10, and adept.studio expires 2026-11-09.

## 2026-10-22: Idea filed, ownership and plain-language alerts

`ideas/2026-10-22-ownership-and-plain-language-alerts.md` (Proposed). Prompted by the
user: the transfer-period and add-period alerts after the move to one registrar were
harmless but read as alarming. It proposes Mine/Watching roles, TXT verification,
four alert levels, and plain what / normal? / what-to-do text. No source change.

## 2026-10-20: Handoff moved out of the entry point

The 2026-10-17 RDAP recovery handoff and the production-readiness review steps
moved unchanged to `handoffs/2026-10-17-rdap-recovery-observation.md`; `AGENTS.md`
keeps rules and pointers only. No source or runtime change.
Next: at the earliest review date (2026-10-24) verify the daily sweeps ran and
report readiness; production still needs explicit authorization.

## 2026-10-20: ops/README.md runbook added

Portable runbook (public repo: placeholders only): runtime shape, run anywhere,
Database section, tests, DEV deploy outline pointing at the private homeserver
README, rollback and verification. Documentation only.

## 2026-10-20: Public-repo scrub

The compose example line showed the owner's real Discord user ID; it is now an
example value and the seed is set through `.env`. Diary placeholders applied.
gitleaks pre-commit hook installed. Nothing deployed.

## 2026-10-20: ideas/ and roadmap/ added to the standard layout

Added `ideas/` (feature entry stage; accepted → `features/`, declined →
`ideas/declined/`) and `roadmap/` (public-safe milestones that feed the AdepT
platform and studio pages; `roadmap/shipped/` when released). Indexes generated by
`~/git/homeserver-apps/tools/tracker-index.py`; empty lifecycle folders hold a
`.gitkeep`. No source or runtime change.

## 2026-10-20: Standard tracker layout added

Added `bugs/` (with `resolved/`), `issues/` (with `resolved/`) and `features/` (with
`implemented/`), each with a generated index README, per the shared rules in
`~/git/homeserver-apps/AGENTS.md`. No records yet. Entry point updated with a one-line
pointer. No source or runtime change.

# domain-watcher Diary

## 2026-10-17: Explicit next-agent production handoff

- Added `AGENTS.md` as the startup entry point with verified dev evidence, pushed
  fix `2ef3f95`, pending scheduled-sweep verification and the October 24 earliest
  observation review. Production approval remains separate; n8n stays unchanged
  during observation. Review steps and rollback documentation are linked there.

## 2026-10-17: RDAP recovery fix verified on DEV

- Deployed the locally tested `domain-watcher:recovery-test` image to DEV LXC <id>,
  aliased as `domain-watcher:latest`; existing Compose/environment retained.
- Nine regression tests passed again on the dev host in an isolated container
  with networking disabled. Homepage HTTP 200, health reports six domains, SQLite
  integrity passes. All domain rows and saved settings match the pre-deploy backup.
- Startup registers the daily 09:00 America/Chicago job. Last completed sweep is
  2026-10-17T14:15:10; a post-deploy scheduled sweep has not yet been observed.
  No manual live scan or Discord message was triggered.
- Stopped-app backup: `/opt/backups/domain-watcher-before-recovery-20261017`
  (owner-only), containing data and source. Rollback image:
  `domain-watcher:before-recovery-20261017`. No database migration required.
- Production remains unchanged. The documented one-clean-week n8n overlap begins
  October 17; review no earlier than October 24, then retire it at approved cutover.

Older entries: `docs/archive/diary/` (rolled by `tools/diary-roll.py`; read the newest three entries unless investigating history).
