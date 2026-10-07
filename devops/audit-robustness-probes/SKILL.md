---
name: audit-robustness-probes
description: Use when auditing a codebase for micro-bugs before release.
---

# Robustness Probe Auditing

Happy-path tests miss a whole class of bugs. Probe the **boundaries and error paths** explicitly.

## High-yield probe categories

1. **Type/contract mismatches** (most common bug class):
   - Functions that sometimes return `dict` and sometimes `str`/`int` — callers doing `.get()` crash. Normalize parsed JSON: `json.loads('"str"')` returns a str, not a dict.
   - **One helper, two domains**: a formatter that returns a *name* ("high") when valid but a *level* ("warning") when invalid — a caller indexing a name→level map raises `KeyError` on the invalid branch. Probe with a missing/unknown value.
   - `f"{x}" + None` concatenation when a required arg is missing (e.g. a tool name from an untrusted JSON-RPC payload).
   - Untrusted input shapes: MCP/JSON-RPC `params` may be missing, `None`, or non-dict.
2. **Raise vs return**: a module documented to return structured errors (e.g. a Tool Layer) must not raise on network failure. Probe with an unreachable host (`http://127.0.0.1:9/`).
3. **Empty/None/garbage inputs**: `""`, `None`, `"not-a-url"`, `"http://"`, non-dict path items, non-dict operations. Also **non-dict items in a list** an aggregator iterates (`[None, "x", 5]`).
4. **Boundary values**: CVSS 0.0 and 10.0, confidence exactly 0.8/0.5, window exactly full.
5. **Auth allowlist bypass**: if public paths are matched with `startswith`, probe look-alikes — `/api/healthz`, `/api/docs-secret`, `/api/openapi.json.bak` — and assert they are NOT public.
6. **Filter/search consistency**: call a list endpoint with `?search=x` both with and without `page=1` and assert the result count matches. A search that only fires when paginated is a silent bug.
7. **Failure isolation**: force each sub-phase to raise and assert the orchestrator still completes (status `partial`, not crash). Include a missing input file (job fails, server stays healthy, other endpoints still work).
8. **Concurrency**: N threads writing to SQLite (WAL) — assert all rows persisted and zero errors. Same for an in-memory event buffer.

## Method

