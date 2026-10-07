---
name: bug-bounty-engagement
description: "Use when picking a bug bounty target; read policy first."
version: 1.0.0
author: hermes-curator
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [bug-bounty, hackerone, scope, policy, disclosure, security-research]
    related_skills: [audit-robustness-probes, fastapi-api-hardening, grounded-citations]
---

# Bug Bounty Engagement

## When to use

Any request to find bugs on a bug-bounty platform: "find me a target", "which
program should I hunt", "is this program worth it", "can I run a scanner on X",
or working an engagement you have already picked. Also load it before pointing ANY
automated tool at a third-party host, because the policy read is a precondition,
not an optional step.

Platform-specific mechanics (reputation table, report states, severity options,
asset types, the directory-pull query) live in
`references/hackerone-platform.md`. Load that when you need the numbers.

Finding endpoints on a target that publishes no spec — driving a real browser,
capturing its XHR/fetch traffic, and filtering the result — is in
`references/browser-endpoint-discovery.md`. Load that when a target has no
usable OpenAPI spec, or when you need to enumerate routes before testing.

Turning a live scope into a machine-enforced allow-list plus a ranked work list
— the generator, the parse rules, the gate verification, and the reachability
probe design — is in `references/engagement-scope-build.md`. Load that before
building or rebuilding an engagement directory.

When a target is sales-gated or you have no test accounts, the vulnerability
classes that need **no authentication at all** — CORS misconfiguration, exposed
configuration and VCS files, directory listing — are in
`references/no-account-checks.md`. Load that before telling the user an
engagement cannot proceed for lack of credentials.

## The order that matters

**Read the program policy BEFORE running anything.** This is step one, not a
formality. A scanner pointed at the wrong program can cost the account, and the
policy is where that is decided.

1. **Read the full policy and scope.** Not the summary — the whole policy page.
   Note every prohibition explicitly (no brute force, no recurring scans, no PII
   beyond the minimum, no DoS, out-of-scope asset list).
2. **Classify the automation stance** (see below). If forbidden, stop.
3. **Check the two-identity requirement** (see below). If you cannot create two
   accounts, cross-identity bugs are unreachable — pick another target.
4. **Check your tool actually covers the bug classes that program pays for.** A
   specialist tool on a generalist program finds nothing.
5. **Only then configure scope and run.**
6. **Validate by hand.** Reproduce the finding manually and capture the raw
   request/response. Never submit raw tool output.
7. **Write the report yourself**, demonstrating real impact.

Steps 6 and 7 are not optional. Every "conditional" policy closes reports that
skip them.

## Classify the automation stance before anything else

Read the policy text and sort it into one of three buckets. Grep for these
keyword families:

| Bucket | Wording to look for | Action |
|---|---|---|
| **FORBIDDEN** | "do not use automated tools or scanners", "strictly prohibited", "automated tools or scans" listed as out of scope | **Stop.** Do not run a tool at all. |
| **CONDITIONAL** | "without validation", "without real impact", "without proof of exploitability", "based only on results from automated tools", "not detailed enough" | Tools allowed; raw output is not. Validate by hand. |
| **SILENT** | no automation language anywhere in the policy | Tools allowed; general platform rules still apply (no DoS, no brute force, minimum necessary access). |

**Read the conditional wording precisely — it is not a ban on tools.**
"without validation" and "based only on" forbid *submitting* scanner output, not
*using* a scanner. That distinction is the entire strategy: the tool is a force
multiplier for a human, never an autonomous submitter.

In practice most programs land in CONDITIONAL, so build the workflow around it
rather than hunting for a program that says yes.

## The two-identity filter

Cross-identity authorization bugs (BOLA/IDOR, BFLA) are found by **comparing two
identities** — that is the detection mechanism, not a nice-to-have. With one
account every hypothesis resolves to `inconclusive` and the tool produces nothing.

So a viable target must let you **self-register two accounts** on a public signup
page. Confirm this before investing any time. It eliminates most banking, telco,
and enterprise programs (KYC), however good their API is.

If a tool's findings are all `inconclusive`, suspect a missing second identity
before suspecting the tool.

## The boundary: you do not register accounts at the target

