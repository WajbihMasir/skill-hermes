# Diagnosing a Non-Reproducible Test Failure

A test that fails once in N full-suite runs and never in isolation. The
discipline: capture evidence, name a mechanism, TEST the mechanism, and report
"unknown" when it does not reproduce.

## Step 1 — Capture the traceback before theorising

Run the full suite to a FILE. A piped or truncated tail loses the traceback.

```bash
pytest tests/ -q > /tmp/full.txt 2>&1; echo "EXIT=$?"
grep -B 40 "^FAILED" /tmp/full.txt | head -60
```

Beware a grep that matches the wrong lines: `grep -A 25 "<testname>"` also hits
DeprecationWarning blocks that merely *name* the test. Confirm you are reading a
real `FAILED` line, not a warning header.

If the traceback was never captured, the cause is UNKNOWN. Say so.

## Step 2 — Read the abbreviated exception type

`pytest -q` abbreviates the exception class to its first letter plus `...`:

| Summary shows | Actual type | Usually means |
|---|---|---|
| `- A...` | `AssertionError` | an assertion in the test body |
| `- O...` | `OSError` | cleanup / teardown, not the body |
| `- V...` | `ValueError` | data or parsing in the body |
| `- K...` | `KeyError` | a missing mapping key |
| `- T...` | `TimeoutError` | a blocking call |

This alone localises the failure. **If the type is not `AssertionError`, every
assertion in the test body PASSED** — the failure is in setup or teardown. That
single deduction reframes the whole investigation and is available before any
theorising.

## Step 3 — Test the mechanism, do not narrate it

Write a standalone script that applies the suspected defect and runs the failing
path verbatim. Run a CONTROL with the defect removed.

```
apply suspected defect -> PASSED  => not the cause
control (no defect)    -> PASSED  => confirms the harness itself works
```

> A real bug found while investigating a flake is still worth fixing, but fixing
> it does not prove it caused the flake.

Report it as a separate, real defect and leave the flake open. Never let a fix
that coincides with the flake disappearing stand in for causation.

Guard against a false confirmation: a repro script that exits non-zero because of
a `SyntaxError` in its own quoting has proved nothing. Read the stderr; do not
check only the exit code.

## Step 4 — To reproduce an order-dependent flake, preserve the context

An inter-test-pollution flake needs the preceding tests to run FIRST, in the
SAME process. Check what a filtered command actually collects:

```bash
pytest tests/ -k <name> -q --collect-only    # -> "2/852 tests collected"
pytest tests/ -q --collect-only              # -> "852 tests collected"
```

A soak loop over a `-k`-filtered subset in fresh processes CANNOT reproduce it:
it removes the state accumulation that is the suspected cause, and a fresh
process per iteration resets everything. **A clean result from that loop is
evidence of nothing** — a trap that looks like diligence.

The valid iteration is the preceding files plus the target, in one process:

```bash
PREFIX=$(ls tests/test_*.py | sed -n '1,11p' | tr '\n' ' ')
pytest $PREFIX -q --tb=long > /tmp/iter.txt 2>&1
```

Price it before committing to a loop. If one iteration costs minutes, a
50-iteration soak costs hours and may still find nothing. Cap the effort, and
report the state honestly rather than burning the budget on a ghost.

## Step 5 — Make cleanup failures attributable

A test body with no `try/finally` lets a teardown failure surface as a test
failure, hiding that the assertions passed:

```python
# Bad: an rmtree failure is indistinguishable from a real test failure
with tempfile.TemporaryDirectory() as tmpdir:
    db = HunterDatabase(tmpdir + "/test.db")
    ...
    assert isinstance(data, list)
    db.close()

# Good: body and cleanup are separately attributable
with tempfile.TemporaryDirectory() as tmpdir:
    db = HunterDatabase(tmpdir + "/test.db")
    try:
        ...
        assert isinstance(data, list)
    finally:
        db.close()
```