- Write standalone probe scripts (not pytest) that print `[OK]/[BUG]/[ERR]` per check, so one crash does not hide the rest — wrap each probe in try/except.
- Run them with the project interpreter via terminal (the sandbox kernel may lack project deps like `yaml`).
- A probe that crashes is itself a finding: capture the traceback, it usually points straight at the bug.
- Distinguish real bugs from probe-authoring mistakes (wrong arg order, wrong signature, wrong expectation). Re-verify each `[BUG]` in isolation before fixing — many "bugs" are the probe calling a method that doesn't exist or passing the wrong constructor args. Read the real signature first.
- **A negative result is only as good as the identity that produced it.** An authorization scanner that never authenticated reports "0 findings" on a deliberately vulnerable target — a false negative that looks like a clean pass. Before trusting any "nothing found" result, assert the precondition (identities authenticated, tokens present). This class of bug is invisible to happy-path tests because the code runs without error.
- **Two timestamp formats compared lexically is always a bug.** SQLite `CURRENT_TIMESTAMP` yields `'YYYY-MM-DD HH:MM:SS'` (space) while app code often uses ISO `'…T…'`. `' '` (0x20) sorts before `'T'` (0x54), so a same-day row looks older than an event that produced it. Normalize both sides before any window comparison.
- **Slice defensively on values read back from SQLite.** `(row["col"] or "")[:10]` raises `TypeError: 'int' object is not subscriptable` when the column stores a numeric-looking value (e.g. CDX `YYYYMMDD`). `str(...)` first.
- **Sweep by pattern, not by module.** After the per-area probes, grep the whole tree for the dangerous patterns (`.get(x).lower()`, `".." + x.get(..)`, `for i in x.get(..)`, `list(x.get(..))`, `.get(..).get(..)`), plus the newly-found classes: `[\"...\"][:N]` on DB reads and `http2=True` without the optional `h2` dep — this finds the same bug class in modules no probe touched.
- **A probe expecting a raise is not a bug.** If the code deliberately raises a clear domain error (`OrchestratorError('No agents registered')`, `PlanValidationError`, `ScopeConfigError`), assert the raise instead of asserting success.
- **A bare string is not a list.** `allowed_methods: GET` (YAML) iterates per character; `tags: "authz"` yields `a,u,t,h,z`; `depends_on: "t1"` splits into `t,1`. Normalize any config/data field that may be a string before iterating (`_as_list`, `[v] if isinstance(v, str)`).
- After fixing, add a regression test per bug and re-run the FULL suite twice (catch flakiness).
- **Beware false-green assertions.** A test that greps a bare substring can pass for the wrong reason (e.g. `assert "sev-error" in html` matched the CSS class name, not a rendered row). When a probe reveals the test was passing wrongly, tighten the assertion to the exact rendered fragment.
- **A prefix selector silently over-matches.** `[data-testid^='copilot-persona-']` also matches the trigger `copilot-persona-select`, so a "menu has 4 entries" assertion always counts 5 and can never pass; `^='copilot-trace-'` matches every `copilot-trace-toggle-<id>` button, so a "collapsed" count is never 0. Add an explicit `:not([data-testid='...'])` / `:not([data-testid^='...'])` exclusion. Any `^=` selector deserves a count printed in the detail so an over-match is visible.
- **Never use a fixed `sleep()` in a browser probe.** A `sleep(1.8)` after a nav click expired while the page was still on its loading skeleton (a larger bundle slowed first paint), and the check failed with an *empty detail* — a silent failure that looked like a product bug. Use `wait_for_function` on the expected end state (`root testid OR honest empty state`, ~12s).
- **Probe the actual product flow, not a synthetic shortcut.** Dispatching a `window` event directly to prove state injection works passes even when the real chat flow never reaches the page. Drive the real path (send the chat message, approve the gate) and assert the end state.
- **Assert on the delta, not the total.** A step that counts `widgets == 0` breaks once an earlier step legitimately created one. Capture `before` and assert `after > before`, and inspect `.last` (the newest) rather than `.first`.
- **When a probe clicks a button that persists across steps, scope the click to the unresolved instance.** A stale approval card from an earlier step swallowed a later click and re-ran the wrong tool — the probe was accidentally correct to fail.
- **Prefer a `probe_all.py` runner** that executes every probe suite and prints one summary — cheap to re-run after each fix and in CI. Keep adding suites as you cover new modules; the count growing (10 → 19) is the coverage growing.

- **A guardrail that mutates process-global state is itself a bug.** `socket.setdefaulttimeout()` is process-wide: set it to bound a DNS lookup and leave it set, and every later socket operation in the process inherits your timeout — surfacing as unrelated, non-reproducible failures far away from the cause. Save the previous value and restore it in a `finally`. Probe it: assert the timeout is unchanged after the call, and that a pre-existing value is preserved.
- **A one-in-N flake needs the traceback, not a theory.** "It passed twice, so it's pre-existing" is an inference, and a wrong one costs credibility. Run the full suite to a FILE, then read the actual exception before characterising it. If the traceback was never captured, say "cause unknown" — do not substitute a plausible story for evidence, and do not claim a fix resolved a failure you never reproduced. **A real bug found while investigating a flake is still worth fixing, but fixing it does not prove it caused the flake.** Verify causation by re-applying the suspected defect and confirming it reproduces the failure; if it does not, the flake's cause remains unknown.

## Auditing a scanner / detector for false negatives

A scanner's worst failure is not a crash — it is reporting a clean target when
the bug is right there. Unit tests cannot catch this because they fake the
network boundary. You need a live target and hand-confirmed ground truth.

- **Establish ground truth by hand FIRST**, with direct HTTP calls, then assert the engine finds it. A test that only checks "endpoint returned 200" proves nothing about detection.
- **Look for the never-probing hunter.** The signature is a status pair of `0/0` and a verdict of `inconclusive` for every hypothesis. Read the executor: if `baseline_status` / `test_status` are assigned as literals and no HTTP call appears in the method, the detector is a no-op that certifies targets as clean.
- **Check that the two sides of a comparison are actually different.** `privilege_identity = admin or normal[0]` with no admin configured makes both sides the SAME identity — a meaningless comparison that still reports any 2xx as an escalation. Assert the two identities differ, and lower the confidence when they cannot.
- **A verdict needs to know how strong it is.** When only one identity was probed, a 200 on an admin route is still a real finding but weaker evidence than a two-identity comparison. Record the difference in the confidence and the evidence rather than reporting both as equally certain.
- **Feed the scanner the target's OWN spec.** Pointing a hunt at a stale local fixture silently omits routes the fixture does not know about — which is exactly how a real admin route gets missed. Prefer the target's published `/openapi.json`.

