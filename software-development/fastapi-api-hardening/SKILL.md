---
name: fastapi-api-hardening
description: "Harden a FastAPI backend for production/dashboard use."
version: 1.0.0
author: hermes-curator
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [fastapi, api, auth, rbac, pagination, sse, openapi, hardening, backend]
    related_skills: [backend-api-testing, audit-robustness-probes]
---

# FastAPI API Hardening

## When to use

Adding production concerns to an existing FastAPI backend so a dashboard or external clients can consume it safely: API-key auth + RBAC, audit logging, rate limiting, pagination/filter/search, analytics aggregates, export formats, realtime streaming, job persistence, and self-documenting OpenAPI. Applies to any "make the API more powerful/complete" request on a FastAPI service.

## Build order (each layer is independently testable)

1. **Auth primitives** (`auth.py`): an API-key store that hashes keys (sha256) and never persists the raw value; an RBAC role hierarchy (`viewer < operator < admin`) with a `has_permission(role, perm)` table; an audit log (append-only JSONL — every mutation plus every auth denial); a per-key sliding-window rate limiter.
2. **Dependencies + edge middleware** (`deps.py`): a `require(perm)` dependency for fine-grained RBAC per route, PLUS an ASGI middleware that enforces auth at the edge for all `/api/*` except a `PUBLIC_PATHS` allowlist. You need both — see pitfalls.
3. **Pagination** (`pagination.py`): pipeline of filter → search → sort → paginate. Return a bare list by default; return an envelope only when the client requests a page.
4. **Analytics** (`analytics.py`): pure functions over finding dicts — severity/type/status breakdown, top endpoints/tags, daily trend, weighted 0-100 risk score.
5. **Export** (`export.py`): SARIF 2.1.0 (tool driver + rules with `helpUri` to CWE), CSV, HTML, JSON; a webhook notifier posting a Slack-compatible body.
6. **Realtime + persistence** (`jobs.py`): per-job SSE stream + a global SSE bus fanning out every job event; persist terminal job state to JSON and restore it on startup (mark restored jobs `recovered`, keep the id counter ahead of them).
7. **Docs**: FastAPI's built-in `/api/docs`, `/api/redoc`, `/api/openapi.json` — add `tags` and `description` so the schema is navigable.

## Pitfalls (each cost real debugging time)

