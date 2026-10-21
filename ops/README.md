# Domain Watcher — operations runbook

Portable instructions. This repo is public: no hosts, addresses or LXC ids here.
Homelab instance state lives in `~/git/homeserver/configs/dev/services/domain-watcher/README.md`;
the promotion gate is `~/git/workflows/promote-to-prod.md`. Facts from `compose.yaml`,
`Dockerfile` and `README.md`.

## Runtime shape

| Item | Value |
|------|-------|
| Process | `uvicorn app.main:app` on container port 80, published on host port 80 |
| Image | `python:3.12-slim`, single stage |
| Data | SQLite at `/data/watcher.db` (`DB_PATH`), bind-mounted from `./data` |
| Config | optional seeds via environment (`WEBHOOK_URL`, `PING_DISCORD_ID`, `CHECK_HOUR`, `SEED_WATCHLIST`); everything editable in the UI afterwards; `BASIC_AUTH` only if exposed beyond LAN/VPN |
| Health | homepage and `/api/health` report the watched domains |

## Run anywhere

```bash
docker compose up -d --build
curl -f http://localhost/api/health
```

## Database

| Item | Value |
|------|-------|
| Engine | SQLite |
| Data path | `./data/watcher.db` on the host |
| Backup | `sqlite3 data/watcher.db ".backup '<private-dir>/watcher.db'"`; or stop the app and copy |
| Integrity | `sqlite3 data/watcher.db "PRAGMA integrity_check;"` |
| Restore check | point `DB_PATH` at a copy in a disposable path and run the tests |
| Migrations | applied at startup by `app/db.py`; additive |

Settings rows hold the webhook URL, so backups are secrets: private paths, mode 600.
Follow `~/git/workflows/database-change.md`.

## Before any deploy

```bash
python -m unittest discover -s tests -v     # network disabled, isolated database
```

## Deploy to DEV

Procedure: `~/git/workflows/deploy-to-dev.md`. Mechanics: sync the source
(excluding `.git`, `data`, caches) to the host, replace everything in the stack
directory except `.env`, the compose override and `data/`, then
`docker compose up -d --build`. The homeserver dev README has the exact commands.

## Deploy to production

Through `~/git/workflows/promote-to-prod.md`; not promoted yet.

## Backup and rollback

Tag the running image before replacing it; take a consistent SQLite backup; roll
back with the previous tag and `docker compose up -d --no-build`.

## Verify after a deploy

Homepage 200, health lists the expected domains, `PRAGMA integrity_check` ok,
settings and domain rows match the pre-deploy backup. Record in `DIARY.md`.