## When one fix exposes the next

A latent crash can stay hidden behind an upstream bug: if a detector never
produces findings of type X, then every code path that formats a type-X finding
is never executed. Fixing the detector makes the formatter reachable, and it
crashes. After fixing a "produces nothing" bug, **re-run the full end-to-end path
that consumes the new output** — do not stop at the detector's own tests.

Related shape bug worth probing: a column written by several components with
different types (one stores a JSON object, another stores a JSON *string*). Code
that parses then calls `.keys()` raises the moment the second writer's row
exists. Normalise at the read boundary (dict / JSON string / list / scalar /
non-JSON text) instead of trusting the shape.

**Fixing a detector breaks tests that encoded its silence.** Expect count
assertions like `assert findings == 8` to fail once the detector works, because
that number silently meant "this hunter finds nothing". Resolve each failure by
asking which side is wrong:
- If the test asserted a **count**, it was testing a magic number instead of the contract. Rewrite it to assert the relationship (non-empty, list matches the job count, report total matches stored rows) — do not just lower the number to the new value.
- If the test asserted **"a clean target has no findings"** and it now fails, check the FIXTURE. A fake that returns 200 to a regular user on an admin route is modelling a *vulnerable* target while the test claims a clean one. The detector is right; fix the fake.

## Scope engines, API clients, report claims

Depth moved to `references/scope-and-api-clients.md`. Load it when auditing a scope
engine, an API client, or a report generator. The headline rules:

- **A global path allow-list cannot express per-host rules.** Mixing a
  path-restricted host with an open host leaks: a `/*` from the open host widens the
  restricted one, so a URL outside the allowed path is permitted. That is an
  out-of-scope request. Add per-host rules evaluated BEFORE the global list.
- **A deny-list needs its own field.** `blocked_paths` matches URL paths, so a
  hostname placed there does nothing. Add `blocked_domains`, checked before the
  allow-list, or a wildcard re-opens the exclusion.
- **Keep "in scope to test" and "eligible to be paid" as separate flags.** One
  boolean produces a scope that maps fine and pays nothing.
- **Report unsupported inputs, never drop them silently** — an untestable in-scope
  asset is a false negative at the scope level.
- **A pagination `next` link must be requested verbatim.** Re-parsing its query and
  passing it back as `params` double-encodes it, so pagination repeats page 1
  forever while appearing to work.
- **API client credentials come from the environment**, never appear in `repr`, the
  URL, or an error message, and retries cover ONLY what a retry can fix (429, 5xx,
  transport) — never a 401/404.
- **Severity is the impact IF the bug is real; confidence is the strength of the
  evidence.** Report them separately. Tempering severity by confidence is cosmetic:
  an unconfirmed finding is Not Applicable whatever label it carries. Gate the
  submission instead. Any line showing a severity label beside a CVSS score must be
  self-consistent.
- **A column written by several components needs a shape probe.** Double-encoded
  JSON makes a confirmed finding render as `status=None`. Fix at the writer, make
  the reader tolerant, and assert the round trip end-to-end.

## Test doubles that replace the thing under test

**An `autouse` fixture that replaces a method will silently disable any test of
that method.** A suite-wide fixture stubbing `RequestMutator.send_with_identity`
(so pipeline tests never touch the network) also replaced it for the tests
written to verify the send path itself. Those tests then asserted against the
fake: the gate under test never ran, and one test failed with `DID NOT RAISE`
while the real code was correct.

Symptoms: a test fails in the suite but the same scenario passes in a standalone
repro. Before debugging the product, check `conftest.py` for an `autouse` fixture
touching the class or function you are testing.

Fix: capture the genuine function at IMPORT time (before the fixture can patch
it) and restore it in the test class's own fixture:

```python
# module level, evaluated at import
_REAL = RequestMutator.send_with_identity

class TestSendPath:
    @pytest.fixture(autouse=True)
    def _restore(self, monkeypatch):
        monkeypatch.setattr(RequestMutator, "send_with_identity", _REAL)
```

## Fail closed, and make the denial visible

