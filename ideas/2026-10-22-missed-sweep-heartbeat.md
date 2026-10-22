# Alert when a daily sweep is missed

- Created: 2026-10-22
- Status: Awaiting user decision (Proposed)
- Priority: Low
- From: logging review on 2026-10-22. A dead scheduler and a quiet day look
  identical, because no Discord message is posted either way.

## Proposal

- **External heartbeat (preferred):** after each sweep, ping a dead-man's-switch URL
  (Healthchecks.io-style or a self-hosted equivalent; could reuse status-tracker).
  The external service alerts when no ping arrives by, say, 10:30. This catches the
  app or the whole host being down, which an in-app check cannot.
- **In-app fallback:** on startup and on each page load, warn if `last_sweep` is
  more than 26 hours old.
- Optional weekly "all quiet, 7/7 sweeps ran" Discord line. Pairs with the quiet
  mode in `2026-10-22-ownership-and-plain-language-alerts.md`.

## Open questions

**For the user:** worth doing? If so, external heartbeat (which service) or only the in-app
stale-sweep warning?


- Which heartbeat service, and does it count as cross-app (would that put it in
  `~/git/homeserver/features/`)?
