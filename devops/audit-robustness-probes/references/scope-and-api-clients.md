# Scope Engines, API Clients & Report Claims

Depth reference for `audit-robustness-probes`. Load when auditing a scope engine,
an API client, a scanner's detection, or a report generator.

---

## Scope allow-lists: a global path list cannot express per-host rules

**A scope that mixes a path-restricted host with an open host leaks.** This is a
security bug, not a convenience gap.

Concretely: HackerOne scope = `app.example.com` limited to `/api`, plus
`blog.example.com` (whole host). A flat `allowed_paths: ['/api/*', '/*']` is
GLOBAL, so `/*` from the open host also widened the restricted one:

```
https://app.example.com/api/x   -> ALLOWED  (correct)
https://app.example.com/SECRET  -> ALLOWED  (WRONG — out-of-scope request)
```

On a bug-bounty platform an out-of-scope request can cost the account, so this is
the highest-severity class of bug in a scope engine.

**Fix:** add per-host path rules (`host_paths: {host: [patterns]}`) and evaluate
them BEFORE the global list. A host with its own rule is governed only by that
rule; the global list is the fallback for hosts without one.

**Probe it directly** — do not trust a config-shape assertion:
- Build the real guard from the produced config and call `is_allowed()` on a URL
  OUTSIDE the restricted path on the restricted host. Assert it is DENIED.
- Assert a URL on the OPEN host is still allowed (the fix must not lock everything).
- Assert a bare-string value (`"host": "/api/*"`) is one pattern, not per-character.
- Assert `blocked_paths` still wins over a host rule (ordering matters).

### A deny-list needs its own field

`blocked_paths` matches URL **paths**. Putting a HOSTNAME in it silently does
nothing — the exclusion is then enforced only by omitting the host from the
allow-list, which a wildcard asset re-opens. A scope engine needs a separate
`blocked_domains` list checked BEFORE the allow-list, so "out of scope" is a hard
boundary rather than an absence.

Probe: given `allowed_domains: ['*.example.com']` and
`blocked_domains: ['secret.example.com']`, assert `secret.example.com` is DENIED.

### Preserve eligibility as two flags

An asset can be in scope to TEST but not eligible to be PAID. Collapsing these
into one boolean produces a scope that maps fine and pays nothing — and asking
"did we map anything?" is not the same as "is any mapped asset paid?". Track
`paid` per asset and answer the second question.

### Report unsupported inputs, never drop them silently

A scope listing a mobile app or a source repo is in scope and the tool cannot test
it. Dropping it silently is a false negative at the scope level. Collect them into
an `unsupported` list with a reason and surface a warning.

Related: prefer returning a diagnostic report over raising when nothing is
testable. Raising discards the reason ("8 assets, all mobile") that tells the
operator what to do. Return the report with a loud warning and expose an explicit
`is_testable()` — an empty allow-list that silently fails every request is the
real hazard.

---

## Pagination and URL re-encoding

**A `next` link that is already URL-encoded must be requested VERBATIM.** Parsing
its query string into pairs and handing them back to an HTTP client as `params`
double-encodes them: `page%5Bnumber%5D=2` becomes `page%255Bnumber%5D=2`, so the
server reads the literal text `page%5Bnumber%5D` instead of `page[number]`. The
usual symptom is silent: pagination repeats the first page forever, so a collector
returns the same 100 rows and looks like it worked.

Probe it by asserting on the **exact URL the client sends**, not on a substring:
- `assert sent_url == next_link` — catches re-encoding AND reordering
- `assert "%255B" not in sent_url` — the specific double-encode signature
- `assert params is None` on the follow-up call — proves no second encoding path

Two related rules for any paginated API client:
- **Follow `links.next` rather than constructing page numbers.** The server's link
  carries the cursor; rebuilding `?page=N` silently drops or repeats rows if the
  server's paging scheme changes.
- **Bound the walk** (`max_pages`) and **refuse links off the expected host** — an
  attacker-controlled pagination link is an SSRF primitive.

