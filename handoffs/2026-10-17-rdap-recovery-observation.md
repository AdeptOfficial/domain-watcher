# Handoff: RDAP outage-recovery fix in observation

**Status:** Awaiting user decision (production cutover, after the agent's review)
**Revisit:** 2026-10-25 (owner 2026-10-24: "will do later")

**For the user, at review time:** promote domain-watcher to production and retire the v1 n8n
workflow? The agent runs the review steps below first; elapsed time is not approval.
Since 2026-10-22, DEV runs the code deployed as release `5755649` (before the history
rewrite): connection close, sweep log, Discord retry/failure warning and log rotation.
The review therefore covers two builds.

Active handoff for domain-watcher, moved out of `AGENTS.md` on 2026-10-20 unchanged.
Consume it at the production-readiness review, then move it to `docs/archive/`.

## Current handoff — 2026-10-17

The RDAP outage-recovery fix is **deployed to dev, verified, committed and pushed**.
App fix commit: **`ee76473`** (rewritten history; originally `2ef3f95`). Infrastructure record: **`eb15134`**.

- All nine isolated regression tests passed on the dev host with networking
  disabled. Health/homepage checks passed; six domains and saved settings were
  preserved exactly. SQLite integrity passed.
- Database/source backup and rollback image are retained. See the latest diary
  entry and `~/git/homeserver/configs/dev/services/domain-watcher/README.md` for
  deployment evidence, locations and rollback procedure.
- The daily 09:00 America/Chicago job registered. A **post-deploy scheduled sweep
  was pending at deployment**; the October 23 execution is now verified below.
- **No production release yet.** The planned clean observation week starts
  October 17; earliest review is **October 24, 2026**, not automatic approval.
- The n8n safety net remains unchanged. Do not disable it during observation.
  Its execution history was not queried during deployment; the October 24 audit below verifies recent runs.

## Observation log

- 2026-10-23: first scheduled sweep logged on DEV (build `5755649`), 14:00:10 UTC:
  6 checked, 0 errors, 0 alerts; no `discord send failed` lines.

- 2026-10-24 06:04 UTC (October 24, 01:04 Chicago): read-only audit confirmed DEV health, six enabled domains,
  SQLite integrity, no current lookup errors or persisted notification-failure warning,
  and all 11 application files matching repository release `4682df8`.
  No app container found across production LXCs; production retains the active v1 n8n
  workflow, with successful daily executions October 18–23. These do not prove DEV sweeps.
  October 24’s 09:00 Chicago sweep was not yet due. October 18/19/21 DEV evidence gaps
  remain; no real outage/recovery or Discord delivery was triggered by this audit.
  Evidence: `~/git/homeserver/notes/2026-10-24-domain-watcher-live-audit.md`.

## Next production-readiness review

1. Verify post-deploy daily sweeps completed and inspect sanitized error/recovery
   evidence over the observation period. Record actual results and any gaps. The October 24 UTC audit verified the October 23 sweep; October 24’s 09:00 Chicago run was not yet due.
2. Review the n8n overlap and prepare its retirement for approved production
   cutover, avoiding duplicate monitoring afterward.
3. Report readiness to the user. Explicit production authorization is still
   required; elapsed time, passing tests or this handoff do not authorize release.

