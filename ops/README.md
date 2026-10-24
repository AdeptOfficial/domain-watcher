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
| Health | homepage and `/healthz` report the watched domains |

## Run anywhere

```bash
docker compose up -d --build
curl -f http://localhost/healthz
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

## Container acceptance checks

After building a candidate, run `ops/acceptance.sh domain-watcher:candidate`.
The standalone harness uses fake RDAP/Discord peers, an internal network and a
throwaway volume, with the normal app image. It verifies outage/restart/recovery,
notifications, saved settings and diagnostics. No image is built or pulled at runtime.
Full setup, limits and cleanup: [acceptance tests](../docs/features/acceptance-test-suite.md).
A core-only run is diagnostic and does not satisfy the release gate.

## Deploy to DEV

Procedure: `~/git/workflows/deploy-to-dev.md`. Mechanics: sync the source
(excluding `.git`, `data`, caches) to the host, replace everything in the stack
directory except `.env`, the compose override and `data/`, then
`docker compose up -d --build`. The homeserver dev README has the exact commands.

For an already tested image, transfer it with `docker save` / `docker load` and
verify the loaded image identifier. Preserve the running image under a rollback tag,
back up SQLite/source as above, tag the candidate with the Compose image name and
use `docker compose up -d --no-build`. Sync matching source/harness from the committed
candidate while preserving `.env`, override and data. Do not rebuild the verified
candidate on the target host. Record image identity and run the full isolated suite
there before replacing the live app. Instance-specific paths belong in homeserver.

## Deploy to production

Through `~/git/workflows/promote-to-prod.md`; not promoted yet.

## Backup and rollback

Tag the running image before replacing it; take a consistent SQLite backup; roll
back with the previous tag and `docker compose up -d --no-build`.

## Verify after a deploy

Homepage 200, health lists the expected domains, `PRAGMA integrity_check` ok,
settings and domain rows match the pre-deploy backup. Record in `DIARY.md`.
