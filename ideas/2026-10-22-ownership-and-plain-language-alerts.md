# Domain ownership and plain-language alerts

- Created: 2026-10-22
- Status: Awaiting user decision (Proposed: accept into `features/` or decline)
- Revisit: 2026-10-25 (owner 2026-10-24: "will do later"; with the observation review)
- Priority: Medium
- From: user, after two "transfer period" alerts (adeptlab.dev, adeptproductions.dev)
  that were just registry grace windows closing after a move to one registrar. The
  alerts were correct but gave no hint that this was expected and harmless.

## Problem

Every status change gets the same `ℹ️ status: [...] → [...]` line in raw EPP
vocabulary. Someone who isn't technical can't tell "your transfer finished" from
"someone is taking your domain". The watcher also doesn't know which domains
are yours and which you're waiting to catch. That changes what an alert means:
a registrar change on a domain you own is a red flag. On a domain someone else
holds, it's just news.

## Proposal

### 1. Ownership: "mine" vs "watching"

- Each domain gets a role: **Mine** (protect it) or **Watching** (want it, track it).
- **Verify Mine** with a DNS TXT record, as Google and Cloudflare do: the UI shows
  `_domain-watcher.<domain> TXT dw-verify=<token>`, and a "Verify" button checks it.
  This proves you control the DNS, which on a self-hosted app is enough. A plain
  "I own this" toggle remains as an unverified fallback.
- After verification, the app records a **known-good fingerprint**: registrar,
  nameservers, expiry. When everything still matches, the page shows a green
  "✅ Yours, locked, matches what you set up". The app can also detect this
  softly, without a TXT record: when a domain's NS and registrar match those of
  your verified domains, it can offer "looks like yours, verify?"

### 2. Alerts that say whether to worry

Every alert follows three plain lines:

> **What happened** · **Is this normal?** · **What to do**

- A translation table for EPP statuses (`add period`, `renew period`,
  `transfer period`, `auto renew period`, `redemption period`, `pending delete`,
  `client/server *prohibited`, `client hold`…), each with a sentence a
  non-technical person can follow.
  Example: *"Transfer period ended on adeptlab.dev. This 5-day window always
  follows a registrar move and closes on its own. Your domain is locked and on
  your nameservers. Nothing to do."*
- Four levels, set by role × change, replace the single ℹ️:
  - ✅ **All good.** A routine window closed and the fingerprint still matches.
  - ℹ️ **FYI.** Something changed that you probably did, such as a renewal or a new NS.
  - ⚠️ **Check this.** A change you didn't flag on a domain you own, for example
    the transfer lock removed or the registrar or NS changed.
  - 🚨 **Act now.** Pending delete, redemption, client hold or expiry close on a domain
    you own, or a domain you're watching starting to drop.
- **Expected changes.** When `transfer period` or `add period` appears, the alert
  says "this clears around <date+5d>, no action needed". When it clears on
  schedule, the message is ✅ (or folded into a summary) rather than a new ℹ️.
- **"I'm moving this" toggle** on a domain you own. It silences the registrar, NS and
  transfer-period alerts you're about to cause for N days. Any of those changes
  outside that window escalates to ⚠️.
- Optional **quiet mode**: ✅ alerts skip Discord and go only to a weekly
  "all your domains are fine" digest.

### 3. In the UI

- Each status flag on the detail page gets a "what's this?" hover with the same
  plain text.
- The watchlist gets a health column per domain (✅ / ⚠️ / 🚨), so someone can
  tell everything is fine without reading anything.

## Open questions

**For the user:** accept, trim or decline? If accepted, which part first: plain-language
alerts (no new data) or ownership roles (TXT verification)?


- Should a TXT record that disappears after verification raise ⚠️, or only show
  as unverified?
- Is the "looks like yours" auto-detect enough on its own for a home user, so
  TXT verification becomes optional?
- How should the role carry over for a domain that moves from Watching to Mine
  when you catch it?

## Acceptance (if accepted)

- Each domain has a role, and a domain marked Mine can be verified by TXT.
- Every alert type has plain-language text with a what / normal? / what-to-do line.
- Grace-period closes on owned domains with a matching fingerprint show as ✅.
- Registrar or NS changes on owned domains outside a "moving" window show as ⚠️.
- Tests cover the mapping from role × change to level.
