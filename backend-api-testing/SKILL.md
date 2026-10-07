---
name: backend-api-testing
description: "FastAPI testing with pytest, httpx, async SQLAlchemy."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [testing, fastapi, pytest, httpx, sqlalchemy, async, backend]
    related_skills: [systematic-debugging, dogfood]
---

# Backend API Testing

## Overview

Testing FastAPI backends with pytest, httpx, and async SQLAlchemy. Covers unit/integration tests, live E2E smoke tests, and Docker-based test infrastructure.

## When to Use

Use this skill when:
- Writing pytest integration tests for FastAPI backends with async SQLAlchemy
- Setting up test infrastructure (database, mocks, fixtures)
- Running live E2E smoke tests against a running server
- Debugging async test failures (connection pool, cookie, schema issues)
- Implementing OCC (Optimistic Concurrency Control) patterns

## Prerequisites

- FastAPI backend with SQLAlchemy async ORM
- PostgreSQL (local or Docker)
- pytest + pytest-asyncio + httpx installed
- Docker (optional, for integration tests)

## Workflow

### 1. Test Infrastructure Setup

**Database URL encoding**: Passwords with `@`, `:`, `/`, or other special chars MUST be URL-encoded in connection strings. Use `urllib.parse.quote_plus()`.

```python
from urllib.parse import quote_plus
TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{USER}:{quote_plus(PASSWORD)}"
    f"@{HOST}:{PORT}/{DB}"
)
```

**NullPool for test isolation**: Use `NullPool` instead of connection pool for async tests to avoid "another operation is in progress" errors.

```python
from sqlalchemy.pool import NullPool
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
```

**DDL migration execution**: Multi-statement DDL migrations cannot be executed via `conn.execute(text(ddl))`. Use raw asyncpg connection instead.

```python
raw_conn = await conn.get_raw_connection()
await raw_conn.driver_connection.execute(ddl)
```

### 2. Writing Integration Tests

**Per-test database cleanup**: Truncate all tables between tests to prevent data leakage.

```python
@pytest_asyncio.fixture(autouse=True)
async def clean_db(db_session):
    for table in reversed(Base.metadata.sorted_tables):
        await db_session.execute(text(f"TRUNCATE {table.name} CASCADE"))
    await db_session.commit()
```

**Mock external services**: Override dependencies for external services (MinIO, Redis) in conftest.py.

```python
@pytest_asyncio.fixture
def mock_storage():
    return MockStorageClient()

@pytest_asyncio.fixture
def override_storage(mock_storage):
    def _override():
        return mock_storage
    app.dependency_overrides[get_storage] = _override
    yield
    app.dependency_overrides.pop(get_storage, None)
```

**Auth bypass in tests**: Generate JWT directly instead of going through login flow.

```python
def get_auth_cookies(user_id: UUID, role: str) -> dict:
    token = create_access_token(user_id, role)
    return {"access_token": token}
```

### 3. Live E2E Smoke Testing

**Per-user clients**: Use separate `httpx.AsyncClient` instances per user to avoid cookie conflicts.

```python
pic_client = httpx.AsyncClient(base_url=BASE_URL, follow_redirects=True)
await pic_client.post("/auth/login", json={"email": ..., "password": ...})
# Cookies auto-managed by httpx on same client instance
```

**Cookie security**: `secure=True` cookies are NOT sent over HTTP. For local testing, set `secure=False` in cookie configuration.

**Schema consistency**: Test database and production database MUST have identical schemas. Use DDL migrations for both, not `Base.metadata.create_all()`.

**Seed data**: Production database needs test users with known credentials for smoke tests. Make the seeding script idempotent (upsert by email, re-assign roles) so the smoke test, the UI builder, and manual demos all draw from one account source — and re-run it after any schema reset.

**A smoke script silently drifts from the API.** Renamed routes and moved parameters leave the script calling URLs that no longer exist, so it fails with 404/405 that look like backend bugs. Dump the OpenAPI spec (`app.openapi()`) and cross-check every call — method, path, and parameter location — before debugging a failing step; also confirm the actor of each step actually holds the permission the endpoint requires, or the script fails at a step whose real blocker is elsewhere.

**A fake at the HTTP boundary cannot catch a detector that never probes.** When
tests monkeypatch the request layer, a component that never sends a request still
runs cleanly and returns an empty result — the suite stays green while the
component is a no-op that certifies targets as clean. Cover this class with a
live-target audit, not a unit test:

1. Establish ground truth BY HAND first (direct calls against a deliberately vulnerable target), so you know what detection must find.
2. Point the engine at the target's OWN published spec (`/openapi.json`), not a local fixture — a stale fixture omits routes, which is precisely how a real route gets missed.
3. Assert the engine finds each hand-confirmed item, and fail the audit on a miss.

