"""domain-watcher — plug-and-play domain monitor.

`docker compose up` → UI on :80 → add domains, set a Discord webhook, done.
Daily RDAP checks alert on drops, lapses, parking flips, and your own renewals.
"""
import base64, json, os
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db, notify
from .checker import diff, fetch

BASE = Path(__file__).parent
templates = Jinja2Templates(directory=BASE / "templates")


def check_domain(row) -> list[str]:
    """Check one domain; persist snapshot; return alert lines (respecting its config)."""
    prev = json.loads(row["snapshot"]) if row["snapshot"] else None
    if prev is not None:
        prev["warned"] = row["warned"]
    snap = fetch(row["domain"])
    ping_id = db.get_setting("ping_discord_id")
    alerts, _baseline, warned = diff(row["domain"], prev, snap,
                                     bool(row["ping_available"]), bool(row["ping_drop"]), ping_id)
    result = ("error" if snap["error"] else "AVAILABLE" if snap["available"]
              else f"expires {snap['expiry'] or '?'}")
    db.save_check(row["id"], snap, warned, result)
    return alerts if row["notify"] != "none" else []


def run_all(manual: bool = False) -> int:
    """Scheduled/manual sweep: one batched Discord message for everything."""
    lines: list[str] = []
    for row in db.list_domains():
        if not row["enabled"]:
            continue
        lines += check_domain(row)
    if lines:
        notify.send("discord", "\n".join(lines))
    return len(lines)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    hour = int(db.get_setting("check_hour") or os.environ.get("CHECK_HOUR", "9"))
    sched = BackgroundScheduler()
    sched.add_job(run_all, "cron", hour=hour, minute=0, id="daily")
    sched.start()
    print(f"[domain-watcher] daily check scheduled at {hour:02d}:00 ({os.environ.get('TZ', 'container tz')})")
    yield
    sched.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.middleware("http")
async def basic_auth(request: Request, call_next):
    """Optional BASIC_AUTH=user:pass for people who expose this publicly."""
    cred = os.environ.get("BASIC_AUTH")
    if cred and request.url.path != "/healthz":
        expect = "Basic " + base64.b64encode(cred.encode()).decode()
        if request.headers.get("authorization") != expect:
            return Response(status_code=401, headers={"WWW-Authenticate": "Basic realm=domain-watcher"})
    return await call_next(request)


def render_rows(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "_rows.html", {"domains": db.list_domains()})


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "domains": db.list_domains(),
        "webhook": db.get_setting("discord_webhook"),
        "ping_id": db.get_setting("ping_discord_id"),
        "check_hour": db.get_setting("check_hour") or os.environ.get("CHECK_HOUR", "9"),
        "channels": notify.CHANNELS,
    })


@app.post("/domains", response_class=HTMLResponse)
def add(request: Request, domain: str = Form(...), note: str = Form("")):
    d = domain.strip().lower().rstrip(".")
    if d and "." in d and "/" not in d:
        try:
            did = db.add_domain(d, note.strip())
            check_domain(db.get_domain(did))  # immediate first snapshot; UI is the baseline
        except Exception:
            pass  # duplicate — just re-render
    return render_rows(request)


@app.post("/domains/{did}/delete", response_class=HTMLResponse)
def remove(request: Request, did: int):
    db.delete_domain(did)
    return render_rows(request)


@app.post("/domains/{did}/toggle/{field}", response_class=HTMLResponse)
def flip(request: Request, did: int, field: str):
    db.toggle(did, field)
    return render_rows(request)


@app.post("/domains/{did}/notify", response_class=HTMLResponse)
def channel(request: Request, did: int, value: str = Form(...)):
    db.set_notify(did, value)
    return render_rows(request)


@app.post("/domains/{did}/check", response_class=HTMLResponse)
def check_one(request: Request, did: int):
    row = db.get_domain(did)
    if row:
        lines = check_domain(row)
        if lines:
            notify.send(row["notify"], "\n".join(lines))
    return render_rows(request)


@app.post("/check", response_class=HTMLResponse)
def check_all(request: Request):
    run_all(manual=True)
    return render_rows(request)


@app.post("/settings")
def settings(webhook: str = Form(""), ping_id: str = Form(""), check_hour: str = Form("9")):
    db.set_setting("discord_webhook", webhook.strip())
    db.set_setting("ping_discord_id", ping_id.strip())
    if check_hour.strip().isdigit() and 0 <= int(check_hour) <= 23:
        db.set_setting("check_hour", check_hour.strip())
    return RedirectResponse("/", status_code=303)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "domains": len(db.list_domains())}
