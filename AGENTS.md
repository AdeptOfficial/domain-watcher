# Domain Watcher — agent entry point

Read `README.md`, the newest `DIARY.md` entries, and `git status --short` before
working. Preserve unrelated edits. Global `~/git/AGENTS.md` rules also apply.

## Current handoff — 2026-10-17

The RDAP outage-recovery fix is **deployed to dev, verified, committed and pushed**.
App fix commit: **`2ef3f95`**. Infrastructure record: **`eb15134`**.

- All nine isolated regression tests passed on the dev host with networking
  disabled. Health/homepage checks passed; six domains and saved settings were
  preserved exactly. SQLite integrity passed.
- Database/source backup and rollback image are retained. See the latest diary
  entry and `~/git/homeserver/configs/dev/services/domain-watcher/README.md` for
  deployment evidence, locations and rollback procedure.
- The daily 09:00 America/Chicago job registered. A **post-deploy scheduled sweep
  still needs verification**; startup registration is not execution evidence.
- **No production release yet.** The planned clean observation week starts
  October 17; earliest review is **October 24, 2026**, not automatic approval.
- The n8n safety net remains unchanged. Do not disable it during observation.
  Its current execution history has not been queried as part of this deployment.

## Next production-readiness review

1. Verify post-deploy daily sweeps completed and inspect sanitized error/recovery
   evidence over the observation period. Record actual results and any gaps.
2. Review the n8n overlap and prepare its retirement for approved production
   cutover, avoiding duplicate monitoring afterward.
3. Report readiness to the user. Explicit production authorization is still
   required; elapsed time, passing tests or this handoff do not authorize release.

Tests: `python -m unittest discover -s tests -v` after installing requirements;
Python 3.12 matches the app image. Use temporary databases and mocked RDAP for
regressions. Never trigger real Discord messages as a test without authorization.
Do not read or print server secrets, environment files or sensitive settings.

Content candidate: `2026-10-17-domain-watcher-recovery` in the shared studio
`docs/content-backlog.md`. Capture deployment changes there; publication follows
the approved content flow.
