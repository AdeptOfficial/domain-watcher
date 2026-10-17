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

## 2026-10-17 — v2.1: per-domain pages, gear settings, expiry override
- Every domain on the watchlist is now a link to `/domains/{id}`: RDAP snapshot
  (expiry · registrar · status flags · nameservers · last check), check-now / remove,
  and the alert settings that used to crowd the main table (note, channel, @-pings).
- New: manual **expiry override** (YYYY-MM-DD) for registries that hide expiry via
  RDAP — threshold warnings use it; a real RDAP date always wins (UI says so).
- Global settings moved behind a ⚙ gear in the header (`/settings`).
- Fixed: the EXPIRY column showed `last_check` — now a view-model (`vm()`) renders real
  expiry + days-left with 30/7-day warn colors; last-check lives on the detail page.

## 2026-10-17 — v2.1 polish round (user-driven UX pass, all on dev 231)
- Header: real A emblem as mark + favicon (branding done right), gear 32px, terminal
  prompt moved below the header as a motd line; chrome standard: 56px header, footer
  `20px 24px` with `domain-watcher v{version}` (VERSION const in main.py) + rotating
  quip (8 messages, random per refresh).
- Detail pages act in place via htmx (no history pile-up; 303 fallback without JS);
  saving settings refreshes the snapshot card too (note display was stale).
- Feedback everywhere: busy buttons blink ▋, scanline sweeps the table during checks,
  settle flash on refreshed rows/cards; in-flight checks lock all check buttons
  (add-domain stays open — new domains join the next sweep).
- Watchlist: notes moved off the list (truncated junk) onto the domain page; ON →
  WATCH column, centered; per-row LAST CHECK column (MM-DD HH:MM, full on hover);
  bottom line = last FULL sweep + daily schedule (individual checks no longer move it).
- Resilience: RDAP fetch retries once after 6s, sweeps pace 1.5s/domain — one
  rate-limit burst (rdap.org throttled our IP during testing) can't flag every domain.
- Mistake log: tried a cyan→magenta gradient on the header dot — reads lavender at
  10px; reverted, rule added to the branding doc.
