# Building an Engagement from a Live Scope

Recipe for turning a platform's scope into a machine-enforced allow-list plus a
ranked work list. Complements the selection gates in SKILL.md and the scope
mechanics in `hackerone-platform.md`.

Write a **generator script**, not a hand-edited file. A 150-asset scope copied by
hand drops an asset, and a dropped asset is a scope-level false negative. The
generator re-runs whenever the program changes its scope.

---

## Step 1 — pull the scope

Fetch the program and its full `structured_scopes` over the public GraphQL
endpoint (see `hackerone-platform.md` for the query and field names). Keep the
raw JSON in a file so the generator is re-runnable without another request.

---

## Step 2 — parse into four buckets, and never silently drop

| Asset kind | Goes to |
|---|---|
| Bare hostname or wildcard | `allowed_domains` **+ `whole_hosts`** |
| URL with a path | `allowed_domains` + `host_paths[host]` |
| CIDR / hardware / source / mobile | a `not_http_testable` list |
| `eligible_for_submission: false` | a `skipped` list with the reason |

The two lists matter. An asset your tool cannot reach is **reported, not
dropped** — the operator must know the program covers more than HTTP, and must
know which entries were excluded and why.

**Track `whole_hosts` as you parse.** A host listed as a bare asset is in scope in
its ENTIRETY. If the same host also has a listed path, emitting a `host_paths`
entry NARROWS it — and the tool then refuses a URL the program explicitly allows:

```python
host_paths = {h: ps for h, ps in host_paths.items() if h not in whole_hosts}
```

Beware entries that only LOOK like paths: a CIDR written as a URL
(`http://10.0.0.0/28`) yields a `/28` "path" that must not become a path rule.

---

## Step 3 — keep recon hints outside the enforcement block

The listed paths on a whole-host asset are no longer enforcement rules, but they
are the **best hints in the file** — they are the endpoints the program itself
points at. Put them under a separate top-level key:

```yaml
scope:
  allowed_domains: [...]
  host_paths: {...}
  blocked_domains: [...]
  max_requests_per_minute: 30
known_urls:            # informational only, never consulted for enforcement
  - https://host.example/oauth/token
```

Outside `scope:` so no parser can read them as a rule, and **merged explicitly by
every reader that builds a target list**. A hint no reader can see is not a hint:
the live `/oauth/token` endpoint sat in the file and was never probed because the
probe returned only the `scope:` block.

---

## Step 4 — put policy controls where the loader reads them, then read them back

The rate limit belongs wherever the loader actually looks
(`scope.max_requests_per_minute`). Placing it under a `governance:` block leaves
the DEFAULT in force — a control that looks configured and is not. After writing
any control, load the file through the real loader and assert the value; do not
trust the file you just wrote.

Set the limit conservatively. On a program whose only prohibition is DoS, the
rate limit **is** the compliance control.

---

## Step 5 — verify the gate BEFORE sending anything

Assert both directions against the real guard, not the file:

| URL | Expected |
|---|---|
| bare host, arbitrary path | ALLOW |
| path-only host, listed path | ALLOW |
| path-only host, other path | **DENY** |
| look-alike domain (`evil-<target>.com`) | **DENY** |
| blocked infrastructure domain | **DENY** |

A gate that has never been observed refusing something is untested. Then
**re-check every URL immediately before sending it**, even though you built it
from the scope file — the assertion should never fire, which is exactly why it is
worth having.

---

## Step 6 — reachability probe (single unauthenticated GET per target)

Design rules, each of which exists because ignoring it produced a wrong answer:

1. **Enumerate host+path PAIRS.** A host's root routinely 404s while the listed
   path answers (401 on `/oauth/token`, 404 on `/`). Hosts alone lose every
   listed endpoint.
2. **Retry once before recording a failure.** A CDN-fronted host intermittently
   times out on the first connection. One attempt reported a live auth endpoint
   as DEAD — a false negative at the cheapest possible stage.
3. **Gate-check every URL before the request**, and skip anything refused.
4. **Sleep between requests** from the scope's rate limit (requests/minute →
   seconds). Report the effective rate in the output so the operator can see it.
5. **Send a plain, honest User-Agent** identifying the research. Do not invent a
   header the program never asked for; an unnecessary one is a bot signal.
6. **Persist results to JSON** and summarise: probed / alive / dead / status
   histogram. That file is the work list.

**Read the headers of every 401.** They usually name the mechanism
(`WWW-Authenticate: Basic realm="oauth2/client"`, `SERVLET: dispatcherServlet`,
`JSESSIONID=node0...`), which converts a bare status code into a concrete
hypothesis list.

---

## Classifying a program's automation stance from the policy text

Grep the `policy` field for the families in `hackerone-platform.md`, then sort
into one of:

| Verdict | What the text actually says |
|---|---|
| **ALLOWED** | No automation language at all, or it names only DoS / social engineering |
| **CONDITIONAL** | "without validation", "without additional analysis", "based only on", "scanner output", "incomplete proof of concept" |
| **COORDINATION** | "without prior coordination", "without prior approval" |
| **FORBIDDEN** | "do not use automated tools or scanners", "the use of automated scanners is", "automated tools, scripts…" |

Two traps when reading these:

- **"Reports generated using automated scanning tools" is usually an exclusion of
  the REPORT, not a ban on the tool.** Read the sentence's subject before
  classifying — this wording is CONDITIONAL (validate by hand), not FORBIDDEN.
- **A hidden obligation can outrank the automation clause.** A policy that permits
  automation may still require human-supervised testing, a 1 req/s ceiling, or a
  mandatory identifying header on every request. Grep for those separately; the
  absence of an automation ban is not the absence of obligations.

Rank surviving programs by API-shaped asset count first, then competition. A
large scope with almost no reports is worth checking against reachability before
treating it as an opportunity — it is sometimes quiet because nobody can reach it.

---

## What the engagement directory should contain

```
engagements/<handle>/
  scope.yaml        machine-enforced allow-list + known_urls + rate limit
  engagement.json   policy obligations, mandatory headers, asset counts,
                    highest-value targets, not_http_testable list
  README.md         operator checklist (fetch → dry-run → probe → accounts)
  HUNT_LOG.md       what the probe found, with limits stated
```

`HUNT_LOG.md` must state, explicitly: the method and rate limit, whether the
capture was authenticated, that **zero vulnerabilities were confirmed**, which
hosts are third-party non-targets, and that the scope is a snapshot to re-fetch.
A log listing endpoints without those caveats reads as a findings report.