A gate that opens when it is confused is not a gate: an unparseable URL, a
missing host, or an exception inside a check must all DENY.

Order the checks so the most decisive reason is reported first. `file:///etc/passwd`
has NO hostname, so a host-first order reports "no host" and hides the real
problem (a non-HTTP scheme). **Check the scheme before the host.**

**A denial that only logs is invisible.** When a caller catches exceptions
generically (`except Exception: log(...)`) and continues, a refused item simply
disappears from the results — the operator sees "fewer findings", not "N
refused". Record refusals in a dedicated, inspectable list AND log them.

Probe it: assert the refusal appears in that list, not merely that the log was
written.

## Secret masking: probe the SHAPES, not one example

A DLP regex tuned on `password=hunter2` missed the commonest credential shape of
all — `?token=...` in a URL — because the pattern listed `access_token` and
`refresh_token` but not bare `token`. It also required a value of 4+ characters,
so `password=x` passed through unmasked.

Probe with a table of shapes and assert BOTH directions:
- must mask: `?token=`, `password=x`, `api_key=`, `session_id=`, `otp=`, JSON
  `"password": "x"`, `Authorization: Bearer ...`
- must NOT mask: an ordinary URL (`/users/42`), the word `session` alone

Include the negative cases. A masking rule that redacts ordinary text is its own
bug: it destroys the evidence a report depends on.

## Evidence capture, report claims, test doubles

Depth moved to `references/evidence-and-reports.md`. The headline rules:

- **Capture what was SENT, not what was built.** A mutation layer (`swap_identity`
  deep-copy + auth headers) means the caller's object is NOT what went on the wire.
  Capturing it yields a transcript with no `Authorization` header, and a triager
  concludes the request was unauthenticated — the opposite of the finding. Retain
  the sent request at the send boundary, plus a bounded history so a cross-identity
  test yields two DISTINCT exchanges.
- **Redact at the boundary** with the same DLP rules as the rest of the system. A
  transcript that leaks the researcher's own session is a new vulnerability.
- **Bound bodies and mark the cut.** Silent truncation makes the reader think the
  response ended there.
- **Reproduction steps are real or explicitly absent.** A skeleton that reads like
  real evidence invites a submission that cannot be reproduced. Probe the negative.
- **Test doubles must match the REAL return shape.** If code calls
  `response.json()`/`.text`/`.content`, a fake returning your own dataclass fails
  with an AttributeError that looks like a product bug.
- **Severity is the impact IF the bug is real; confidence is the strength of the
  evidence.** Report them separately; a severity label must never contradict the
  CVSS score printed beside it.
- **A column written by several components needs a shape probe.** Double-encoded
  JSON makes a confirmed finding render as `status=None`.

## A browser context is not an identity

**Switching a browser context does NOT authenticate the request.** If a fetch
helper takes an `identity` parameter and only uses it to pick a page/context, every
request goes out ANONYMOUS — and an authorization test then compares 401 against
401 and reports `inconclusive` forever. That is the worst detector failure: a
permanent false negative that reads as a clean target.

Wire the identity to CREDENTIALS, not just to isolation:
- fetch the identity's auth headers and set them on the request/page
- merge them UNDER any caller-supplied headers, so an explicit header still wins
- do it on BOTH the browser path and the HTTP fallback, or a browser-less
  environment silently goes anonymous
- log when a token cannot be obtained — an anonymous probe is legitimate, but it
  must be visible, not silent

Probe it: fetch as two identities and assert the two requests carry DIFFERENT
authorization values. Same value (or none) means the comparison proves nothing.

Related wiring bug: passing `identity_manager` to the HUNTER but not through to the
AGENT. The hunter looks configured and the agent stays anonymous. Assert
`hunter.agent.identity_manager is manager` in a test.

## Playwright sync API keeps an event loop alive in the thread

While a browser agent is open, `asyncio.run(coro)` in the SAME thread raises
`RuntimeError: asyncio.run() cannot be called from a running event loop`. The
loop belongs to Playwright's greenlet and stays alive until `close()`.

Symptoms: a sync FastAPI endpoint that uses `asyncio.run()` fails only after a
browser step ran on that threadpool thread, with an error blaming the engine
rather than the threading constraint.

Fix: run the coroutine on a dedicated worker thread that has no loop.