- **Enforce auth at the ASGI middleware edge, not only per-route.** Router-level dependencies cover only routes that declare them; a middleware that merely rate-limits leaves every other endpoint open (200 with no key). Add BOTH the edge middleware (blanket coverage) and `require(perm)` (fine-grained RBAC).
- **Give every mutating route its own `require(...)`.** A missing check on a POST lets a read-only role trigger privileged work (e.g. viewer starting a job returns 200 instead of 403). Enumerate routes × roles and assert the full matrix in tests.
- **Keep the bootstrap key on the instance.** If `APIKeyStore.__init__` calls `bootstrap()` and discards the return value, the raw admin key is gone forever — only its hash was stored. Save it as `self.bootstrap_key` and have the app factory print it exactly once to stderr.
- **Pagination must be backward compatible.** Return the bare list unless `page`/`page_size` is present; adding an envelope unconditionally breaks every existing client.
- **Exempt docs/health from auth explicitly.** Put `/api/health`, `/api/docs`, `/api/redoc`, `/api/openapi.json` in `PUBLIC_PATHS`, or the Swagger UI itself becomes unreachable behind auth.
- **Redact secrets at the serialization boundary**, not per-endpoint, so no future route can leak an API key.
- **Bind to `127.0.0.1` by default**; print a warning (and require auth) when binding to `0.0.0.0`.
- **A cookie's `path` must match the URL prefix where it will be read.** A refresh cookie set with `path="/auth/refresh"` while the router is mounted at `/api/v1/auth` is never sent by the browser — login works, then the first refresh fails with no server-side error to see. Derive the path from the actual mount (`/api/v1/auth`) or use `/`, and pass the same path to `delete_cookie`, or logout leaves the cookie in place.
- **`secure=True` cookies are silently dropped over plain HTTP.** Local development against `http://localhost` needs `secure=False` gated on an env setting (keep `True` as the production default), or every authenticated request after login returns 401.
- **`localhost` and `127.0.0.1` are different sites for cookie purposes.** If the CORS allowlist and the frontend dev origin disagree on the spelling, `SameSite=Strict` cookies are not sent and auth fails only in the browser — the same requests work from curl. Pin one spelling in both places.
- **Walk each seeded role's primary user journey against its permission list.** A role missing a single permission makes the flagship demo impossible and looks like a frontend bug — e.g. a REVIEWER without `evidence.submit` cannot upload the evidence it is supposed to review. Assert journeys, not just the permission table.
- **Sync the parent when a child's review action completes.** When verify/reject updates only the child row (evidence), a dashboard aggregate over the parent's status field (`VERIFIED assignments / total`) reads 0% forever even though every review succeeded. For each aggregate, grep which code path writes the field it counts; if the review lives on a child record, the action must propagate to the parent.
- **Audit status enums for dead members.** A value no code path ever assigns (`UNDER_REVIEW`) is advertised in schemas, shows up in UI filters, and never matches a row. Grep each enum value for a writer; wire it or remove it and say it is unused — never let a phantom state reach the client contract.
- **"Today" must be computed in the viewer's timezone, not UTC.** A day window built from UTC midnight misclassifies early-morning local events for timezones ahead of UTC (05:00 WIB = 22:00 UTC the previous day, so it vanishes from "today"). Compute the window in the display timezone, or state the UTC-boundary limitation in the contract.
- **A mutating service function must `commit()`, not `flush()`, when the session is request-scoped.** With a `get_db` dependency that closes the session per request, a `flush()`-only write (e.g. marking a notification read) is discarded when the request ends: the API returns 200 with the new state but the next GET shows the old one. Commit in the service; only leave the commit to the caller if the dependency explicitly does so. In tests this shows up as an assertion passing on the response object and failing on the follow-up read.
- **Never let one helper return two domains.** A `_sev()` that returns a severity *name* ("high") when known but a SARIF *level* ("warning") when unknown makes `MAP[_sev(f)]` raise `KeyError` on any missing/unknown value. Split into `_sev_name()` (always a canonical name) and `_sarif_level()`; each caller picks one.
- **Match public paths EXACTLY, not by prefix.** `path.startswith("/api/health")` also opens `/api/healthz`, `/api/docs-secret`, `/api/openapi.json.bak` — a real auth bypass. Use `path in PUBLIC_PATHS`, with a separate explicit prefix list only for the Swagger/ReDoc asset sub-paths (`/api/docs/`, `/api/redoc/`).
- **Apply `search` before the pagination branch.** A list endpoint that only searches when `page`/`page_size` is present silently ignores the dashboard's search box (`?search=x` with no page returns everything). Filter/search/sort first, paginate last.
- **Validate required body fields at the route** (`target` non-empty, `spec` an object with `type`+`value`). `body or {}` then handing straight to the manager means `{}` starts a job with HTTP 200 instead of 422.
- **A function that returns `bool` for "found" must actually check existence.** `resolve_review` that always returns `True` makes the route emit 200 for an unknown id instead of 404.
- **Guard aggregate helpers against non-dict rows.** `Counter(f.get(...) for f in findings)` crashes on a `None` row; drop non-dict items first. Also: iterating `tags` when it is a bare string yields one tag per character — normalize `str` → `[str]`.
- **Don't write false-green assertions.** `assert "sev-error" in html` passed for the wrong reason (the class name appeared in the CSS, not on any row). Assert the exact rendered fragment (`"class='sev-error'"`), not a bare substring that also lives in the stylesheet.
- **Compile before running the suite.** `python -m compileall -q backend` catches import/syntax breakage in seconds before a multi-minute test run.
- **Never block a test on an SSE stream that may be idle.** Reading `iter_lines()` on a stream that has no new event yet blocks forever (a foreground timeout). Test the event bus by inspecting the buffered events / calling the generator's `next()` a bounded number of times, and give the stream a heartbeat yield so a live client is never hung.
- **Persist terminal job state AFTER you assign it.** A pipeline that emits its own `done` event fires it *before* `run()` returns, so a persist hook wired to that event captures `status="running"`. Persist once more after the terminal status is set, or a restart restores a finished job as if it were still running. On restore, force any non-terminal record to `interrupted` — its worker thread is gone and it can never finish.
- **Persist and restore must agree on the shape.** If restore reads `item["input"]` but the serializer never wrote an `input` key, every restart silently drops the job's parameters (targets, identities, credentials). Round-trip one record and assert equality instead of trusting the pair.
- **Sanitize anything that becomes a path segment.** `"output/" + target + "/report.md"` fails with `WinError 267` and enables traversal the moment the target contains `:` or `/`. Keep `[A-Za-z0-9._-]` and map the rest to `_` before building the path.
- **An optional dependency must degrade one feature, not 500 the endpoint.** `httpx.AsyncClient(http2=True)` raises `ImportError` when the optional `h2` extra is absent. Probe for the import and fall back (HTTP/1.1 with a larger connection pool) rather than letting a missing extra take out the whole route.
- **Never compare a SQLite timestamp against an ISO one as strings.** SQLite's `CURRENT_TIMESTAMP` writes `'YYYY-MM-DD HH:MM:SS'` (space separator) while application code typically writes ISO `'YYYY-MM-DDTHH:MM:SSZ'`. Lexically `' '` (0x20) sorts before `'T'` (0x54), so every same-day row looks *older* than the event that produced it — a time-window filter then returns nothing and the endpoint reports an empty result instead of the real rows. Normalize both sides (replace the space with `T`, parse with `datetime.fromisoformat`) before any window comparison.
- **Authenticate every identity before running probes.** A scanner whose sessions were never established reports a clean target — a false negative that looks like a pass. Log the auth result per identity and fail loudly when a required session is missing.
- **Re-run the auth matrix over every newly mounted router.** Edge middleware protects only what mounts under the protected prefix; a router added outside it is an open door. Issue one anonymous request per new route and assert 401.
- **Retry only TRANSIENT failures.** A bare `except Exception:` that sleeps `2 ** attempt` and retries spends its whole budget on errors that cannot succeed — a connection-refused target is still refused on the third attempt, so the retries are pure delay. Classify before retrying: retry read/write/pool timeouts and 5xx; fail fast on connect errors, DNS failure, TLS errors, and every 4xx (the request or the credential is wrong, and waiting will not fix either). Measured cost of getting this wrong: authenticating two identities against a dead port took 15.4s before the first pipeline phase; against a host that DROPS packets (firewall) the same pattern costs 3 x 30s timeout plus sleeps PER IDENTITY — three minutes of nothing before any real work starts. Record the reason for a fast failure (`_last_auth_error`) so it is also an explained one.
- **Bound the total time of any startup step that talks to an external target.** A pipeline that authenticates every identity before its first phase pays the target's unreachability as pure latency, and it is paid before the first useful event. Prefer fail-fast plus a short per-attempt timeout over a large retry budget, and make sure the step cannot exceed a small multiple of the timeout in total.
- **A `hasattr(obj, "x")` guard on an attribute the model never has is an always-False check.** `hasattr(current_user, "permissions")` on an ORM `User` (permissions resolved by a separate query) made `"evidence.review" in user.permissions` permanently False — every reviewer/admin got 403 on a route they own, while the owner-only happy-path test passed. Grep for `hasattr(` on model objects; if the attribute is not a column/relationship, the guarded branch is dead. Resolve through the real accessor (`get_user_permissions(db, user_id)`) instead of guessing attributes.
- **An invalid FK must be 404, not a raw 500.** Inserts that reference another table (assign task→user, create issue→event/task, create requirement→program) blow up as a database FK violation when the referenced id does not exist. Add an existence check (`_ensure_exists(db, Model, id, "User")` → `ResourceNotFound`) before insert in every service that accepts a foreign id; then probe each create/assign route with a random UUID and assert 404.
- **Validate BEFORE the irreversible side effect.** An upload pipeline that writes to object storage before looking up the target row leaves an orphan file AND 500s on the FK violation. Order: validate existence → external side effect → persist. Probe with a nonexistent parent id and assert both the 404 and that nothing was written to the store.
- **A PATCH route that reads only one field silently drops the rest.** An `update_issue_status` wired from a full `IssueUpdateRequest` used only `data.status`, so `title`/`description`/`severity`/`assignee_id` were accepted, validated, and then discarded (silent data loss); a request with no `status` crashed. Match the route to the mock/UI contract: apply every provided field, make `status` optional with state-machine validation only when present, and verify with a field-only PATCH.
- **A guardrail constant that nothing reads is dead code.** A `POLICY_STATUS = 403  # only used for repeated denials` that no code path consumes documents an intent the system does not implement — a reader will assume the behaviour exists. Either wire it or delete it.
- **A sync endpoint that calls `asyncio.run()` breaks once any library owns a loop on that thread.** FastAPI runs `def` (non-async) endpoints in a threadpool, so `asyncio.run(coro)` inside one is normally fine — until a library in that same thread is holding a live event loop. Playwright's SYNC API is exactly that: its context manager keeps an asyncio loop alive in a greenlet for as long as a browser is open, and `asyncio.run()` then raises `RuntimeError: asyncio.run() cannot be called from a running event loop`. The failure is order-dependent (only after a browser step touched that thread) and the error blames the engine, not the threading, so it reads as a bug in the thing being run. Run the coroutine on a dedicated worker thread that has no loop:

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

  General rule: when a sync library owns a loop in your thread, do not `asyncio.run` there. Probe it by launching the loop-owning component first and calling the endpoint afterwards — the failure does not appear in a clean process.