---

## Credentials in an API client

- **Read secrets from the environment, never from a config file**, and name the
  missing variable in the error so the fix is obvious. Include what to DO
  (`export ...`), not just what failed.
- **Never log, `repr`, or serialise the token.** Assert it: `assert "SECRET" not in
  repr(client)`, and assert the token is absent from the URL (use `auth=`, not a
  query param) so it cannot leak through logs or exception messages.
- **Retry ONLY what a retry can fix.** A 401 (bad token), 403, 404, and 4xx are
  deterministic; retrying them wastes the budget and resembles credential probing.
  Retry 429 (honouring `Retry-After`, clamped) and 5xx/transport timeouts with
  bounded exponential backoff.
- Give each failure its own exception type (`Auth`, `NotFound`, `RateLimited`,
  `Unavailable`) so callers can react differently instead of string-matching a
  generic error.

---

## Severity, confidence, and what a report is actually claiming

**Severity and confidence are different quantities and conflating them breaks a report.**

- **Severity / CVSS = the impact IF the bug is real.** It is what a triage platform
  asks for and what a human verifies. Derive it from the vulnerability class and the
  affected endpoint. Never from how sure the scanner is.
- **Confidence = how strongly the evidence supports the claim.** Report it
  SEPARATELY, and use it to gate submission. It must not silently move the severity
  label.

Why the distinction matters: "tempering" severity by confidence is **cosmetic, not
protective**. An unconfirmed finding is Not Applicable whatever label it carries,
and on platforms where N/A costs reputation, the label buys nothing. The only real
protection is a **gate that refuses to file the finding at all** until evidence is
sufficient.

Probe for the contradiction: **any single rendered line that shows a severity label
next to a CVSS score must be self-consistent**
(`severity_for_score(score) == label`). Two heuristics — one from confidence, one
from a metric mapping — will eventually disagree, and "Severity: medium (CVSS 9.8)"
tells a triager the tool does not understand its own output.

When a test asserts `confidence 0.6 -> Medium`, that test is encoding the wrong
model. Fix the test to assert the real contract (impact rating is stable;
confidence is reported alongside), not to re-tune the threshold.

---

## Shape bugs at a storage boundary

A column written by several components is a recurring source of crashes and silent
wrong values. Probe ALL of these:

- **Double encoding**: writer A calls `json.dumps` and the store helper calls it
  again, so the column holds a JSON *string of a JSON string*. Parsing once returns
  a `str`; the field reads as `None`; a **confirmed** finding renders as
  `status=None`. Fix at the WRITER (pass a plain dict and let the store serialise)
  and make the READER tolerant (unwrap repeatedly, bounded, until a dict appears).
- **Mixed shapes from different writers**: one stores a dict, another a JSON string.
  Normalise at the read boundary (dict / JSON string / list / scalar / non-JSON
  text) instead of trusting the shape.
- Assert the round trip end-to-end: store a finding, read it back, and check the
  rendered output contains the real status — not just that the parse helper returns
  a dict.

---

## When one fix exposes the next

A latent crash can stay hidden behind an upstream bug: if a detector never produces
findings of type X, then every code path that formats a type-X finding is never
executed. Fixing the detector makes the formatter reachable, and it crashes. After
fixing a "produces nothing" bug, **re-run the full end-to-end path that consumes the
new output** — do not stop at the detector's own tests.

**Fixing a detector breaks tests that encoded its silence.** Expect count assertions
like `assert findings == 8` to fail once the detector works, because that number
silently meant "this hunter finds nothing". Resolve each failure by asking which
side is wrong:

- If the test asserted a **count**, it was testing a magic number instead of the
  contract. Rewrite it to assert the relationship (non-empty, list matches the job
  count, report total matches stored rows) — do not just lower the number.
- If the test asserted **"a clean target has no findings"** and it now fails, check
  the FIXTURE. A fake that returns 200 to a regular user on an admin route is
  modelling a *vulnerable* target while the test claims a clean one. The detector is
  right; fix the fake.