The signature of the bug is a status pair of `0/0` and an `inconclusive` verdict
for every case: read the executor, and if the status variables are assigned as
literals with no request call anywhere in the method, the detector does nothing.

Also check that both sides of a comparison are actually different — a fallback
like `privileged = admin or normal[0]` makes both sides the SAME identity when no
admin is configured, so the comparison is meaningless while still reporting any
2xx as an escalation. When only one side could be probed, record that in the
confidence and the evidence instead of reporting it as equally certain.

### 4. Common Pitfalls

| Pitfall | Why | Fix |
|---------|-----|-----|
| `cannot perform operation: another operation is in progress` | asyncpg doesn't support concurrent ops on same connection | Use `NullPool` |
| `functions in index predicate must be marked IMMUTABLE` | DDL migration has indexes with non-immutable functions | Create indexes separately or use `Base.metadata.create_all()` |
| `Don't know how to join to X` | SQLAlchemy relationship ambiguity with multiple FK paths | Add explicit `foreign_keys` to relationship |
| `ChunkedIteratorResult has no rowcount` | `.returning()` changes result type | Remove `.returning()` or use separate query |
| Cookies not sent in requests | `secure=True` cookies rejected over HTTP | Set `secure=False` for local testing |
| 500 error on create | Audit log insert fails due to missing column | Ensure schema matches between test and prod |
| `- O...` in the `pytest -q` summary | Abbreviated `OSError` — a teardown/cleanup failure, NOT an assertion failure | Wrap the body in `try/finally`; see `references/flake-diagnosis.md` |
| Suite flakes only when run whole | Inter-test state pollution; the repro unit is the suite, not the test | Reproduce with the preceding files + target in one process, never a `-k` soak loop |
| Test flips green/red with no code change | The fixture's `base_url` points at a real service the suite does not manage, so an unrelated process decides the result | Prove it by toggling that service, then fix the slow-to-fail product path and size the wait from the measured worst case — see section 8 |

### 5. OCC (Optimistic Concurrency Control)

Use atomic UPDATE with version check instead of read-then-write:

```python
result = await db.execute(
    sql_update(Task)
    .where(Task.id == task_id, Task.version == expected_version)
    .values(status=new_status, version=Task.version + 1)
)
if result.rowcount == 0:
    raise OCCConflictException()
```

This prevents race conditions without explicit locking.

### 6. Testing auth / RBAC layers

- **Isolate per test**: build the app with `require_auth=True` and pass explicit `key_path`/`audit_path` under `tmp_path` so keys and audit logs never bleed between tests.
- **Assert the full role matrix**, not a single case. Create one key per role from the store, then check: no key → 401; viewer → read 200, run 403, admin 403; operator → run 200, admin 403; admin → admin 200. A missing per-route dependency shows up here as 200 where 403 was expected.
- **Keep legacy tests green with a hermetic bypass**: `os.environ.setdefault("HH_DISABLE_AUTH", "1")` in `conftest.py`, and have the auth tests set it to `"0"` explicitly. This lets the whole existing suite run unchanged while auth is exercised in its own file.
- **Assert hashed-at-rest**: read the key file and assert the raw key string is NOT present while its hash IS — proves you never persist plaintext.
- **Both header styles**: verify `X-API-Key` and `Authorization: Bearer` are accepted.
- **Suite runtime**: an API integration file that drives the full job pipeline can take minutes; run the full suite in the background with notify instead of a foreground timeout.
- **Capture the full suite output to a FILE, not a truncated pipeline.** Truncating the output loses the traceback you need for a rare failure, and `pytest -q` abbreviates the exception class to its first letter (`O...` = `OSError`). If a test flakes once in N runs, read the real traceback before characterising the cause — if it was never captured, the cause is **unknown**, and a plausible story is not a substitute.
- **`try/finally` around the body, not a bare `with` block.** Without it, a `TemporaryDirectory` cleanup failure on Windows (a still-open SQLite `-wal`/`-shm` handle, an unclosed log handler) surfaces as a test failure and hides that every assertion passed. A conftest `gc.collect()` "so Windows releases SQLite file handles" is documentation of this class — a signal, not a fix.
- **A DB `close()` that only closes the calling thread's connection leaks worker-thread connections.** With thread-local connections, a connection opened on a worker is never closed; track them and close all of them, or a later filesystem cleanup fails.
- **Newly added production code is a prime flake suspect when a stable suite starts failing.** A guardrail that mutates process-global state is itself a bug: `socket.setdefaulttimeout()` is process-wide, so set-and-forget leaks your timeout into every later socket operation. Save the previous value and restore it in a `finally`, and probe that a pre-existing value is preserved.

### 7. Reconciling a gate result that arrives after you moved on

