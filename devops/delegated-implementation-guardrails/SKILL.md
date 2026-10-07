---
name: delegated-implementation-guardrails
description: Use when delegating code implementation to sub-agents.
---

# Delegated Implementation Guardrails

## The failure mode

A sub-agent asked to "create tests + make them pass" will sometimes invent method/constructor signatures in its new test, then **rewrite existing backend modules to match its invented test** instead of fixing the test. This silently breaks every pre-existing caller and the canonical interface contract.

Real incident: a Phase 6 sub-agent wrote `test_integration.py` calling `ExperimentPlanner(db, logger)`, then patched the class from the canonical `__init__(base_url, db, logger)` to `__init__(db, logger, base_url=...)`. 24 pre-existing tests broke. The error surfaced as a misleading `PermissionError` (WinError 32) from `TemporaryDirectory` cleanup because the `AttributeError` fired in `_setup()` *before* `db.close()` ran, leaving an open SQLite handle.

## Rules when delegating

1. **Pin the interfaces.** In the sub-agent's context, list every existing class's exact `__init__` signature and public methods it may call. Say explicitly: "do NOT modify existing files' signatures; if a test fails, fix the test."
2. **Separate test-writing from implementation.** Do not ask one agent to both author new tests and adjust production code to satisfy them. Give the test author the real signatures, or give the implementer the real tests.
3. **Scope the write set.** Tell the agent exactly which files it may create/modify. Any other file it wants to touch = stop and report.
4. **Verify independently.** After the batch, run the FULL test suite yourself — never trust the child's `tests_passed` self-report. It only ran its own new tests.

## Diagnosing the aftermath

- **Signature mismatch symptom**: `AttributeError: 'X' object has no attribute 'Y'` where `Y` belongs to a *different* expected type (e.g. `'HunterLogger' object has no attribute 'rstrip'`). The arg order was swapped.
- **Misleading cleanup errors**: on Windows, a `PermissionError [WinError 32]` at `TemporaryDirectory`/`shutil.rmtree` is usually a *secondary* symptom. Find the exception that fired *before* `close()` was reached — read the full traceback, not just the last frame.
- **Compare against the canonical spec** (`docs/phaseN-spec.md`) — the spec's "Interface Contract" block is the source of truth, not the current code.
- **Reconstruct intent from the child's transcript**: `~/AppData/Local/hermes/cache/delegation/live/<deleg_id>/task-N.log` records its reads, patches, and its own reasoning — it often states exactly what it changed and why.

## Making tests hermetic

If tests hit a live target (e.g. `http://localhost:8000`) that is absent, they will be slow (connect-refused ~2s each) and non-deterministic (status 0 -> INCONCLUSIVE). Add an autouse `conftest.py` fixture that `monkeypatch.setattr`s the network boundary (e.g. `RequestMutator.send_with_identity`) with a deterministic fake returning the statuses the assertions expect (baseline 200, cross-identity 403). Keep a `gc.collect()` in the fixture teardown for Windows SQLite handle release.
