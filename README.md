# 🛰️ domain-watcher

**Never lose a domain drop by six days again.**

A tiny self-hosted app that watches domains you want (or own) and pings your Discord
the day anything moves — a drop coming, a lapse approaching, nameservers flipping to a
parking service, or a wishlist name suddenly becoming available.

Born from watching `adept.dev` for years, then losing its drop to a drop-catcher — by six days.

## Quickstart

```bash
git clone https://github.com/AdeptOfficial/domain-watcher && cd domain-watcher
docker compose up -d
# open http://localhost — add domains, paste a Discord webhook in settings. Done.
```

One container, one SQLite file in `./data/`. No accounts, no external database, no config
files required — everything is managed in the UI.

## What it alerts on

| Signal | Why you care |
|---|---|
| 🟢 domain became **AVAILABLE** | grab it now (optional @-ping) |
| 🚨 status → `pendingDelete` / `redemptionPeriod` | the drop is coming — place backorders (optional @-ping) |
| 🅿️ nameservers flipped to a parking service | just got listed for sale |
| 🔀 nameserver / 🏷️ registrar / 📅 expiry changes | ownership or intent is moving |
| ⏳ expiry in 30 / 14 / 7 / 1 days | works on **your own** domains too — never lapse |

Checks run daily via [RDAP](https://rdap.org) (free, no API keys). Click any domain for
its own page: the latest RDAP snapshot (expiry, registrar, status flags, nameservers)
plus per-domain alert settings — notify channel (`discord` / `none`), @-ping toggles for
the two act-now alerts, and a manual expiry override for registries that hide expiry
dates (RDAP wins whenever it reports one). Alerts batch into one Discord message per
run; no changes → no noise. Failed lookups retain the last successful snapshot,
so recovery reports changes observed across the outage. For older error records
without a valid baseline, recovery still alerts on availability or a drop status.
Changes that happen and reverse entirely between successful checks cannot be detected.

See [container acceptance tests and diagnostics](docs/features/acceptance-test-suite.md)
for isolated integration checks and lookup failure logs.

## Configuration (all optional)

| Env | Default | Purpose |
|---|---|---|
| `TZ` | UTC | container timezone for the daily check |
| `CHECK_HOUR` | 9 | hour (0–23) of the daily check |
| `WEBHOOK_URL` | — | seed the Discord webhook (editable in UI) |
| `PING_DISCORD_ID` | — | seed the user ID to @-ping (editable in UI) |
| `SEED_WATCHLIST` | — | `1` seeds the author's demo watchlist (you don't want this) |
| `BASIC_AUTH` | — | `user:pass` — set it if you expose the UI beyond your LAN/VPN |
| `DB_PATH` | /data/watcher.db | SQLite location |
| `RDAP_BASE_URL` | https://rdap.org/domain/ | RDAP base URL, ending in `/`; deployment override |

There is **no auth by default** — run it on your LAN or behind your VPN
(e.g. Tailscale), or set `BASIC_AUTH`.

## Development

```bash
pip install -r requirements.txt
DB_PATH=./data/watcher.db uvicorn app.main:app --reload
```

Stack: FastAPI · HTMX · SQLite · APScheduler. The RDAP diff engine lives in
`app/checker.py`; notification channels are pluggable in `app/notify.py` (PRs for
ntfy/Slack/email welcome). `workflow/` holds the original n8n prototype (v1).

### Regression tests

After installing the requirements, run `python -m unittest discover -s tests -v`.
The recovery tests use temporary SQLite databases and mocked RDAP responses;
they do not contact registries or send Discord messages.

## License

MIT — see [LICENSE](LICENSE).

## // codesign

<img src="https://raw.githubusercontent.com/AdeptOfficial/AdeptOfficial/main/assets/codesign-typing.svg" alt="// code-signed by AdepT_X · stay sad and dead <3">

<p align="right"><img src="https://raw.githubusercontent.com/AdeptOfficial/AdeptOfficial/main/assets/codesign.svg" alt="// code-signed by AdepT_X · stay sad and dead <3"></p>