- **A library that allows only one instance per process needs an explicit shared singleton, not a retry.** Playwright's sync API can be started once per process; a second `sync_playwright().start()` finds the first instance's loop still running and raises. Wrap it in a process-wide holder with a refcount — `_acquire()` shares the running instance, `_release()` stops it only when the LAST holder lets go — so closing one component never breaks another. A retry cannot succeed here, and the failure typically surfaces as the caller's generic error value, which is indistinguishable from an unreachable target. Regression-test the count (`N holders alive -> N work`), not a single pass.

## Where a policy check must live

An authorization or scope check placed in ONE caller is a check every other caller
can bypass. The tell-tale shape is a guard at the top of a single function:

```python
if not scope_guard.is_allowed(plan.steps[0].url, plan.method):
    raise ScopeError(...)
```

That one line hides three separate defects.

- **Attach the gate to the single chokepoint that sends, not to callers.** Put it
  on the one function that actually performs the action (`send_request`,
  `send_with_identity`, the HTTP wrapper). The check then becomes a property of
  SENDING, and a new caller cannot forget it — every other path (a repeater, a lab
  endpoint, an agent tool loop) inherits it for free.
- **RAISE on a denial; never return a synthetic failure value.** Returning
  `status_code=0`, an empty body, or `None` makes a policy refusal
  **indistinguishable from "the target was unreachable"**. The caller records
  `inconclusive` and the violation is misfiled as a network problem. A refusal is a
  configuration error: give it a distinct exception type carrying the reason and the
  deciding layer.
