"""RDAP diff engine — port of workflow/domain-watcher.n8n.json's Code node."""
import json, re, time, datetime as dt
import httpx

PARKING = re.compile(r"(atom|sedo|afternic|dan|parkingcrew|bodis|squadhelp|hugedomains)\.", re.I)
THRESHOLDS = [1, 7, 14, 30]


def fetch(domain: str) -> dict:
    """One RDAP lookup with a single retry — a transient 429/5xx burst from
    rdap.org must not flag every domain as failing."""
    snap = _fetch_once(domain)
    if snap["error"]:
        time.sleep(6)
        snap = _fetch_once(domain)
    return snap


def _fetch_once(domain: str) -> dict:
    try:
        r = httpx.get(f"https://rdap.org/domain/{domain}", follow_redirects=True,
                      timeout=20, headers={"accept": "application/rdap+json, application/json"})
        if r.status_code == 404:
            return {"available": True, "error": False, "status": [], "expiry": None, "ns": [], "registrar": None}
        if not r.is_success:
            return {"available": False, "error": True, "status": [], "expiry": None, "ns": [], "registrar": None}
        b = r.json()
        exp = next((e for e in b.get("events", []) if e.get("eventAction") == "expiration"), None)
        reg = next((e for e in b.get("entities", []) if "registrar" in (e.get("roles") or [])), None)
        fn = None
        if reg and reg.get("vcardArray"):
            fn = next((x[3] for x in reg["vcardArray"][1] if x[0] == "fn"), None)
        return {
            "available": False, "error": False,
            "status": sorted(b.get("status") or []),
            "expiry": str(exp["eventDate"])[:10] if exp else None,
            "ns": sorted((n.get("ldhName") or "").lower() for n in b.get("nameservers") or []),
            "registrar": fn,
        }
    except Exception:
        return {"available": False, "error": True, "status": [], "expiry": None, "ns": [], "registrar": None}


def diff(domain: str, prev: dict | None, snap: dict, ping_available: bool,
         ping_drop: bool, ping_id: str) -> tuple[list[str], str | None, int | None]:
    """Returns (alert_lines, baseline_line, warned_threshold)."""
    L = f"**{domain}**"
    ping = f" <@{ping_id}>" if ping_id else ""
    alerts: list[str] = []
    baseline = None

    if prev is None:
        baseline = ("fetch error" if snap["error"] else "AVAILABLE" if snap["available"]
                    else f"expires {snap['expiry'] or '?'}" + (f" · {snap['registrar']}" if snap["registrar"] else ""))
    else:
        if prev["error"] != snap["error"]:
            alerts.append(f"⚠️ {L}: RDAP lookups failing" if snap["error"] else f"✅ {L}: RDAP lookups recovered")
        comparison = prev.get("last_success") if prev["error"] else prev
        if not snap["error"]:
            # Old error snapshots (and failed first checks) have no valid baseline.
            # Still surface actionable current states on recovery without inventing
            # registrar/nameserver changes from empty error placeholders.
            if comparison is None:
                if snap["available"]:
                    alerts.append(f"🟢 {L} IS AVAILABLE — GRAB IT NOW{ping if ping_available else ''}")
                if any(re.search(r"pending ?delete|redemption", s, re.I) for s in snap["status"]):
                    alerts.append(f"🚨 {L} status: {snap['status']} — DROP INCOMING, place backorders NOW{ping if ping_drop else ''}")
        if not snap["error"] and comparison is not None:
            prev = {**comparison, "warned": prev.get("warned")}
            if prev["available"] != snap["available"]:
                alerts.append(f"🟢 {L} IS AVAILABLE — GRAB IT NOW{ping if ping_available else ''}"
                              if snap["available"] else f"🔒 {L} just got registered by someone")
            if prev["status"] != snap["status"]:
                drop = any(re.search(r"pending ?delete|redemption", s, re.I) for s in snap["status"])
                alerts.append(f"{'🚨' if drop else 'ℹ️'} {L} status: {prev['status']} → {snap['status']}"
                              + (f" — DROP INCOMING, place backorders NOW{ping if ping_drop else ''}" if drop else ""))
            if prev["ns"] != snap["ns"]:
                park = any(PARKING.search(n) for n in snap["ns"])
                alerts.append(f"{'🅿️' if park else '🔀'} {L} nameservers: {', '.join(prev['ns']) or '—'} → "
                              f"{', '.join(snap['ns']) or '—'}" + (" (parking service — likely listed for sale)" if park else ""))
            if prev["registrar"] != snap["registrar"]:
                alerts.append(f"🏷️ {L} registrar: {prev['registrar'] or '—'} → {snap['registrar'] or '—'}")
            if prev["expiry"] != snap["expiry"]:
                alerts.append(f"📅 {L} expiry moved: {prev['expiry'] or '—'} → {snap['expiry'] or '—'}")

    warned = (prev or {}).get("warned")
    if not snap["error"] and snap["expiry"]:
        days = (dt.date.fromisoformat(snap["expiry"]) - dt.date.today()).days
        th = next((t for t in THRESHOLDS if days <= t), None)
        if th is not None and th != warned:
            alerts.append(f"⏳ {L} expires in {days} day(s) — {snap['expiry']}")
            warned = th
        if days > 30:
            warned = None
    return alerts, baseline, warned


def send_discord(webhook: str, content: str, attempts: int = 3) -> bool:
    """Post with retries on 429/5xx/network errors. Logs never include the
    webhook URL (it is a credential) — only status codes and error types."""
    if len(content) > 1900:
        content = content[:1900] + "\n…(truncated)"
    for n in range(1, attempts + 1):
        wait = 5.0
        try:
            r = httpx.post(webhook, json={"content": content}, timeout=15)
            if r.is_success:
                return True
            why = f"HTTP {r.status_code}"
            if r.status_code == 429:
                try:
                    wait = min(float(r.json().get("retry_after", 5)), 30.0)
                except Exception:
                    pass
            elif r.status_code < 500:
                print(f"[domain-watcher] discord send failed: {why}, not retrying", flush=True)
                return False  # bad or deleted webhook — retrying won't help
        except Exception as e:
            why = type(e).__name__
        print(f"[domain-watcher] discord send failed: {why} (attempt {n}/{attempts})", flush=True)
        if n < attempts:
            time.sleep(wait)
    return False