```python
def _run_coroutine_sync(coro):
    box = {}
    def _worker():
        try: box["result"] = asyncio.run(coro)
        except BaseException as exc: box["error"] = exc
    t = threading.Thread(target=_worker, daemon=True)
    t.start(); t.join()
    if "error" in box: raise box["error"]
    return box.get("result")
```

Rule: when a sync library owns a loop in your thread, do not `asyncio.run` there.

## Two Playwright sync-API traps that look like a broken target

### Trap 1: only ONE `sync_playwright().start()` per process

Playwright's sync context manager keeps an asyncio loop alive in a greenlet and
refuses to start when it sees one already running:

```python
self._loop = asyncio.get_running_loop()   # finds the PREVIOUS instance's loop
if self._loop.is_running():
    raise Error("...Playwright Sync API inside the asyncio loop.")
```

So the SECOND `BrowserAgent` in a process always fails. If the failure surfaces
as `status_code: 0`, it is indistinguishable from "target unreachable" — a hunt
that built two agents (BOLA + BFLA) reports a CLEAN TARGET instead of an error.

Fix: one process-wide instance with a refcount. `_acquire_playwright()` shares
it, `_release_playwright()` stops it only when the last holder lets go. Never
retry — a retry cannot succeed. Regression test: `N agents alive -> N works`.

### Trap 2: a live loop blocks `asyncio.run()` in the same thread

While any browser agent is open, `asyncio.run(coro)` in that thread raises
`RuntimeError: asyncio.run() cannot be called from a running event loop`. A sync
FastAPI endpoint (run in a threadpool) that calls `asyncio.run()` therefore dies
only after a browser step touched that thread — and the error blames the engine,
not the threading.

Fix: run the coroutine on a dedicated worker thread that has no loop.

```python
def _run_coroutine_sync(coro):
    box = {}
    def _worker():
        try: box["result"] = asyncio.run(coro)
        except BaseException as exc: box["error"] = exc
    t = threading.Thread(target=_worker, daemon=True)
    t.start(); t.join()
    if "error" in box: raise box["error"]
    return box.get("result")
```

### Testing rules that came out of these

- **Never let a transport failure and a scope/config rejection share a sentinel**
  (`status_code: 0`). A rejected request must be distinguishable from a dead
  target, or a silent false negative is indistinguishable from a clean scan.
- **Do not widen scope to make a test pass.** If the shipped scope allows only
  `/api/*`, add an in-scope route to the fixture instead of allowing `/app`.
- **A test that needs a clean thread must not assume one.** If the suite may
  leave a loop running, drive the scenario through the helper under test rather
  than `asyncio.run`, or the test fails for the reason it is testing.

## A test that passes alone but fails in the suite: find the leaked state, don't retry

"Flaky" is a guess. Establish which of three causes it is, with evidence:

1. **Resource contention** — count the relevant processes before and after a
   full run. A stable count means no leak; a rising one is a real bug.
2. **Leaked process-global state** — a plugin that reports the first test after
   which the state appears. Do not guess which test; instrument it.
3. **A real product bug the suite happens to expose** — this is the valuable one.

### Worked example: Playwright sync API + running asyncio loop

Symptom: `tests/test_browser_live.py` passed alone, failed with
`status_code: 0` in the full suite. A first theory (browser contention from a
concurrent hunt) was WRONG — it also failed in a clean environment.

The real cause was in Playwright's source:

```python
try:
    self._loop = asyncio.get_running_loop()   # finds the PREVIOUS instance's loop
if self._loop.is_running():
    raise Error("...Playwright Sync API inside the asyncio loop.")
```

**Playwright's sync API can be started only ONCE per process.** A second
`sync_playwright().start()` finds the first instance's loop still running and
raises. Because the failure surfaced as `status_code: 0`, it was
indistinguishable from "target unreachable" — a hunt that built two agents
(BOLA + BFLA) would silently report a CLEAN TARGET instead of an error.

Fix: a process-wide shared instance with a refcount (`_PW_STATE`, `_PW_LOCK`,
`_acquire_playwright`, `_release_playwright`). Agents share one Playwright; the
last release stops it. Closing one agent never breaks another.

Rules that came out of this:
- **Never let a transport failure and a scope/config rejection share a sentinel**
  (`status_code: 0`). A rejected request must be distinguishable from a dead
  target, or a silent false negative is indistinguishable from a clean scan.
