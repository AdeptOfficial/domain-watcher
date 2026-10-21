# Domain Watcher — agent entry point

Read `README.md`, the newest `DIARY.md` entries, and `git status --short` before
working. Preserve unrelated edits. Global `~/git/AGENTS.md` rules also apply.
Ideas, bugs, issues, features, roadmap: one new file each in `ideas/`, `bugs/`,
`issues/`, `features/`, `roadmap/` (roadmap is public-safe)
(rules and index tool: `~/git/homeserver-apps/AGENTS.md`, read only when filing).

Session state never lives in this file: resume from the newest `DIARY.md` entry and
the handoff it links (`handoffs/`). Mechanics: `ops/README.md`.

Tests: `python -m unittest discover -s tests -v` after installing requirements;
Python 3.12 matches the app image. Use temporary databases and mocked RDAP for
regressions. Never trigger real Discord messages as a test without authorization.
Do not read or print server secrets, environment files or sensitive settings.

Content candidate: `2026-10-17-domain-watcher-recovery` in the shared studio
`docs/content-backlog.md`. Capture deployment changes there; publication follows
the approved content flow.
