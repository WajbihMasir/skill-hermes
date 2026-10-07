---
name: mock-to-live-integration
description: "Use when replacing mock data with a real backend."
version: 1.0.0
author: hermes-curator
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [frontend, backend, api, integration, zero-mock, dashboard, adapters, verification]
    related_skills: [fastapi-api-hardening, dogfood, frontend-component-testing, backend-api-testing]
---

# Mock-to-Live Integration

## When to use

A dashboard or app renders mock/fixture data, hides backend failures behind
`catch { return mock }`, or fakes actions with `setTimeout`, and the ask is to
make it real: "zero mock", "connect it to the backend", "100% production".
Also applies when a page shows plausible data while the backend is down —
same defect, spotted from the outside.

Not for: building the backend endpoints (`fastapi-api-hardening`), exploratory
QA of a finished app (`dogfood`), unit-test plumbing
(`frontend-component-testing`), or layout/overflow breakage that the new DOM
introduced (`defensive-responsive-layout`).

**Removing a fallback changes the DOM, which can expose layout bugs.** Pages that
switched from a populated mock table to an honest empty state (or the reverse)
render different content at the same viewport, so a page that fit before can
overflow after. Re-run the multi-viewport sweep
(`defensive-responsive-layout`) as part of the integration gate, not only the
per-page data audit.

## The policy (state it in the deliverable, enforce it in the code)

1. **A `catch` that returns mock data is a lie** — it turns an outage into a
   convincing screen. Delete the fallback and let the error reach the UI.
2. **MOCK is an explicit opt-in.** The flag is false unless the env var is
   literally `"true"`; a default-on mock flag means production serves fixtures.
   (Exception: a build produced for a cloud preview platform — see
   `agent-handoff-specs` → cloud preview handoff — ships mock-default BY
   DESIGN because its preview cannot reach a local backend. Integrating it
   means flipping the mode flag for the local run and pinning real mode in any
   deployed build.)
3. **Empty is honest; fabricated is not.** No data → return `null`/`[]` so the
   page renders its empty state. Never seed a canned dataset to look populated.
4. **A simulated action is a bug.** A `setTimeout` that fakes a scan/send/run
   must be wired to a real endpoint or the control removed.

## Procedure

1. **Inventory before you delete.** Grep the API client for fallbacks and the
   pages for direct mock-module imports — a page-level `import("@/lib/mock")`
   bypasses a centralized toggle, so the global flag can be off while that page
   still shows fixtures.
   `search_files(pattern="return mock|lib/mock|MOCK_", target="content")`
2. **Build the real endpoint before removing its fallback.** Removing first
   ships a broken screen. Order: endpoint → adapter → remove fallback.
3. **Adapt at the client boundary, not in the pages.** Engine responses are not
   view models (field names, nesting, enum casing all differ). Do the mapping in
   one wrapper per endpoint and leave the page's type contract untouched, so no
   component changes when the engine response evolves.
4. **Split the two failure modes.** "No data yet" returns `null`/`[]` → the page
   shows its empty state. "Backend failed" throws → the page shows an error with
   a retry. Collapsing both into an empty state hides outages.
5. **Give every fetch a loading state.** A page that shows its empty state while
   the request is in flight looks broken on a slow backend.
6. **Wire the write actions for real.** Mutations (send, run, scan, probe) call
   their endpoint and render the *returned* result — never a locally invented
   one. A verdict string computed client-side is a fabricated finding.
7. **Keep tests hermetic without faking the build.** Pin MOCK in the test env
   file only, and check the loader order — see `frontend-component-testing`
   (`.env.test` loses to `.env` when the tool's config calls `dotenv.config()`
   first, because dotenv never overrides an existing value).
8. **Seed real data, then audit.** For data a user flow could create, POST
   through the live API — it proves the whole path and doubles as a smoke test.
   For demo richness endpoints cannot produce (backdated history, terminal
   review states, append-only audit rows), insert directly via an idempotent
   tag-and-recreate script, then verify through the read APIs the UI uses.
   Recipe: `references/demo-seed-data.md`. Then run the per-page audit.

## Verification gate — all four must pass

If the frontend was produced from a handoff spec (`agent-handoff-specs`), replay that spec's numbered acceptance criteria first — it is the contract the producer was measured against, using the same seeded accounts.

1. **Type + build clean:** `tsc --noEmit` → 0 errors, then the production build.
2. **Unit suite green in MOCK mode** (hermetic, no network).
3. **Per-page live audit:** drive every page against the running backend and
   require, per page: root testid present OR honest empty state, a matching
   `/api/*` request in the network log, and zero console errors. Copy
   `templates/live_page_audit.py` and fill in its page table.
4. **Anon → 401 on every new route** when auth is on.

An empty state passes ONLY together with a request. Empty-without-a-request is
broken wiring; populated-without-a-request is a hidden fallback.

## Pitfalls

- **The mock's role/permission matrix drifts from the real backend and the drift only shows in REAL mode.** A mock `rules.ts` gave PIC `evidence.submit` while the backend DDL did not — in mock mode the upload button worked, in real mode the same user got 403. Treat the backend DDL/migration (or the handoff spec's matrix) as the single source of truth; make the mock matrix a copy of it, note that in a comment, and bump the mock store `schema` so stale localStorage auto-resets. Then audit every action button: gate it on `can('<permission>')` from `/auth/me`, not just on ownership/status — a button that only checks `row.owner_id === me.id` will render for roles the backend will reject.
- **"The page rendered" is not proof of integration.** Intercept the network and
  assert the request happened; a mock fallback renders perfectly.
- **Assert the page root marker before asserting content.** A nav click that does
  not register (animating sidebar, unstable element) leaves the previous page
  mounted, so the next assertion silently validates the wrong screen. Use
  `click(force=True)` on animated nav and check the root testid first.
- **Adapters must tolerate a partial payload.** An engine response missing an
  optional key must not throw during render; default it and let the UI show what
  it has.
- **Keep the mock module for MOCK mode** unless asked to delete it — the goal is
  no fallback on the live path, not deleting fixtures the tests rely on.
- **A verdict computed in the UI is a fabricated finding.** If the backend
  returns raw results (status codes, bodies), derive the verdict server-side, or
  label it a client-side heuristic — never present it as engine output.
- **Deriving the verdict server-side is not enough — calibrate it to the evidence.**
  A verdict must not claim more than the raw results support. "N requests returned
  2xx" proves the operation was *accepted* more than once; it does NOT prove a
  double-spend, because a non-idempotent endpoint may simply accept every call.
  Distinguish by comparing the response bodies: differing bodies = shared state
  mutated (strong evidence); byte-identical bodies = accepted repeatedly (a signal
  that needs confirmation, worded as such). A confident label the evidence cannot
  support is the same defect as a client-side verdict, just moved one layer down.
- **Say what is honestly unavailable.** "None detected" is a valid result; a
  confident-looking guess is not. State the limits in the deliverable
  (third-party service flaky, sandbox not hardened, feature needs ≥2 inputs).

## Files

- `templates/live_page_audit.py` — per-page live audit driver; copy and fill in
  the page table.
- `references/demo-seed-data.md` — populating a live DB for a demo: API vs.
  direct-insert decision table, idempotent tag-and-recreate, scenario coverage,
  the "today" timezone trap, post-seed API verification.
