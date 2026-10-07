# Browser-Driven Endpoint Discovery

Operational recipe for finding API endpoints on a target that publishes **no**
machine-readable spec. Complements the target-selection gates in SKILL.md.

Why it matters: a spec-driven pipeline can only test routes the spec declares. A
real engagement usually has no spec, or has one that omits exactly the
interesting routes (internal APIs, auth endpoints, admin paths). Driving a real
browser and reading the page's own traffic finds what the spec does not contain.

---

## The recipe

1. **Read the policy first.** Discovery sends real requests to a third-party host.
   Confirm the automation stance and attach any mandatory header before the first
   one leaves (see SKILL.md).
2. **Check the host serves a page that calls the API.** A JSON-only host produces
   zero XHR — you need an HTML app that fetches from the backend. Open the landing
   page and confirm the capture is non-empty before drawing conclusions.
3. **Enable network capture, then navigate.** Capture is usually opt-in; a
   navigation with capture off returns an empty list, which reads as "this page
   makes no API calls" rather than "capture was not enabled".
4. **Derive endpoints** from the captured XHR/fetch entries.
5. **Filter out non-targets** before acting (see below).
6. **Repeat while authenticated** — this is where the value is.

```python
from backend.browser_agent import BrowserAgent

a = BrowserAgent(headless=True, scope_guard=guard)
a.start_network_capture("user_a")
a.navigate("https://target.example/app", wait_until="networkidle",
           headers={"X-HackerOne-Research": "<username>"})
net = a.stop_network_capture()
api = [n for n in net if n.get("resource_type") in ("xhr", "fetch")]
endpoints = a.derive_endpoints()
a.close()
```

---

## Two failure modes that look like "the browser is broken"

**An empty capture on a marketing page is normal.** A landing page loads CSS, JS,
and analytics — not API calls. The capture is working; there is simply nothing
API-shaped to see. Verify capture works by pointing it at a page you *know* calls
an API (a dashboard, or a local fixture that fetches) before concluding the tool
is faulty.

**A JSON-only fixture proves nothing about discovery.** If the local test target
answers `/openapi.json` but serves no HTML, discovery has nothing to observe. To
exercise the path end-to-end, give the fixture a minimal HTML page that calls the
API from JavaScript — then a successful run shows real XHR being captured and
endpoints derived.

---

## Authenticated discovery is the step that finds bugs

An unauthenticated capture shows public marketing routes and third-party
analytics. The endpoints that carry **object identifiers** — the ones where
broken authorization lives — appear only after login.

Log in **by hand in a visible browser** (`headless=False`) and browse normally
while capture runs. This keeps the workflow inside conditional policies: the tool
observes a human's session rather than scripting a login flow, which is what
"force multiplier for a human" means in practice.

---

## Filtering the capture before you act

A raw capture is mostly noise. Sort it:

| Category | Action |
|---|---|
| Same-origin, named for auth/session (`*/api/*auth*`, `/oauth/*`, `/session`) | **highest value** — a lead, not a finding |
| Same-origin object routes (`/api/orders/1001`, `/api/users/42`) | test cross-identity |
| Third-party analytics / ad / consent hosts | **not targets** — outside scope; the preflight gate must block them |
| Static assets (`.css`, `.js`, fonts) | ignore |

**An auth-shaped endpoint is a lead, not a bug.** Discovery only establishes that
the route exists and the page calls it. Nothing is confirmed until you show that an
identifier not bound to the caller's session is accepted.

---

## Reporting what discovery found

Be explicit about the limits, or the operator will over-trust the list:

- Say the capture was **unauthenticated** if it was, and that user-specific
  endpoints therefore do not appear.
- Say the depth: how many pages were visited, how many requests were spent.
- Say **zero vulnerabilities were confirmed** — it is a candidate list.
- Name the third-party hosts that appeared and state they are **not** targets.

A discovery log that lists endpoints without those caveats reads as a findings
report, which it is not.

---

## Verify the entry point the operator actually runs

The same engine reached two ways can differ in whether it is wired. A CLI
subcommand reported **`safe: 8`** on a deliberately vulnerable target — a
false-negative that reads as a clean scan — while the API/job path, given the same
identities, found **9 findings**. The library path was fine; the CLI entry point
never loaded the credentials.

So: after wiring identities, drive the **real** entry point (the CLI subcommand,
or the job runner the dashboard uses) and confirm findings appear. A passing unit
test or a direct library call does not prove the CLI is configured, and "the
engine works" is not the same claim as "the command the user runs works".

When you see a suspicious `safe`/`0 findings` result, assert the precondition
before believing it: were the identities actually authenticated on THAT path?

---

## Keep the fixture inside the scope you ship

A demo target must be reachable **without widening the scope**. If the shipped
config allows only `/api/*` on localhost, add an in-scope HTML route
(`/api/app`) to the fixture rather than adding `/app` to the allow-list.

Widening an allow-list so a test passes is how a tool ends up requesting an
out-of-scope URL in production — and an out-of-scope request is the mistake that
costs a HackerOne account. The scope gate refusing your test URL is the gate
working; fix the fixture, not the gate.

---

## Preconditions that make discovery worthless

- **No second identity.** Discovery finds routes; cross-identity comparison proves
  the bug. One account yields `inconclusive` forever.
- **A browser context is not an identity.** Selecting a different browser context
  does not attach that identity's credentials — every request goes out anonymous
  and the comparison becomes 401-vs-401. Wire the identity to auth headers on the
  browser path *and* the HTTP fallback. See `audit-robustness-probes` for the
  detection signature.
- **No mandatory header.** If the policy requires a research header on every
  request, it must be applied at the send chokepoint so no code path can omit it —
  and `navigate()` must accept headers, or the common call silently drops it.