- **A library that allows one instance per process needs an explicit shared
  singleton**, not a retry — retrying cannot succeed.
- **Prove the count**: `N agents alive -> N works` is the regression test; "it
  passed once" is not.

## Scope rules that silently invert: bare-host vs path-only

Two mistakes in a scope file change WHAT GETS TESTED without any error:

**1. A bare-host asset means the WHOLE host.** If H1 lists
`api.example.com` as a bare asset AND also lists
`http://api.example.com/oauth/token` as a separate URL asset, the bare entry
grants the entire host. Emitting a `host_paths` entry for that host NARROWS it
to just `/oauth/token`, and the tool then refuses a URL the program explicitly
allows — a scope-level false negative.

Rule: track `whole_hosts` while parsing; drop any `host_paths` entry for them.

```python
host_paths = {h: ps for h, ps in host_paths.items() if h not in whole_hosts}
```

**2. A path-only asset covers ONLY that path.** A host that appears *only* as
`http://api.example.com/v2/query/iplist` is in scope at that path and nowhere
else. Probing its root is an out-of-scope request.

Both rules must hold at once, and they are opposites. Assert them separately:

| URL | Expected |
|---|---|
| bare-host `/anything` | ALLOW |
| path-only `/listed/path` | ALLOW |
| path-only `/SECRET` | DENY |

**3. Policy controls must be in the block the code reads.** `ScopeGuard` reads
`scope.max_requests_per_minute`. Writing `governance.rate_limit_per_minute`
leaves the default of 60 in force — a rate limit that looks configured and is
not. After writing a control, read it back through the real loader and assert
the value; do not trust the file.

**4. A recon probe needs one retry.** A Cloudflare-fronted host intermittently
times out on the first connection. Recording that as DEAD hides a live endpoint
(`/oauth/token` answered 401 only on the second attempt). A false "dead" is a
false negative at the cheapest stage to avoid one.

## Live-browser tests fail under concurrency, not from your change

Tests that launch a real browser fail with `status_code == 0` when another
browser process is running at the same time. The tell: **the same file passes when
you run it alone.**

Before blaming your change, check for leftover processes:
- count browser/node processes BEFORE and AFTER a full run — a stable count means
  no leak; a rising one means `close()` is not working
- re-run the failing file alone; if it passes, the failure was contention
- clean up stragglers (`taskkill`) and re-run the suite

Do not record "browser tests are flaky" as a conclusion. Either the browser
leaks (a real bug) or the suite ran while another browser held resources (an
environment problem). Distinguish them with the count, not with a guess.

## Fix pattern

Make the boundary total: normalize return types at the parse boundary (`_parse_*` helpers always return `dict`), validate required identifiers before string concatenation, and convert network/transport exceptions into structured error results at the module edge.

## State that must survive a navigation

A **transient event is lossy** whenever the action that produces it also navigates. If directive A is "switch to page P" and directive B is "inject this payload into P", B is dispatched before P mounts, so P's listener is not attached yet and the event is dropped — the UI reports success while the page shows nothing.

Fix: retain the payload in shared state (survives the navigation) *and* broadcast the event (an already-mounted page reacts immediately). The consuming page reads state on mount and subscribes for later updates. Probe both paths: live dispatch **and** inject-then-navigate.

Related, same family:
- **A resolved approval card must disable its buttons.** A decided HITL/confirm card left clickable lets a stale card re-fire an already-executed action — real double execution. Mark it resolved (e.g. once any later message exists) and replace the buttons with a status line; assert `resolved cards expose no approve button`.
- **Validate a tool's required params against its schema before dispatch.** Executors that accept `**kwargs` for tolerance silently run with an empty value and report success when a caller (or an LLM) mistypes a key (`url` for `endpoint`). Return `missing required parameter(s): …` with `ok: false` instead of a green result for work that never happened.

## LLM tool-calling gateways

