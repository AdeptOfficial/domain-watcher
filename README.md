# domain-watcher

Watches a list of domains you want (or own) and alerts the day anything moves —
so "someone in Canada is sitting on it" becomes a ping instead of a manual check.
Born from losing the `adept.dev` drop to a drop-catcher on 2026-10-10 after
watching the domain for years.

**Status:** NEXT UP — scheduled as the opener for the 2026-10-17 session (option A: n8n-native build first). Watchlist additions since planning: adeptlab.dev (owned, renewal safety net).

## What it checks (per domain, daily)

Via RDAP (`https://rdap.org/domain/<name>`, free, no API key):

| Signal | Why it matters |
|--------|----------------|
| `status` changes | `pendingDelete` / `redemptionPeriod` = the drop is coming — place a backorder NOW |
| Expiry date approaching | Holder may be about to lapse (or you are — works for owned domains too) |
| Nameserver changes | NS flipping to atom.com / afternic / dan.com etc. = just got parked for sale |
| Registrar changes | Transferred — ownership may have changed hands |
| 404 → 200 / 200 → 404 | Domain dropped and became available, or got registered |

State lives in a small JSON/SQLite file: previous snapshot per domain, diffed each run.

## Architecture (two options)

**Option A — pure n8n (recommended first version, zero new infra):**
Schedule trigger (daily) → HTTP Request per watchlist entry → Code node diffs
against stored state (n8n static data or a mounted file) → on change, notify
(email / Discord webhook / ntfy). Lives entirely in the existing n8n (prod LXC 131).

**Option B — standalone script + cron (if logic outgrows n8n):**
Small Python script (`rdap_watch.py`, stdlib only) + SQLite state + cron in a
tiny LXC or inside the n8n host; posts to an n8n webhook which handles routing
the alert. Repo-friendly, testable, versioned here.

Either way, n8n is the alerting layer — the watcher only detects and posts.

## Watchlist (seed)

```yaml
# watchlist.yaml
- domain: adept.dev            # lost to drop-catcher 2026-10-10; parked on atom.com — watch for price drop/re-drop
- domain: adeptproductions.com # dormant since 2005, renewed to 2028; watch for lapse
- domain: adeptproductions.dev # OWNED — watch own expiry/NS as a safety net
- domain: adeptofficial.dev    # available fallback; alert if someone takes it
```

## Future ideas

- Backorder hand-off: when `pendingDelete` hits, link straight to DropCatch/SnapNames
- Availability checks for wishlist names not yet registered (RDAP 404 → "grab it now" alert)
- Weekly digest vs instant alerts, per-domain
