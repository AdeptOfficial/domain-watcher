"""domain-watcher — plug-and-play domain monitor.

`docker compose up` → UI on :80 → add domains, set a Discord webhook, done.
Daily RDAP checks alert on drops, lapses, parking flips, and your own renewals.
"""
import base64, datetime as dt, json, os, re, time
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
VERSION = "2.1.0"

templates = Jinja2Templates(directory=BASE / "templates")
templates.env.globals["version"] = VERSION


def check_domain(row) -> list[str]:
    """Check one domain; persist snapshot; return alert lines (respecting its config)."""
    prev = json.loads(row["snapshot"]) if row["snapshot"] else None
    if prev is not None:
        prev["warned"] = row["warned"]
    snap = fetch(row["domain"])
    if snap["error"] and prev is not None:
        # Keep the last valid observation across repeated failures and restarts.
        # Error placeholders must never become the domain-change baseline.
        last_success = prev.get("last_success") if prev["error"] else prev
        if last_success is not None:
            snap["last_success"] = last_success
    if not snap["expiry"] and row["expiry_override"]:
        snap["expiry"] = row["expiry_override"]  # RDAP hides it; user-supplied date drives thresholds
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
    first = True
    checked = 0
    for row in db.list_domains():
        if not row["enabled"]:
            continue
        if not first:
            time.sleep(1.5)  # pace the sweep — don't burst rdap.org into a 429
        first = False
        lines += check_domain(row)
        checked += 1
    db.set_setting("last_sweep", dt.datetime.now().isoformat(timespec="seconds"))
    if lines:
        notify.send("discord", "\n".join(lines))
    errors = sum(1 for r in db.list_domains() if r["enabled"] and r["last_result"] == "error")
    # One line per sweep in `docker logs` — the only sweep history the app keeps.
    print(f"[domain-watcher] {'manual' if manual else 'scheduled'} sweep: "
          f"{checked} checked, {errors} errors, {len(lines)} alerts", flush=True)
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
async def no_store_html(request, call_next):
    # pages change on every check; never let the browser serve a stale one
    resp = await call_next(request)
    if resp.headers.get("content-type", "").startswith("text/html"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


@app.middleware("http")
async def basic_auth(request: Request, call_next):
    """Optional BASIC_AUTH=user:pass for people who expose this publicly."""
    cred = os.environ.get("BASIC_AUTH")
    if cred and request.url.path != "/healthz":
        expect = "Basic " + base64.b64encode(cred.encode()).decode()
        if request.headers.get("authorization") != expect:
            return Response(status_code=401, headers={"WWW-Authenticate": "Basic realm=domain-watcher"})
    return await call_next(request)


def vm(row) -> dict:
    """Row → view-model with real expiry + days-left."""
    snap = json.loads(row["snapshot"]) if row["snapshot"] else {}
    expiry = snap.get("expiry") or row["expiry_override"]
    days = None
    if expiry:
        try:
            days = (dt.date.fromisoformat(expiry) - dt.date.today()).days
        except ValueError:
            days = None
    return {**dict(row), "expiry": expiry, "days": days, "snap": snap,
            "available": snap.get("available", False), "error": snap.get("error", False)}


def rows_ctx() -> dict:
    hour = db.get_setting("check_hour") or os.environ.get("CHECK_HOUR", "9")
    return {
        "domains": [vm(r) for r in db.list_domains()],
        "last_sweep": db.get_setting("last_sweep"),
        "check_hour": int(hour) if hour.isdigit() else 9,
    }


def render_rows(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "_rows.html", rows_ctx())


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", rows_ctx())


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    return templates.TemplateResponse(request, "settings.html", {
        "webhook": db.get_setting("discord_webhook"),
        "ping_id": db.get_setting("ping_discord_id"),
        "check_hour": db.get_setting("check_hour") or os.environ.get("CHECK_HOUR", "9"),
    })


@app.get("/domains/{did}", response_class=HTMLResponse)
def domain_page(request: Request, did: int):
    row = db.get_domain(did)
    if not row:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "detail.html",
                                      {"d": vm(row), "channels": notify.CHANNELS})


def _detail_or_redirect(request: Request, did: int):
    """htmx requests get the re-rendered page (swapped in place, no history entry);
    plain form posts fall back to the classic 303 redirect."""
    if request.headers.get("HX-Request"):
        return domain_page(request, did)
    return RedirectResponse(f"/domains/{did}", status_code=303)


@app.post("/domains/{did}/settings")
def domain_settings(request: Request, did: int, note: str = Form(""), notify_ch: str = Form("discord"),
                    ping_available: str = Form(None), ping_drop: str = Form(None),
                    expiry_override: str = Form("")):
    ov = expiry_override.strip() or None
    if ov and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", ov):
        ov = None
    db.update_settings_for(did, note.strip(), notify_ch,
                           1 if ping_available else 0, 1 if ping_drop else 0, ov)
    return _detail_or_redirect(request, did)


@app.post("/domains/{did}/check-page")
def check_from_page(request: Request, did: int):
    row = db.get_domain(did)
    if row:
        lines = check_domain(row)
        if lines:
            notify.send(row["notify"], "\n".join(lines))
    return _detail_or_redirect(request, did)


@app.post("/domains/{did}/delete-page")
def delete_from_page(did: int):
    db.delete_domain(did)
    return RedirectResponse("/", status_code=303)


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