When a target needs credentials you do not have, the answer is **not** to create
them yourself — however directly the user asks. Registration is a WRITE to a
third party's system, not recon:

- It is not read-only, so it sits outside the no-mutation discipline that makes
  the rest of the work safe to run.
- It needs a legal identity, a verifiable mailbox, and often a card or a national
  ID. Inventing those values means submitting false data to a third party — a
  terms-of-service violation distinct from the bounty policy, and not one the
  program's safe harbour covers.
- The user's platform account carries the consequence, and a registration cannot
  be undone.

**Test the signup path during target SELECTION, not after committing.** Fetch the
candidate's public signup pages early and record the result. "Enterprise,
sales-gated, no public signup" is a hard filter with the same force as the
two-identity gate. Say plainly that such a target puts the cross-identity classes
out of reach.

**When the answer is "no credentials", do not stop — run the classes that need no
account.** `references/no-account-checks.md` covers them. A negative result from a
real check is worth more than an unstarted engagement, provided you report it as a
negative rather than as a clean target.

**Decline with evidence, then do the permitted adjacent work.** When the user
asks you to cross a boundary, show the concrete findings that make it impossible
(the signup pages that 403, the identity checks the flow demands) instead of
asserting a rule, and then run everything that IS reachable without it. A refusal
that ends the session wastes the turn; a refusal plus the no-account sweep is a
deliverable.

## Reputation economics drive the whole strategy

On platforms with a reputation system, a bad report costs more than a good report
earns. Treat these as the budget you are spending:

- A resolved/triaged report **gains** a modest amount.
- A **not-applicable** report **loses** roughly as much as a resolved one gains.
- **Spam** loses about twice that.
- A **duplicate filed after public disclosure** also loses — the same issue filed
  earlier is worth a small gain instead.

**The consequence:** two careless reports cost more than one good report earns. A
tool that finds more bugs but files them carelessly is **net-negative** — worse
than not running it. This is why the policy read and hand-validation come before
detection volume, and why a duplicate check is a high-value feature, not a nicety.

## Prefer export-only over automated submission

Default to producing a report you paste yourself rather than posting through an
API. It removes an entire class of accident (a bad report filed at machine speed)
for free, and it is the only mode compatible with the conditional policies above.

With export-only, a human-attestation gate and a submission volume cap become
unnecessary — the human *is* the submission path. Spend that effort on report
quality instead, because the report is now the entire deliverable.

## Choosing a target

Run the two **hard gates** first. A program that fails either is unusable no matter
how good its metadata looks, so checking these before ranking saves building a
shortlist you cannot act on.

### Gate 1 — is the asset actually reachable?

A large scope means nothing if the assets sit behind a customer login. Probe a few
in-scope hosts with a single unauthenticated GET each and record the status:

| Result | Meaning |
|---|---|
| 200 with real content | usable |
| 403 / 503 / auth wall on every path | customer-only; nothing to discover |
| 200 but an identical generic error on **every** path (incl. `/openapi.json`) | WAF rejecting non-browser clients |
| 401 | **a live protected endpoint** — the best possible recon result; see below |
| timeout / connection error | unreachable **only after a retry** — see below |

Four rules make this probe trustworthy. Each one exists because ignoring it
turned a live endpoint into a reported "dead host":

1. **Probe host+path PAIRS, not bare hosts.** A host's root routinely 404s while
the exact path the program listed answers (401 on `/oauth/token`, 404 on `/`).
Enumerating hosts alone loses every listed endpoint.
2. **Retry once before recording a failure.** A CDN-fronted host intermittently
times out on the first connection; a single attempt reported a live auth endpoint
as DEAD. A false "dead" is a false negative at the cheapest possible stage.
3. **Gate-check every URL immediately before sending it**, even though you built
it from the scope file. The assertion should never fire — which is why it is
worth having. A silent mismatch between what the scope file says and what the
guard enforces is the failure that costs the account.
4. **Enforce the program's rate limit from the scope file** (requests/minute →
seconds between requests), and keep it conservative. On a program whose only
prohibition is DoS, the rate limit IS the compliance control.

**A 401 is the strongest recon signal available.** It proves the route exists,
is protected, and is worth understanding — without touching a single record. Read
the response headers before moving on; they usually name the mechanism:

