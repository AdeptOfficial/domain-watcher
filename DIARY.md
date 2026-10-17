# domain-watcher Diary

## 2026-10-17: v2 shipped — open-sourced and deployed

- v2 app (FastAPI + HTMX + SQLite + APScheduler) built, verified locally end-to-end
  (seed, live RDAP add, toggles, falsified-NS alert fired in Discord, silent re-runs,
  state persisted), published public: **github.com/AdeptOfficial/domain-watcher** (MIT).
- Deployed to dev **LXC 231** @ 10.0.2.31 (`/opt/stacks/domain-watcher`; `.env` holds
  webhook/ping seeds, compose.override adds env passthrough — deploy wipes must preserve
  `.env`, `compose.override.yaml`, and `data/`). Daily check 09:00 CT.
- v1 n8n workflow stays active (daily 09:00) as the safety net for one clean week, then
  gets deactivated at prod cutover. Expect one duplicate baseline from it tomorrow.

## 2026-10-16: Project created (planning only)

- Directory + README with design: daily RDAP checks (status/expiry/NS/registrar diffs)
  against a YAML watchlist, alerts through existing n8n (LXC 131). Two build options
  documented (n8n-native vs script+cron). Nothing implemented yet.
- Context: adept.dev dropped 2026-10-10 and was caught by an investor (Sav.com → atom.com
  parking) while the user had wanted it for years — this tool exists so that never repeats.