A long gate run (full suite, browser audit) finishes while you are already
working on something else, so its result lands afterwards. **A green run from
before a fix says nothing about the code after it** — and it can be green
*precisely because* the bug is still present, since a detector that finds nothing
leaves every count assertion passing.

- **Prove staleness from the artifact; do not assert it.** Grep the run's log for the test names the change added — zero occurrences is proof it predates them. Then list the logs newest-first with their pass/fail lines and check the counts form a coherent sequence (pre-fix N green -> regression N+delta failing -> post-fix N+delta green). Numbers that reconcile arithmetically are evidence; "it looks old" is not.
- **Name the run's own artifacts** (a job id, a row count) and compare them with the current ones, so you can say which run is which without ambiguity rather than relying on timestamps alone.
- **Re-run the gate and report the fresh number as authoritative.** The late result is context, not evidence, and a late green must never be reported as the current state.
- **Qualify a gate you only passed under a narrowed flag.** If `tsc` is clean only with `--skipLibCheck` because a dependency ships broken type definitions, report it that way and count the `^src/` errors separately to separate your code from the dependency's. An unqualified "gate passed" is a claim you cannot support.
- **A task list restored across a context boundary is not evidence of progress.** An item may read "in progress" for work that is finished, and a file existing is not verification — re-run that item's own gate and mark it from the result; anything whose gate you cannot re-run stays open.

### 8. A test that depends on an external service

When a fixture points `base_url` at a real server the suite does not manage, the
test's result depends on an unrelated process — it flips green and red with no
code change. That is a defect in the test, not flakiness, and it must be proven
rather than assumed.

**Diagnose before touching the assertion:**

1. **Find the same scenario asserted elsewhere in the suite.** If a sibling file
   covers it through a different path and passes, diff the two variants — the
   difference (a synchronous pipeline call vs. an API-driven job behind a poll
   loop) is the suspect, and the passing sibling is your control.
2. **Measure time-to-first-event instead of guessing.** Instrument the step with
   a timestamped print (`_phase`, `_emit`, the worker entry) and read where the
   time actually goes. A gap that looks like network latency can be a retry-sleep
   loop in an authentication step that runs *before* the first pipeline phase, so
   the phase timings alone will not show it.
3. **Toggle the condition and re-run** — with the service up, then down. A test
   that passes only with the service up is environment-dependent, demonstrated
   rather than asserted.

**Then fix the product before widening the window.**

- If the delay comes from a component that fails slowly, fix the component (see
  `fastapi-api-hardening`: retry only transient failures). Widening a timeout
  hides a product that hangs.
- Size a wait window from the **measured worst case**, and record that
  measurement in a comment beside the constant so the next reader can re-derive
  it. A window sized to the happy path leaves only a small margin and breaks
  under CPU load.
- **Put the observed state in the assertion message.** `assert waited, "job
  should wait for review"` costs a re-run; including the status and per-phase
  statuses tells you what actually happened. Never assert on a bare boolean when
  the object you polled is already in scope.
- Verify **both** directions before claiming the fix: pass with the service up
  and with it down.

### 9. Severity and confidence are different quantities

When a test asserts that a low-confidence finding maps to a lower severity, that
test encodes the wrong model. **Severity/CVSS is the impact IF the bug is real**
— what a triage platform asks for and a human verifies — and it comes from the
vulnerability class and the affected endpoint. **Confidence is how strongly the
evidence supports the claim**; report it separately and use it to gate
submission. Tempering severity by confidence is cosmetic: an unconfirmed finding
is rejected whatever label it carries, so the label buys nothing and only the
gate protects.

- **Any single rendered line showing a severity label beside a CVSS score must be
  self-consistent** (`severity_for_score(score) == label`). Two heuristics — one
  from confidence, one from a metric mapping — will eventually disagree, and
  "Severity: medium (CVSS 9.8)" tells a reader the tool does not understand its
  own output. Assert the consistency across a table of representative findings.
- **Coerce an unknown or malformed confidence to the LOW end, never the high
  end.** A NULL column, a non-numeric string, or a missing field must resolve to
  `0.0`; defaulting the other way turns a malformed row into an over-claim.
- **Fix the test to assert the real contract** (the impact rating is stable;
  confidence is carried alongside it) rather than re-tuning the threshold to make
  the old assertion pass.

## References

- `references/pytest-async-sqlalchemy.md` — Detailed pytest + async SQLAlchemy patterns
- `references/httpx-cookie-management.md` — httpx cookie handling for multi-user scenarios
- `references/flake-diagnosis.md` — Diagnosing a non-reproducible test failure: capturing the traceback, reading the abbreviated exception type, testing a mechanism instead of narrating it, reproducing order-dependent flakes, and reporting cause-unknown honestly
- `references/test-failure-triage.md` — Triaging failures a behaviour change caused: count assertions that silently encoded a bug's absence, fixtures that contradict their own name, and keeping the triage honest
