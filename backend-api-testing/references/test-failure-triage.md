# Triaging Test Failures a Behaviour Change Caused

Fixing a bug that made a component produce NOTHING — a detector that never
probed, a parser that always returned empty, a feature flag stuck off — WILL
break existing tests. Expect it, and triage each failure rather than editing
numbers until the suite goes green.

## The signature

Count and emptiness assertions fail:

```
assert findings == 8      ->  assert 14 == 8
assert len(rows) == 0     ->  6 != 0
```

The old number silently encoded the bug's absence: *"this component finds
nothing"*. That is why the suite was green while the bug was live.

## Decision rule — which side is wrong?

Ask what the assertion was actually protecting.

**1. It asserted a COUNT.** The number was a magic value, not the contract.
Rewrite it to assert the RELATIONSHIP:

- non-empty, or `>=` the previous baseline
- the list endpoint's length equals the job's own reported count
- the report's total equals the stored rows

Do **not** simply move the number to the new value. That re-encodes today's
output as tomorrow's truth and the test stops protecting anything.

**2. It asserted "a clean input yields no findings/errors" and now fails.**
Check the FIXTURE before the code. A test double whose name says
`safe`/`clean`/`valid` but whose behaviour is permissive is modelling exactly the
condition the test claims is absent.

> Shape: a fake named for a target "where authorization is enforced" that
> returns 200 to a non-privileged identity on a privileged route. Every
> authorization probe correctly reports it. The fixture, not the probe, was
> wrong — fix the double so it matches its own name.

**3. It asserted an exact phase/step list.** Adding a phase legitimately changes
the length. Assert the invariant (every phase completed, none failed) rather
than the count.

## Keep the triage honest

- Name which side was wrong and why. Never weaken an assertion to reach green without stating it.
- Do not delete a failing test that turns out to be correct — it just caught a real change.
- If the wrong party is a fixture shared across tests, fix it once at the fixture and re-run the whole file. The blast radius is the point.
- A test double that models a *vulnerable* target makes every negative-result test using it meaningless. Audit fixtures for this whenever a detector starts working.

## Related

`references/flake-diagnosis.md` — when the failure is non-reproducible instead
of caused by your change.