- **Verify function calling directly before designing around it.** An OpenAI-compatible gateway may return a proper `tool_calls` array for a simple request yet leak tool-call markup into `content` as plain text once the conversation already contains `role: "tool"` results. The user then sees raw protocol noise in the chat. Sanitize the text; if nothing usable remains, return `None` to trigger one explicit "summarise, emit no markup" retry and then a deterministic data-grounded fallback.
- **Never route deterministic UI control through an LLM.** Opening a tab or toggling a modal must be a pattern match (~1ms), not a 3–8s round-trip that can also pick the wrong tool. Use a fast path for unambiguous commands and the model only for open-ended reasoning; have both emit the same response contract so the frontend has one code path.
- **A mixed tool loop must degrade, not fail.** Wrap the tool-calling attempt so an unsupported/garbled gateway falls back to a plain completion and then to a grounded answer built from real stored data.
- **Gate the model's tool calls with the SAME policy as the user path.** A tool loop that calls the executor directly bypasses every approval check the UI enforces. If the model can invoke a destructive tool, an injected instruction becomes remote code execution on the target. Apply the tier/approval gate inside the loop and return a confirmation card instead of executing.

## Guardrails: what to build and what to probe

Layered defences, each assuming the layer above can fail.

**SSRF / network boundary**
- Resolve the hostname and judge the ADDRESS, not the name: an allowlisted name that resolves to `169.254.169.254` or an RFC1918 address still leaves the engagement (DNS rebinding).
- Cloud metadata (`169.254.169.254`, `169.254.170.2`, `100.100.100.200`, `fd00:ec2::254`) must be a HARD block that an allowlist entry cannot open — an allowlist entry for the metadata IP is precisely the confused-deputy mistake.
- Fail CLOSED on an unresolvable host; never treat "cannot resolve" as "public".
- Exempt `localhost` from the rebinding rule (RFC 6761 reserved, cannot be rebound) or you break every local lab target.
- Strip IPv6 zone indexes (`fe80::1%eth0`) and brackets before parsing.

**Untrusted-code sandbox**
- Validate the AST before executing: deny dangerous imports, `eval`/`exec`/`open`/`__import__`, dynamic `getattr`/`setattr`, and dunder chains (`__subclasses__`, `__globals__`, `__code__`).
- Make the import allowlist SUBMODULE-aware — `urllib.parse` is pure parsing while `urllib.request` does network I/O; a root-only check forces you to choose between a false positive and a real hole.
- Scrub the child environment to a minimal set: no `PATH`, no `PYTHONPATH`, no `*_KEY`/`*_TOKEN`. Run with `-I -S` so a planted module cannot be imported.
- `resource` is POSIX-only — guard the import or the module fails to load on Windows, and the timeout is then your only remaining quota.

**Indirect prompt injection**
- Wrap target-authored content in an explicit isolation envelope and state in the system prompt that it is DATA, never instruction.
- Neutralize the payload BEFORE wrapping so it cannot close the envelope early; assert the wrapper contains exactly one closing tag, at the end.
- Treat the heuristic scanner as a tripwire that TELLS the operator, not as a filter — the real defence is the separation plus the tool gate.

**Approval integrity**
- Bind an approval to `action+tool+params+expiry` under an HMAC so approving one action cannot authorize a different one; verify that tampering with a param invalidates it.
- Burn the token on use and PERSIST the burn, or a restart resurrects it within its TTL.
- Assert the resolved UI state and the server-side burn independently — defence in depth means either alone would stop a replay.

**DLP / egress**
- The chat bubble, the tool-call trace, and the audit log are all egress paths; mask at the boundary so no future route can leak.
- Match the JSON-QUOTED form (`"password": "x"`), not just `password=x` — a bare-name pattern silently misses the JSON case, which is the one that appears in API responses.
- Use replacement FUNCTIONS, not backslash backrefs: `r'\1 ' + REDACTED` is fragile and can emit the wrong literal.
- Keep masked output parseable (preserve quotes) so a masked payload is still usable.

**Audit trail**
- Hash-chain each record with the previous line's SHA-256; then deleting or editing any record breaks every later link. Probe both (remove a line, edit a line).
- Never let the audit writer raise into the request path.

**Emergency stop**
- A kill switch that can fail is not a kill switch: run each subsystem hook in its own try/except and report per-subsystem outcomes.
- Make it idempotent, and require an explicit `confirm=true` so a stray request cannot halt an engagement.
- Persist the latch for the process lifetime and require an explicit re-arm; a stopped system must not silently resume.
- Block new offensive work while latched, and refuse the APPROVAL REQUEST too — a confirmation card that cannot be executed is a lie.
- Give the panic button TWO affordances and assert at least one is always clickable: an open side panel can cover a TopBar button, and a panic button that scrolls out of reach is not a panic button.