Windows is the usual source: a file handle still open (SQLite `-wal`/`-shm` side
files, an unclosed log handler, a connection opened on a worker thread while
`close()` only closes the calling thread's) blocks directory removal. If a
conftest already carries a `gc.collect()` after each test "so Windows releases
SQLite file handles", treat that as documentation of this class — a signal, not
a fix.

## Step 6 — A guardrail must not mutate process-global state

Newly added production code is a prime suspect when a previously-stable suite
starts flaking. `socket.setdefaulttimeout()` is process-wide: set it to bound a
DNS lookup and leave it set, and every later socket operation in the process
inherits your timeout — surfacing as unrelated, non-reproducible failures far
from the cause.

```python
previous = socket.getdefaulttimeout()
try:
    socket.setdefaulttimeout(timeout)
    infos = socket.getaddrinfo(name, None, proto=socket.IPPROTO_TCP)
finally:
    socket.setdefaulttimeout(previous)   # restore, or you leak a global
```

Probe it: assert the timeout is unchanged after the call, and that a
pre-existing value is preserved. Do not assume this is the cause of a flake you
are chasing — test it (Step 3).

## Step 7 — Contention vs leaked state: measure, do not guess

A test that passes alone and fails in the full suite has three possible causes.
They need different fixes, so identify which one before touching anything:

1. **Resource contention** — another process holds a shared resource (a browser, a
   port, a lock).
2. **Leaked process-global state** — an earlier test left a loop, a thread, a
   monkeypatch, or a global setting alive.
3. **A real product bug the suite happens to expose** — the valuable one.

**"It must be contention" is a guess, and often wrong.** A live-browser file that
failed in the suite also failed in a deliberately CLEAN environment with zero
leftover browser processes — contention was ruled out by measurement, not argument.

Rule contention in or out by counting, then move on:

```bash
# before and after a full run — a stable count means no leak, a rising one is a bug
tasklist | grep -ciE "chrome|node"
```

If the count is stable and the file still fails alone, stop looking at resources
and instrument for leaked state.

### Find the culprit with a plugin, not with bisection by hand

A `conftest`/plugin hook that inspects the suspect state after EVERY test reports
the first test after which it appears. That is one run, and it names the culprit
outright:

```python
# loop_watch_plugin.py — run with: pytest tests/ -q -p loop_watch_plugin -s
import asyncio, threading

_seen = False

def pytest_runtest_teardown(item, nextitem):
    global _seen
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return                      # no loop here — state is clean
    if not _seen:
        _seen = True
        print("\n*** STATE APPEARED AFTER: %s" % item.nodeid, flush=True)
        print("*** thread: %s" % threading.current_thread().name, flush=True)
        print("*** loop: %r running=%s" % (loop, loop.is_running()), flush=True)
        for t in list(asyncio.all_tasks(loop))[:6]:
            coro = t.get_coro()
            frame = getattr(coro, "cr_frame", None)
            where = ("%s:%s in %s" % (frame.f_code.co_filename, frame.f_lineno,
                                      frame.f_code.co_name)) if frame else "?"
            print("***   task %s @ %s" % (t.get_name(), where), flush=True)
```

Adapt the probe to the state you suspect: an open loop, a live thread, a patched
attribute, a changed global. The pattern is the same — check after each test,
print once, name the owner.

The task list is the second half of the answer: a live task sitting inside a
third-party library (`.../_impl/_connection.py ... run_as_sync`) names the owner
directly, so you stop suspecting your own fixtures.

### Read the library's source before theorising about its limits

When the leaked state belongs to a dependency, read the check that raises. The
condition is usually explicit and settles the mechanism in one glance:

```python
try:
    self._loop = asyncio.get_running_loop()
if self._loop.is_running():
    raise Error("... Sync API inside the asyncio loop.")
```

That is the whole rule — and it explains why the failure is order-dependent and
why a retry cannot help. A theory about library behaviour that you have not read
the source for is a guess.

### Make the skip honest, not silent

If a test genuinely cannot run in the polluted environment (a sync browser API
that cannot start while a loop is live), guard it on the real precondition at
**test time** — not at import time, since pytest imports every module before
running the first test, so a module-level check always sees a clean process:

```python
@pytest.fixture
def agent():
    if not _can_launch_here():
        pytest.skip("a real browser cannot launch in this process: "
                    "a live asyncio loop is already running")
    ...
```

A skip that states the reason is honest; a lowered assertion or a deleted test is
not. Prefer a skip you can explain over a green you cannot.

## Reporting

Three honest outcomes, in order of preference:

1. **Cause found and reproduced** — state the mechanism, the reproduction, and the fix.
2. **Real defect found, causation unproven** — report the defect as fixed and the flake as still open.
3. **Nothing found** — report the flake as open with cause unknown, and say what evidence would settle it.

Never present (2) or (3) as (1). A plausible story is not evidence, and two clean
runs after a fix do not prove the flake is gone.
