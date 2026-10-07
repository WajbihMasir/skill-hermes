# Evidence Capture, Report Claims & Test Doubles

Depth reference for `audit-robustness-probes`. Load when auditing a report
generator, an evidence/transcript path, or test doubles.

---

## Evidence capture: capture what was SENT, not what was built

**A mutation layer invalidates the object the caller holds.** `send_with_identity`
deep-copies the request and adds the identity's auth headers; that copy goes on
the wire. Evidence capture that records the caller's original object therefore
produces a transcript with **no `Authorization` header** — and a triager reading
it concludes the request was unauthenticated, which is the opposite of the
finding being reported.

Capture at the send boundary. Have the sender retain what it actually sent, plus
a bounded history so a cross-identity test yields two DISTINCT exchanges rather
than the same one twice.

Probe it in both directions:
- assert the transcript CONTAINS the auth header (masked) — missing it misleads
- assert the secret VALUE is absent — carrying it is a new vulnerability

Related: `str(None).upper()` is `"NONE"`, not `"GET"`. A falsy method must fall
back explicitly, or the report renders `NONE /path HTTP/1.1` as the request line.

### Bound the body, and mark the cut

A 50 MB response bloats the database and makes the report unreadable. Truncate —
and say so. Silent truncation is dangerous in a report: the reader assumes the
response ended there and may conclude the impact is smaller than it is.

### Redact at the boundary, not at the template

An `Authorization` header, a cookie, a `Set-Cookie`, and a `?token=` in a URL are
all credential shapes. Run them through the SAME DLP rules the rest of the system
uses, so one policy governs every egress path. A transcript that leaks the
researcher's own session is a new vulnerability, not evidence.

---

## Reproduction steps: real or explicitly absent

A fixed template ("authenticate as user_a and create an object") is what a
program closes as "not precise enough to reproduce the issue, not eligible for a
reward". There are two acceptable states and no third:

1. **A transcript exists** → the steps name the real URL, method, identities and
   observed status codes.
2. **No transcript** → the steps SAY SO.

A skeleton that reads like real evidence is worse than an obvious placeholder: it
invites a submission that cannot be reproduced. Probe the negative — with no
transcript, assert the output contains an explicit "not captured / verify by
hand" marker.

---

## Test doubles must match the REAL return shape

When code under test calls `response.json()`, `response.text`, and
`response.content`, a fake returning your own domain dataclass fails with
`'Response' object has no attribute 'text'` — a test bug that looks like a product
bug. Read what the code actually calls on the returned object and mirror THAT
shape.

Before debugging such a failure, check whether the fake is wrong rather than the
product. The tell: the same scenario passes in a standalone repro outside pytest.

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