```
WWW-Authenticate: Basic realm="oauth2/client"   -> client-credentials grant
SERVLET: dispatcherServlet                      -> Java Spring
JSESSIONID=node0....node0                       -> load-balanced servlet
```

That combination says the interesting questions are about **authorization scope,
not authentication**: can a client influence the scope/tenant claim in the token
it receives, can client A's token reach client B's resources, is a weaker grant
(e.g. `password`) reachable, and does the endpoint reveal whether a given
`client_id` exists. Note that a `client_credentials` endpoint issues tokens to
*clients*, so the cross-identity comparison may not apply at all — say so rather
than assuming the usual two-account test fits.

**Low competition can be a red flag, not an opportunity.** A scope with almost no
reports relative to its size is sometimes quiet because almost nobody *can* reach
the surface — an enterprise product behind a sales login, not an overlooked gold
mine. Cross-check competition against reachability before treating it as a win.

Also confirm the asset is a **target**, not just an open host: a marketing site on a
CMS is usually excluded by policy (e.g. CMS user-enumeration is a common explicit
exclusion), so "it responds" is not the same as "there is something to test".

**Recon hints belong outside the enforcement block — and every reader must still
merge them.** When the program lists both a whole host and specific paths on it,
those paths are not enforcement rules, yet they are the best hints in the file.
Keep them under a separate top-level key (e.g. `known_urls:`) so no parser can
ever read them as a scope rule, and merge that key explicitly wherever targets
are built. **A hint no reader can see is not a hint** — the live `/oauth/token`
endpoint sat in the scope file and was never probed, because the probe reader
returned only the enforcement block.

**Write policy controls where the code actually reads them, then read them
back.** A rate limit placed under a `governance:` block while the loader reads
`scope.max_requests_per_minute` leaves the DEFAULT in force — a policy control
that looks configured and is not. After writing any control, load it through the
real loader and assert the value. Likewise, distinguish a **whole-host** asset
(entire host in scope) from a **path-only** asset (in scope at that path alone):
recording the former as a path rule NARROWS it and makes the tool refuse a URL
the program allows. Depth on both in `audit-robustness-probes`.

### Gate 2 — can you obtain two identities?

See the two-identity filter above. Confirm a public self-registration path exists.
A signup demanding a national ID number or a phone-verified identity means no
second account, which means no cross-identity comparison, which means no findings.

### Then rank what survives

- **Competition proxy:** reports received recently ÷ number of in-scope HTTP
  assets. Lower means less duplicate risk — but only among programs that passed
  Gate 1. A large program with hundreds of reports per quarter is a bad first
  target even if it pays well.
- **API-shaped assets** (`/api`, `api.`, `/v1`, `/graphql`, developer portals)
  indicate object-reference surfaces where authorization bugs live.
- **Wildcards and URL-with-path entries** widen the probe surface; URL assets also
  carry a path restriction that must be enforced (see `audit-robustness-probes`).
- **Proven payout history** (a non-zero resolved count) beats a large average.
- **Avoid** the biggest names first: enormous scope, enormous competition, and a
  specialist tool covers only a slice of what they pay for.

### Check the API architecture before committing

Establish what protocol the API speaks and whether a real machine-readable spec
exists. A host can answer 200 on every path and still be unusable:

- Fetch the spec path and compare **byte size** across several sibling paths. An
  identical response for `/openapi.json`, `/swagger.json`, and `/docs` means a
  single-page-app shell being served for all of them — there is no spec, only HTML.
- If the policy describes a **WebSocket / RPC** API, an HTTP request/response
tooling stack cannot exercise it. That is not a bug to fix mid-engagement; it is a
  target to skip unless you have already built a client for it.
- A target with **no spec** is still workable via browser-driven discovery: drive a
  real browser, capture the page's own XHR/fetch traffic, and derive endpoints from
  that. It finds routes no published spec contains — including auth endpoints.
  Note the dependency: discovery needs a page that actually calls the API, so a
  JSON-only host yields nothing to observe.

State the fit honestly, including what the tool cannot do. A target list that
omits "your tool has no XSS/SQLi/SSRF hunter" — or that lists a WebSocket-only
program to an HTTP scanner — sends the user into a program where they cannot earn.

