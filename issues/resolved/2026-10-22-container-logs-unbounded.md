# Container logs grow without limit

- Created: 2026-10-22
- Status: Resolved 2026-10-22, fixed on DEV (release `5755649`); `docker inspect` shows json-file max-size 5m, max-file 3
- Severity: Low
- From: logging review on 2026-10-22.

## Problem

`compose.yaml` sets no `logging:` options, so Docker's default `json-file` driver
keeps every line forever. Uvicorn logs every HTTP request, including htmx partial
refreshes. On a 6G LXC disk this will eventually fill the disk, and the important
lines (sweep summaries, delivery failures) get buried.

## Next steps

- Add `logging: {driver: json-file, options: {max-size: "5m", max-file: "3"}}` to
  `compose.yaml`. That is plenty to cover several weeks of daily sweep lines.
- Optionally pass `--no-access-log` to uvicorn, or log only non-2xx requests.

## Acceptance

`docker inspect` shows the log options on DEV, and the app still starts with
`.env` and the override kept.