- **Do not let a per-item `except Exception` swallow the violation.** An
  orchestrator shaped `for item in items: try: ... except Exception as e: log(e)`
  turns a refusal into a log line. The caller receives fewer results than inputs and
  cannot tell why. Catch the violation type explicitly and collect it into an
  inspectable list (`get_scope_violations()`) so "N requests were refused" is a
  first-class outcome rather than a missing row.
- **Judge EVERY item, not `items[0]`.** A plan is a SEQUENCE of requests. When all
  steps currently share a URL, checking the first merely *happens* to cover them —
  an unenforced invariant. The moment one step targets another host, an unchecked
  request goes out. Loop over every target. Probe it by making a LATER step the
  out-of-scope one: on the unpatched code the plan runs and sends it.
- **Order the layers deliberately, and fail closed in each.** Shape (does it parse,
  is there a host, is the scheme http/https) → policy/allow-list → network boundary
  (SSRF, cloud metadata) → governance (rate limit, emergency latch). The network
  layer runs AFTER the allow-list on purpose: a host authorized by NAME can still
  resolve to a metadata address (DNS rebinding), which a name-based list cannot
  catch. Every layer must DENY on an unparseable input or on an exception raised
  inside the check itself — a gate that opens when it is confused is not a gate.
- **Audit both outcomes, but weight the denials.** A silent denial is
  indistinguishable from a bug, so record every refusal with its reason and deciding
  layer. Do NOT log every allowance by default: an append-only trail with one record
  per request buries the refusals that matter. Offer an opt-in `record_allow()` for
  when a full trace is genuinely wanted.

## Verifying

- Compile, then run the new test files, then the full suite. A large suite can exceed 5 minutes — run it in the background with notify rather than a foreground timeout.
- Live-check the contract: build the app with `require_auth=True` and confirm the bootstrap key prints once and that anon → 401, viewer → read 200 / run 403 / admin 403, operator → run 200, admin → keys 200.
- Confirm no secrets leak: assert the raw key is absent from the key file and from every response body.

## Testing the auth layer

See `backend-api-testing` (section on testing auth/RBAC layers) for the auth-enabled TestClient fixture, the role-matrix assertions, and the hermetic `HH_DISABLE_AUTH` bypass that keeps legacy tests green.