## Working an engagement over weeks

A bounty program is not a one-session task — building tooling for it spans many
sessions, and the user will lose the thread of a long build if you only ever
report the last increment.

**Know when to stop building and start hunting.** Tooling work expands to fill any
amount of time, and the point of the tool is to find bugs. When the user signals
they want results ("just go hunt", "focus on hunting"), stop adding phases and
drive the pipeline against a real target — even if the report still has to be
written by hand. Say plainly what is missing and what the manual step is; a hunt
with a hand-written report is worth more than another week of unshipped features.

**Fix a broken capability instead of working around it.** When the user asks for a
capability to work ("make the browser agent work"), treat a non-functioning path
as the task, not as a constraint to route around. Find the root cause, fix it, and
prove it with a real run against a live target — "the tool cannot do X" is a bug
report about your own stack, not an answer.

- **Keep a progress log in the repo**, not in your head: which phase is done,
  which is in progress, which is blocked. Update it as you go, so the state
  survives a context boundary.
- **When the user asks "what are we building / how far along?", lead with the big
  picture** — the goal, the decisions already made, then done / in-progress /
  next — before any detail. That question means the anchoring was missing, so
  answer at the level they asked rather than resuming the current subtask.
- **Restate the goal and progress at natural checkpoints**, and keep an honest
  status line (including what is *not* finished) in each summary.
- **Record the user's standing decisions** (e.g. export-only rather than
automated submission, how much time they have per week) — they change the plan
  and a later session should not re-litigate them.

## Pitfalls

- **Never run a tool on a host before reading its program's policy.** The policy
  is the authorization; the tool is not entitled to assume one.
- **"In scope" is not one boolean.** An asset can be eligible for *submission* but
  not for *bounty*. Check both, or you work for free.
- **A program's own spec beats a local fixture.** Fetch the target's published
  `/openapi.json`; a stale local copy silently omits routes and produces false
  negatives on the very endpoints that pay.
- **Do not treat a clean scan as a clean target.** If the tool never authenticated,
  or you never supplied two identities, "0 findings" is a false negative, not a
  result. Assert the precondition before believing the negative. Note the two
  shapes: all-`inconclusive` usually means a missing second identity, while a
  confident `safe` verdict on a deliberately vulnerable target means the path you
  ran never loaded credentials at all.
- **Verify the entry point the operator actually runs, not a library call.** The
  same engine reached two ways can differ in wiring: a CLI subcommand reported
  `safe` on a vulnerable target while the job/API path found the bugs. A passing
  unit test or a direct function call does not prove the shipped command works.
- **Never widen a scope to make a test or demo pass.** Add an in-scope fixture
  route instead. An allow-list widened for convenience is how an out-of-scope
  request reaches production, which is the mistake that costs the account.
- **Never access more data than needed to prove the bug.** Take the minimum, never
  third-party PII, and say so in the report. This is a policy requirement on every
  program and a common cause of reports being closed.
- **Respect the platform's own automation stance too**, not just the program's.
  Platform-level rules on AI-assisted submissions and required identity
  verification apply on top of the program policy.
- **Verify a snapshot before acting on it.** Directory data, policies, and scope
  change. A shortlist built from an API pull is a starting point to confirm on the
  live program page, not a standing fact.
- **Do not present an untested workflow as validated.** If a target was chosen but
  nothing was run against it, say the target is unverified rather than implying
  results.
- **A recon result is only as good as the probe that produced it.** A false "dead"
  host, a host-only enumeration that skips the listed paths, and an informational
  hint no reader merges all silently shrink the work list. When a probe returns
  "nothing here", verify the probe before believing it.

## Reporting a finding

- **Severity is the impact IF the bug is real**, not how confident you are. Report
  confidence separately; do not let it move the severity label.
- **Include the raw request/response** a triager can replay, plus real identifiers
  and status codes. Placeholder steps (`user_a`, `{id}`) get closed as
  informational.
- **Map to the platform's taxonomy** (e.g. CWE) — reports are tagged and routed by
  it.
- **Self-consistency matters:** a severity label that contradicts its own CVSS
  score reads as a tool that does not understand its output.
- **Disclose duplicate risk yourself** when you know a similar issue is public.
